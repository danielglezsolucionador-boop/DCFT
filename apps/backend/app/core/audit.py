from __future__ import annotations

from datetime import datetime, timezone
import json
import uuid

from app.core.config import settings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_audit_event(event_type: str, actor: str, payload: dict, risk: str = "low", tenant_id: str = "public") -> dict:
    settings.audit_dir.mkdir(parents=True, exist_ok=True)
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": utc_now(),
        "tenant_id": tenant_id,
        "event_type": event_type,
        "actor": actor,
        "risk": risk,
        "payload": _redact(payload),
    }
    with (settings.audit_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


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