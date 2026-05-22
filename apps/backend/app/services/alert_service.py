from __future__ import annotations

import uuid

from app.core.audit import append_audit_event, utc_now
from app.core.storage import store


class AlertService:
    def __init__(self) -> None:
        self._store = store("alerts")

    def create(self, payload: dict, actor: str, tenant_id: str) -> dict:
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": utc_now(),
            "tenant_id": tenant_id,
            "status": "open",
            **payload,
        }
        self._store.update([], lambda rows: rows.append(record))
        append_audit_event("alert.created", actor, {"id": record["id"], "severity": record["severity"]}, risk=record["severity"], tenant_id=tenant_id)
        return record

    def list(self, tenant_id: str, limit: int = 100) -> list[dict]:
        return [row for row in self._store.read([]) if row["tenant_id"] == tenant_id][-limit:]


alert_service = AlertService()