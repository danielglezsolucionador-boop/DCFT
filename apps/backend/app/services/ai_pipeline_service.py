from __future__ import annotations

from app.core.audit import append_audit_event_async
from app.core.config import settings
from app.db import repositories


class AIPipelineService:
    async def create(self, payload: dict, actor: str, tenant_id: str) -> dict:
        status = "queued" if settings.ai_provider_enabled else "blocked_provider_disabled"
        provider_id = "ai.configured" if settings.ai_provider_enabled else "ai.disabled"
        record_payload = {
            "requested_by": actor,
            "explanation": "External AI provider is disabled; DCFT will not invent a response." if status.startswith("blocked") else "Provider configured for future controlled execution.",
            **payload,
        }
        record = await repositories.create_ai_request(record_payload, tenant_id, provider_id, status)
        await append_audit_event_async("ai.request_recorded", actor, {"id": record["id"], "status": status}, risk="medium", tenant_id=tenant_id)
        return record

    async def list(self, tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        return await repositories.list_ai_requests(tenant_id, limit, offset)


ai_pipeline_service = AIPipelineService()
