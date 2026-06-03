from __future__ import annotations

from fastapi import HTTPException, status

from app.db import repositories

PLANS = [
    {
        "id": "free",
        "name": "Free",
        "login_required": False,
        "commercial_tier": "free",
        "trial_days": 0,
        "features": ["education", "basic_dashboard", "limited_manual_records"],
        "limits": {"alerts": 5, "recommendations": 2, "documents": 3, "workflows": 2, "ai_requests": 0, "users": 1},
    },
    {
        "id": "student",
        "name": "Estudiante",
        "login_required": True,
        "commercial_tier": "student",
        "trial_days": 7,
        "requires_ruc": False,
        "features": ["education", "practice_workflows", "basic_recommendations", "premium_modules_visible_locked"],
        "limits": {"alerts": 10, "recommendations": 5, "documents": 10, "workflows": 5, "ai_requests": 0, "users": 1},
    },
    {
        "id": "mype",
        "name": "MYPE",
        "login_required": True,
        "commercial_tier": "mype",
        "trial_days": 7,
        "requires_ruc": True,
        "features": ["basic_monitoring", "alerts", "document_analysis", "basic_cross_checks", "safe_sunat_auxiliary_foundation"],
        "limits": {"alerts": 100, "recommendations": 50, "documents": 100, "workflows": 50, "ai_requests": 10, "users": 5},
    },
    {
        "id": "premium",
        "name": "Premium",
        "login_required": True,
        "commercial_tier": "premium",
        "trial_days": 7,
        "requires_ruc": True,
        "features": ["advanced_recommendations", "deep_simulations", "executive_reports", "advanced_audit", "sunat_document_support"],
        "limits": {"alerts": 1000, "recommendations": 500, "documents": 1000, "workflows": 500, "ai_requests": 100, "users": 25},
    },
]

PLAN_ALIASES = {
    "free_student": "student",
    "business_basic": "mype",
    "professional": "mype",
    "business_premium": "premium",
}


class SubscriptionService:
    def plans(self) -> list[dict]:
        return PLANS

    def current(self, plan: str = "free_student") -> dict:
        plan_id = self.normalize_plan(plan)
        return next((item for item in PLANS if item["id"] == plan_id), PLANS[0])

    def normalize_plan(self, plan: str) -> str:
        return PLAN_ALIASES.get(plan, plan)

    def limits_for(self, plan: str) -> dict:
        return dict(self.current(plan).get("limits") or {})

    async def enforce_limit(self, tenant_id: str, plan: str, resource: str) -> None:
        limits = self.limits_for(plan)
        limit = limits.get(resource)
        if limit is None:
            return
        usage = await repositories.tenant_usage_counts(tenant_id)
        current = usage.get(resource, 0)
        if current >= int(limit):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "plan_limit_reached",
                    "resource": resource,
                    "limit": limit,
                    "current": current,
                    "plan": self.normalize_plan(plan),
                },
            )

    async def change_plan(self, tenant_id: str, actor: str, plan: str) -> dict:
        plan_id = self.normalize_plan(plan)
        if not any(item["id"] == plan_id for item in PLANS):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_plan")
        limits = self.limits_for(plan_id)
        updated = await repositories.update_tenant_subscription(tenant_id, plan_id, limits)
        usage = await repositories.tenant_usage_counts(tenant_id)
        over_limit = {
            key: {"current": usage.get(key, 0), "limit": value}
            for key, value in limits.items()
            if usage.get(key, 0) > int(value)
        }
        await repositories.record_runtime_event(
            "product.subscription_changed",
            "warning" if over_limit else "ok",
            {"actor": actor, "plan": plan_id, "over_limit": over_limit},
            tenant_id=tenant_id,
        )
        return {**(updated or {"tenant_id": tenant_id, "plan": plan_id, "limits": limits}), "usage": usage, "over_limit": over_limit}


subscription_service = SubscriptionService()
