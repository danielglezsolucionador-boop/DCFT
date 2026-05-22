from __future__ import annotations

from app.core.audit import append_audit_event_async
from app.db import repositories


class FeedbackService:
    async def submit(self, payload: dict, actor: str, tenant_id: str) -> dict:
        severity = payload.get("severity", "medium")
        status = "warning" if severity == "high" else "ok"
        event_payload = {
            "actor": actor,
            "category": payload["category"],
            "severity": severity,
            "message": payload["message"],
        }
        await repositories.record_runtime_event("product.feedback_submitted", status, event_payload, tenant_id=tenant_id)
        await append_audit_event_async(
            "feedback.submitted",
            actor,
            {"category": payload["category"], "severity": severity},
            risk=severity,
            tenant_id=tenant_id,
        )
        return {"status": "recorded", "category": payload["category"], "severity": severity}


feedback_service = FeedbackService()
