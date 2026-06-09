from __future__ import annotations

from fastapi import HTTPException, status

from app.db import repositories
from app.schemas.common import CurrentUser
from app.services.subscription_service import subscription_service


LEGACY_ROLE_MAP = {
    "super_admin": "ADMIN",
    "tenant_admin": "ADMIN",
    "operator": "PROFESSIONAL",
    "auditor": "STUDENT",
    "readonly": "STUDENT",
}

PLAN_MAP = {
    "free": "FREE",
    "student": "FREE",
    "free_student": "FREE",
    "business_basic": "PROFESSIONAL",
    "business_premium": "PREMIUM",
}

SUBSCRIPTION_SAFE_READ_PERMISSIONS = {
    "companies:read",
    "workspaces:read",
    "context:read",
    "permissions:read",
    "sunat:read",
}


class IdentityService:
    async def _role_for_user(self, user: CurrentUser, workspace_id: str | None = None) -> str:
        if workspace_id:
            workspace_role = await repositories.workspace_role_for_user(user.tenant_id, user.user_id, workspace_id)
            if workspace_role:
                return workspace_role
        if user.role in {"super_admin", "tenant_admin"}:
            return "ADMIN"
        return LEGACY_ROLE_MAP.get(user.role) or PLAN_MAP.get(user.plan, "FREE")

    async def require_business_permission(
        self,
        user: CurrentUser,
        permission: str,
        *,
        workspace_id: str | None = None,
    ) -> str:
        role_id = await self._role_for_user(user, workspace_id)
        permissions = await repositories.business_role_permissions(role_id)
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "business_permission_denied", "permission": permission, "role_id": role_id},
            )
        if permission not in SUBSCRIPTION_SAFE_READ_PERMISSIONS:
            await subscription_service.ensure_active_commercial_subscription(user.tenant_id, user.plan)
        return role_id

    async def create_company(self, user: CurrentUser, payload: dict) -> dict:
        await self.require_business_permission(user, "companies:create")
        created = await repositories.create_company(user.tenant_id, payload)
        if created is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "ruc_already_exists"})
        await repositories.record_runtime_event("identity.company_created", "ok", {"company_id": created["id"]}, user.tenant_id)
        return created

    async def list_companies(self, user: CurrentUser) -> list[dict]:
        await self.require_business_permission(user, "companies:read")
        return await repositories.list_companies(user.tenant_id)

    async def create_workspace(self, user: CurrentUser, payload: dict) -> dict:
        await self.require_business_permission(user, "workspaces:create")
        created = await repositories.create_workspace(user.tenant_id, user.user_id, payload)
        if created is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "invalid_company_or_plan_for_tenant"},
            )
        await repositories.record_runtime_event(
            "identity.workspace_created",
            "ok",
            {"workspace_id": created["id"], "company_id": created["empresa_id"]},
            user.tenant_id,
        )
        return created

    async def list_workspaces(self, user: CurrentUser) -> list[dict]:
        await self.require_business_permission(user, "workspaces:read")
        return await repositories.list_workspaces_for_user(user.tenant_id, user.user_id)

    async def assign_membership(self, user: CurrentUser, workspace_id: str, payload: dict) -> dict:
        await self.require_business_permission(user, "memberships:assign", workspace_id=workspace_id)
        assigned = await repositories.assign_workspace_membership(user.tenant_id, workspace_id, payload["user_id"], payload["role_id"])
        if assigned is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "invalid_workspace_user_or_role_for_tenant"},
            )
        await repositories.record_runtime_event(
            "identity.workspace_membership_assigned",
            "ok",
            {"workspace_id": workspace_id, "user_id": payload["user_id"], "role_id": payload["role_id"]},
            user.tenant_id,
        )
        return assigned

    async def permission_matrix(self, user: CurrentUser) -> dict:
        await self.require_business_permission(user, "permissions:read")
        roles = await repositories.list_business_roles()
        plans = await repositories.list_business_plans()
        return {
            "roles": {role["id"]: role["permissions"] for role in roles if role["estado"] == "active"},
            "plans": {
                plan["id"]: {"limits": plan["limits"], "features": plan["features"]}
                for plan in plans
                if plan["estado"] == "active"
            },
            "enforced_by_backend": True,
        }

    async def get_context(self, user: CurrentUser) -> dict:
        await self.require_business_permission(user, "context:read")
        return await repositories.get_active_context(user.tenant_id, user.user_id)

    async def set_active_company(self, user: CurrentUser, company_id: str) -> dict:
        await self.require_business_permission(user, "context:write")
        context = await repositories.set_active_company(user.tenant_id, user.user_id, company_id)
        if context is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "company_not_found_for_tenant"})
        await repositories.record_runtime_event("identity.active_company_selected", "ok", {"company_id": company_id}, user.tenant_id)
        return context

    async def set_active_workspace(self, user: CurrentUser, workspace_id: str) -> dict:
        await self.require_business_permission(user, "context:write", workspace_id=workspace_id)
        context = await repositories.set_active_workspace(user.tenant_id, user.user_id, workspace_id)
        if context is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "workspace_not_found_for_user"})
        await repositories.record_runtime_event(
            "identity.active_workspace_selected",
            "ok",
            {"workspace_id": workspace_id, "company_id": context["active_company_id"]},
            user.tenant_id,
        )
        return context


identity_service = IdentityService()
