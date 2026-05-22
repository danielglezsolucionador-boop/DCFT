from __future__ import annotations

from app.core.audit import append_audit_event_async
from app.db import repositories
from app.services.governance_service import governance_service


class WorkflowService:
    async def create(self, payload: dict, actor: str, tenant_id: str) -> dict:
        record = await repositories.create_workflow(payload, tenant_id)
        await append_audit_event_async(
            "workflow.created",
            actor,
            {"id": record["id"], "steps": len(record["steps"])},
            risk=record["risk"],
            tenant_id=tenant_id,
        )
        return record

    async def advance(self, workflow_id: str, payload: dict, actor: str, tenant_id: str) -> dict | None:
        approval_id = payload.get("approval_request_id") or ""
        approval_ok = await governance_service.is_approved(approval_id, tenant_id) if approval_id else False
        result = await repositories.advance_workflow(workflow_id, payload, tenant_id, approval_ok)
        if result is not None:
            await append_audit_event_async(
                "workflow.advanced",
                actor,
                {"id": workflow_id, "status": result["status"], "current_step": result["current_step"]},
                risk=result["risk"],
                tenant_id=tenant_id,
            )
        return result

    async def list(self, tenant_id: str, limit: int = 100) -> list[dict]:
        return await repositories.list_workflows(tenant_id, limit)


workflow_service = WorkflowService()
