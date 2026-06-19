from __future__ import annotations

from fastapi import HTTPException, status

from app.core.audit import append_audit_event_async
from app.core.config import settings
from app.db import repositories
from app.schemas.common import CurrentUser
from app.services.subscription_service import subscription_service


class AdminService:
    def _ensure_ceo_admin(self, user: CurrentUser) -> None:
        allowed = user.role in {"ceo", "admin", "super_admin"} or (
            settings.admin_username.strip() and user.username == settings.admin_username.strip()
        )
        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "admin_ceo_required"})

    async def list_users(self, user: CurrentUser) -> dict:
        self._ensure_ceo_admin(user)
        users = await repositories.admin_list_users()
        await append_audit_event_async(
            "admin.users_listed",
            user.username,
            {"count": len(users), "panel": "ceo"},
            risk="medium",
            tenant_id=user.tenant_id,
        )
        return {"users": users, "protected": True, "admin": user.username}

    async def set_trial(self, user: CurrentUser, target_user_id: str, active: bool, days: int) -> dict:
        self._ensure_ceo_admin(user)
        tenant_id = await repositories.tenant_id_for_user(target_user_id)
        if tenant_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "user_not_found"})
        subscription = await repositories.set_tenant_trial(tenant_id, active=active, days=days)
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "subscription_not_found"})
        await repositories.record_runtime_event(
            "admin.trial_updated",
            "ok",
            {"target_user_id": target_user_id, "trial_active": active, "days": days, "plan_effective": subscription["plan_effective"]},
            tenant_id=tenant_id,
        )
        await append_audit_event_async(
            "admin.trial_updated",
            user.username,
            {"target_user_id": target_user_id, "active": active, "days": days},
            risk="medium",
            tenant_id=tenant_id,
        )
        return {"user_id": target_user_id, "tenant_id": tenant_id, "subscription": subscription}

    async def change_plan(self, user: CurrentUser, target_user_id: str, plan: str) -> dict:
        self._ensure_ceo_admin(user)
        plan_id = subscription_service.normalize_plan(plan)
        if not any(item["id"] == plan_id for item in subscription_service.plans()):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "invalid_plan"})
        tenant_id = await repositories.tenant_id_for_user(target_user_id)
        if tenant_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "user_not_found"})
        updated = await repositories.admin_change_tenant_plan(tenant_id, plan_id, subscription_service.limits_for(plan_id))
        await repositories.record_runtime_event(
            "admin.plan_changed",
            "ok",
            {"target_user_id": target_user_id, "plan": plan_id},
            tenant_id=tenant_id,
        )
        await append_audit_event_async(
            "admin.plan_changed",
            user.username,
            {"target_user_id": target_user_id, "plan": plan_id},
            risk="medium",
            tenant_id=tenant_id,
        )
        return {"user_id": target_user_id, "tenant_id": tenant_id, "subscription": updated}


admin_service = AdminService()
