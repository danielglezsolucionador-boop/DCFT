from __future__ import annotations

from sqlalchemy import select

from app.core.audit import append_audit_event_async
from app.core.observability import metrics_registry
from app.core.rbac import permissions_for_role
from app.core.security import create_access_token, verify_password
from app.db.models import Tenant, User
from app.db.session import async_session
from app.schemas.common import CurrentUser


class AuthService:
    async def authenticate(self, username: str, password: str) -> str | None:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            if user is None or not user.active or not verify_password(password, user.password_hash):
                metrics_registry.record_auth_failure()
                await append_audit_event_async("auth.login_failed", username, {"username": username}, risk="medium")
                return None
            tenant = await session.get(Tenant, user.tenant_id)
            if tenant is None or tenant.status != "active":
                metrics_registry.record_auth_failure()
                await append_audit_event_async(
                    "auth.login_failed",
                    username,
                    {"username": username, "reason": "tenant_inactive_or_missing"},
                    risk="high",
                )
                return None

        await append_audit_event_async("auth.login_success", username, {"username": username}, tenant_id=user.tenant_id)
        return create_access_token(username, [], user.tenant_id, user.plan)

    async def resolve_user(self, payload: dict) -> CurrentUser | None:
        username = payload.get("sub")
        token_tenant_id = payload.get("tenant_id")
        if not username or not token_tenant_id:
            return None
        async with async_session() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            if user is None or not user.active or user.tenant_id != token_tenant_id:
                return None
            tenant = await session.get(Tenant, user.tenant_id)
            if tenant is None or tenant.status != "active":
                return None
            return CurrentUser(
                username=user.username,
                tenant_id=user.tenant_id,
                role=user.role,
                plan=user.plan,
                scopes=[],
                permissions=permissions_for_role(user.role),
            )


auth_service = AuthService()
