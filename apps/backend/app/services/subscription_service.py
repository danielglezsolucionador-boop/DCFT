from __future__ import annotations

from fastapi import HTTPException, status

from app.db import repositories
from app.services.payment_service import PLAN_PRICES

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
        "trial_days": 0,
        "requires_ruc": False,
        "prices": PLAN_PRICES["student"],
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
        "prices": PLAN_PRICES["mype"],
        "features": ["basic_monitoring", "alerts", "document_analysis", "basic_cross_checks", "safe_sunat_sol_credentials"],
        "limits": {"alerts": 100, "recommendations": 50, "documents": 100, "workflows": 50, "ai_requests": 10, "users": 5},
    },
    {
        "id": "premium",
        "name": "Premium",
        "login_required": True,
        "commercial_tier": "premium",
        "trial_days": 7,
        "requires_ruc": True,
        "prices": PLAN_PRICES["premium"],
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

COMMERCIAL_PLANS = {"mype", "premium", "business_basic", "business_premium", "professional"}
BLOCKING_SUBSCRIPTION_STATUSES = {"expired", "pending", "pending_payment", "past_due", "unpaid", "cancelled", "canceled"}


class SubscriptionService:
    def plans(self) -> list[dict]:
        return PLANS

    def current(self, plan: str = "free_student") -> dict:
        plan_id = self.normalize_plan(plan)
        return next((item for item in PLANS if item["id"] == plan_id), PLANS[0])

    async def current_for_tenant(self, tenant_id: str, fallback_plan: str = "free_student") -> dict:
        subscription = await repositories.current_subscription(tenant_id)
        plan_id = self.normalize_plan((subscription or {}).get("plan") or fallback_plan)
        base = dict(self.current(plan_id))
        if subscription is None:
            return {
                **base,
                "status": "pending",
                "plan": plan_id,
                "plan_effective": plan_id,
                "trial": {"active": False, "status": "none", "started_at": None, "ends_at": None},
                "subscription": None,
                "provider": None,
                "billing_cycle": None,
                "interval": None,
                "started_at": None,
                "ends_at": None,
            }
        return {
            **base,
            "status": subscription.get("status"),
            "plan": subscription.get("plan"),
            "plan_effective": subscription.get("plan_effective"),
            "trial": {
                "active": subscription.get("trial_active"),
                "status": subscription.get("trial_status"),
                "expired": subscription.get("trial_expired"),
                "days_remaining": subscription.get("trial_days_remaining"),
                "started_at": subscription.get("trial_started_at"),
                "ends_at": subscription.get("trial_ends_at"),
            },
            "subscription": subscription,
            "provider": subscription.get("provider"),
            "billing_cycle": subscription.get("billing_cycle"),
            "interval": subscription.get("interval"),
            "started_at": subscription.get("started_at"),
            "ends_at": subscription.get("ends_at"),
        }

    async def latest_checkout_for_tenant(self, tenant_id: str) -> dict | None:
        return await repositories.latest_checkout_session_for_tenant(tenant_id)

    def normalize_plan(self, plan: str) -> str:
        return PLAN_ALIASES.get(plan, plan)

    def limits_for(self, plan: str) -> dict:
        return dict(self.current(plan).get("limits") or {})

    async def ensure_active_commercial_subscription(self, tenant_id: str, fallback_plan: str = "free_student") -> None:
        subscription = await repositories.current_subscription(tenant_id)
        status_value = str((subscription or {}).get("status") or "").lower()
        stored_plan = self.normalize_plan(str((subscription or {}).get("plan") or fallback_plan))
        effective_plan = self.normalize_plan(str((subscription or {}).get("plan_effective") or stored_plan))
        is_commercial_context = stored_plan in {"mype", "premium"} or fallback_plan in COMMERCIAL_PLANS
        if status_value in BLOCKING_SUBSCRIPTION_STATUSES or (is_commercial_context and effective_plan not in {"mype", "premium"}):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "subscription_not_active",
                    "status": status_value or "pending",
                    "plan": stored_plan,
                    "plan_effective": effective_plan,
                    "message": "Pago o renovación pendiente. Los datos históricos se conservan, pero el acceso empresarial queda bloqueado hasta activar la suscripción.",
                },
            )

    async def enforce_limit(self, tenant_id: str, plan: str, resource: str) -> None:
        subscription = await repositories.current_subscription(tenant_id)
        status_value = str((subscription or {}).get("status") or "").lower()
        if status_value in BLOCKING_SUBSCRIPTION_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "subscription_not_active",
                    "status": status_value,
                    "resource": resource,
                    "message": "Pago o renovación pendiente. Los datos históricos se conservan, pero las acciones premium/empresa quedan bloqueadas.",
                },
            )
        effective_plan = (subscription or {}).get("plan_effective") or plan
        limits = self.limits_for(effective_plan)
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
                    "plan": self.normalize_plan(effective_plan),
                    "base_plan": self.normalize_plan(plan),
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
