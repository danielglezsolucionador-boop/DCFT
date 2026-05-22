from __future__ import annotations

from app.db import repositories


class AnalyticsService:
    async def record(self, tenant_id: str, actor: str, event_type: str, metadata: dict) -> dict:
        await repositories.record_runtime_event(
            f"product.{event_type}",
            "ok",
            {"actor": actor, "metadata": metadata},
            tenant_id=tenant_id,
        )
        return {"status": "recorded", "event_type": event_type}

    async def summary(self, tenant_id: str) -> dict:
        return await repositories.product_analytics_summary(tenant_id)


analytics_service = AnalyticsService()
