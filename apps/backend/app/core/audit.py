from __future__ import annotations

from datetime import datetime, timezone
from contextvars import ContextVar
import hashlib
import json
import uuid

from app.core.config import settings
from app.core.observability import metrics_registry


request_id_context: ContextVar[str | None] = ContextVar("request_id_context", default=None)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def set_audit_request_id(request_id: str | None) -> None:
    request_id_context.set(request_id)


def append_audit_event(event_type: str, actor: str, payload: dict, risk: str = "low", tenant_id: str = "public") -> dict:
    settings.audit_dir.mkdir(parents=True, exist_ok=True)
    request_id = request_id_context.get()
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": utc_now(),
        "request_id": request_id,
        "tenant_id": tenant_id,
        "event_type": event_type,
        "actor": actor,
        "risk": risk,
        "payload": _redact(payload),
    }
    with (settings.audit_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


async def append_audit_event_async(event_type: str, actor: str, payload: dict, risk: str = "low", tenant_id: str = "public") -> dict:
    event = append_audit_event(event_type, actor, payload, risk, tenant_id)
    try:
        from app.db.repositories import add_audit_event

        db_event = await add_audit_event(
            event_type,
            actor,
            event["payload"],
            risk,
            tenant_id,
            event_id=event["id"],
            created_at=event["timestamp"],
            request_id=event["request_id"],
        )
        event["previous_hash"] = db_event.get("previous_hash")
        event["event_hash"] = db_event.get("event_hash")
        metrics_registry.record_audit_event()
    except Exception as exc:
        append_audit_event(
            "audit.db_write_failed",
            "system",
            {"event_type": event_type, "reason": exc.__class__.__name__},
            risk="high",
            tenant_id=tenant_id,
        )
    return event


def canonical_audit_material(
    *,
    event_id: str,
    timestamp: str,
    request_id: str | None,
    tenant_id: str,
    event_type: str,
    actor: str,
    risk: str,
    payload: dict,
    previous_hash: str | None,
) -> str:
    return json.dumps(
        {
            "actor": actor,
            "event_id": event_id,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous_hash,
            "request_id": request_id,
            "risk": risk,
            "tenant_id": tenant_id,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def audit_hash(**kwargs) -> str:
    return hashlib.sha256(canonical_audit_material(**kwargs).encode("utf-8")).hexdigest()


def read_audit_events(limit: int = 100) -> list[dict]:
    path = settings.audit_dir / "events.jsonl"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-limit:] if line.strip()]


def _redact(payload: dict) -> dict:
    blocked = {"password", "token", "secret", "api_key", "authorization"}
    clean: dict = {}
    for key, value in payload.items():
        clean[key] = "***redacted***" if any(part in key.lower() for part in blocked) else value
    return clean
