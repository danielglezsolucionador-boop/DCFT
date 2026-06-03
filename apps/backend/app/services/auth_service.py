from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.audit import append_audit_event_async
from app.core.observability import metrics_registry
from app.core.rbac import permissions_for_role
from app.core.security import create_access_token, verify_password
from app.db.models import Subscription, Tenant, User
from app.db import repositories
from app.db.session import async_session
from app.schemas.common import CurrentUser


class AuthService:
    async def authenticate(self, username: str, password: str) -> str | None:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            password_ok = bool(user and user.active and await asyncio.to_thread(verify_password, password, user.password_hash))
            if not password_ok:
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

    async def record_login_failure(self, username: str, client: str, reason: str = "invalid_credentials") -> None:
        await repositories.record_auth_event(username.lower(), client, "failed", reason)

    async def record_login_success(self, username: str, client: str) -> None:
        await repositories.record_auth_event(username.lower(), client, "success", "authenticated")

    async def is_login_locked(self, username: str, client: str) -> bool:
        return await repositories.count_recent_auth_failures(username.lower(), client, minutes=5) >= 10

    async def is_token_revoked(self, payload: dict) -> bool:
        jti = payload.get("jti")
        return bool(jti and await repositories.is_token_revoked(jti))

    async def revoke_token(self, payload: dict, reason: str = "logout") -> None:
        jti = payload.get("jti")
        subject = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        expires_at = payload.get("exp")
        if not jti or not subject or not tenant_id or expires_at is None:
            return
        if isinstance(expires_at, (int, float)):
            expiration = datetime.fromtimestamp(expires_at, tz=timezone.utc)
        elif isinstance(expires_at, datetime):
            expiration = expires_at
        else:
            expiration = datetime.now(timezone.utc)
        await repositories.revoke_token(jti, subject, tenant_id, expiration, reason)
        await append_audit_event_async("auth.token_revoked", subject, {"reason": reason}, risk="low", tenant_id=tenant_id)

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
            subscription = (
                await session.execute(select(Subscription).where(Subscription.tenant_id == user.tenant_id, Subscription.status == "active"))
            ).scalar_one_or_none()
            plan = subscription.plan if subscription is not None else user.plan
            return CurrentUser(
                user_id=user.id,
                username=user.username,
                tenant_id=user.tenant_id,
                role=user.role,
                plan=plan,
                scopes=[],
                permissions=permissions_for_role(user.role),
            )


auth_service = AuthService()
