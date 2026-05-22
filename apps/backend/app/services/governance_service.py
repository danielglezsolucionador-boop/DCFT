from __future__ import annotations

from app.core.audit import append_audit_event_async
from app.core.observability import metrics_registry
from app.db import repositories


class GovernanceService:
    async def create_request(self, payload: dict, requested_by: str, tenant_id: str) -> dict:
        record = await repositories.create_approval_request(payload, requested_by, tenant_id)
        metrics_registry.record_governance_event()
        await append_audit_event_async(
            "governance.request_created",
            requested_by,
            {"id": record["id"], "risk": record["risk"]},
            risk=record["risk"],
            tenant_id=tenant_id,
        )
        return record

    async def decide(self, request_id: str, decision: str, reason: str, decided_by: str, tenant_id: str) -> dict | None:
        before = await self.get(request_id, tenant_id)
        result = await repositories.decide_approval_request(request_id, decision, reason, decided_by, tenant_id)
        if result is not None:
            metrics_registry.record_governance_event()
            event_type = "governance.request_replayed" if before and before["status"] in {"approved", "rejected"} else "governance.request_decided"
            await append_audit_event_async(
                event_type,
                decided_by,
                {"id": request_id, "decision": result["status"]},
                risk=result["risk"],
                tenant_id=tenant_id,
            )
        return result

    async def get(self, request_id: str, tenant_id: str) -> dict | None:
        for row in await repositories.list_approval_requests(tenant_id, limit=500):
            if row["id"] == request_id:
                return row
        return None

    async def is_approved(self, request_id: str, tenant_id: str) -> bool:
        return await repositories.is_approval_approved(request_id, tenant_id)

    async def list(self, tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        return await repositories.list_approval_requests(tenant_id, limit, offset)


governance_service = GovernanceService()
