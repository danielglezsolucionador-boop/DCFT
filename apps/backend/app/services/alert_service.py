from __future__ import annotations

from app.core.audit import append_audit_event_async
from app.db import repositories


class AlertService:
    async def create(self, payload: dict, actor: str, tenant_id: str) -> dict:
        record = await repositories.create_alert(payload, actor, tenant_id)
        await append_audit_event_async("alert.created", actor, {"id": record["id"], "severity": record["severity"]}, risk=record["severity"], tenant_id=tenant_id)
        return record

    async def list(self, tenant_id: str, limit: int = 100) -> list[dict]:
        return await repositories.list_alerts(tenant_id, limit)


alert_service = AlertService()
