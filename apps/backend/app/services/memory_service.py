from __future__ import annotations

from app.core.audit import append_audit_event_async
from app.db import repositories


class MemoryService:
    async def record(self, tenant_id: str, actor: str, memory_type: str, payload: dict) -> dict:
        row = await repositories.create_memory_record(tenant_id, memory_type, payload)
        await append_audit_event_async("memory.recorded", actor, {"id": row["id"], "memory_type": memory_type}, tenant_id=tenant_id)
        return row

    async def list(self, tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        return await repositories.list_memory_records(tenant_id, limit, offset)


memory_service = MemoryService()
