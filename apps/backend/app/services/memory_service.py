from __future__ import annotations

import uuid

from app.core.audit import append_audit_event, utc_now
from app.core.storage import store


class MemoryService:
    def __init__(self) -> None:
        self._store = store("memory_records")

    def record(self, tenant_id: str, actor: str, memory_type: str, payload: dict) -> dict:
        row = {"id": str(uuid.uuid4()), "timestamp": utc_now(), "tenant_id": tenant_id, "memory_type": memory_type, "payload": payload}
        self._store.update([], lambda rows: rows.append(row))
        append_audit_event("memory.recorded", actor, {"id": row["id"], "memory_type": memory_type}, tenant_id=tenant_id)
        return row

    def list(self, tenant_id: str, limit: int = 100) -> list[dict]:
        return [row for row in self._store.read([]) if row["tenant_id"] == tenant_id][-limit:]


memory_service = MemoryService()