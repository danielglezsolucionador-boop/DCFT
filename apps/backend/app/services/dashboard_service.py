from __future__ import annotations

from app.core.runtime_status import runtime_snapshot
from app.db.repositories import current_subscription, dashboard_counts
from app.services.knowledge_service import knowledge_service
from app.services.regulatory_service import regulatory_service
from app.services.subscription_service import subscription_service


class DashboardService:
    async def summary(self, tenant_id: str, plan: str, database: dict) -> dict:
        counts = await dashboard_counts(tenant_id)
        subscription = await current_subscription(tenant_id)
        effective_plan_id = (subscription or {}).get("plan_effective") or plan
        current_plan = subscription_service.current(effective_plan_id)
        limits = current_plan.get("limits") or {}
        over_limit = {
            key: {"current": counts.get(key, 0), "limit": value}
            for key, value in limits.items()
            if isinstance(value, int) and counts.get(key, 0) > value
        }
        return {
            "product": "DCFT - Doctor Contable Financiero Tributario",
            "tagline": "Tu copiloto empresarial premium.",
            "tenant_id": tenant_id,
            "plan": current_plan,
            "trial": {
                "status": (subscription or {}).get("trial_status", "none"),
                "active": (subscription or {}).get("trial_active", False),
                "expired": (subscription or {}).get("trial_expired", False),
                "days_remaining": (subscription or {}).get("trial_days_remaining", 0),
                "plan_base": (subscription or {}).get("plan", plan),
                "plan_effective": effective_plan_id,
                "started_at": (subscription or {}).get("trial_started_at"),
                "ends_at": (subscription or {}).get("trial_ends_at"),
            },
            "runtime": runtime_snapshot(database),
            "counts": {
                **counts,
                "knowledge_items": len(knowledge_service.list_items()),
                "regulatory_items": len(regulatory_service.list_items()),
            },
            "usage": {"current": counts, "limits": limits, "over_limit": over_limit},
            "activation": {
                "has_alerts": counts.get("alerts", 0) > 0,
                "has_documents": counts.get("documents", 0) > 0,
                "has_workflows": counts.get("workflows", 0) > 0,
            },
            "boundaries": [
                "No autonomous tax filing.",
                "No SUNAT, bank, or official document modification.",
                "No fake AI or OCR responses.",
                "Human approval required for critical actions.",
            ],
        }


dashboard_service = DashboardService()
