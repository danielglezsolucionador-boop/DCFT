from __future__ import annotations

import uuid

from app.core.audit import append_audit_event, utc_now
from app.core.config import settings
from app.core.storage import store


class AIPipelineService:
    def __init__(self) -> None:
        self._store = store("ai_requests")

    def create(self, payload: dict, actor: str, tenant_id: str) -> dict:
        status = "queued" if settings.ai_provider_enabled else "blocked_provider_disabled"
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": utc_now(),
            "tenant_id": tenant_id,
            "requested_by": actor,
            "provider_id": "ai.configured" if settings.ai_provider_enabled else "ai.disabled",
            "status": status,
            "explanation": "External AI provider is disabled; DCFT will not invent a response." if status.startswith("blocked") else "Provider configured for future controlled execution.",
            **payload,
        }
        self._store.update([], lambda rows: rows.append(record))
        append_audit_event("ai.request_recorded", actor, {"id": record["id"], "status": status}, risk="medium", tenant_id=tenant_id)
        return record

    def list(self, tenant_id: str, limit: int = 100) -> list[dict]:
        return [row for row in self._store.read([]) if row["tenant_id"] == tenant_id][-limit:]


ai_pipeline_service = AIPipelineService()