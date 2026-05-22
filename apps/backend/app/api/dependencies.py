from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.audit import append_audit_event_async
from app.core.observability import metrics_registry
from app.core.rate_limit import enforce_rate_limit
from app.core.rbac import enforce_permission
from app.core.security import decode_access_token
from app.schemas.common import CurrentUser
from app.services.auth_service import auth_service


bearer = HTTPBearer(auto_error=False)


def client_key(request: Request, suffix: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{suffix}"


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> CurrentUser:
    if credentials is None:
        metrics_registry.record_auth_failure()
        await append_audit_event_async("auth.missing_token", "anonymous", {"path": request.url.path}, risk="medium")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_bearer_token")
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        enforce_rate_limit(client_key(request, "invalid-jwt"), limit=40, window_seconds=60)
        metrics_registry.record_auth_failure()
        await append_audit_event_async("auth.invalid_token", "anonymous", {"path": request.url.path}, risk="medium")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token") from exc
    user = await auth_service.resolve_user(payload)
    if user is None:
        enforce_rate_limit(client_key(request, "invalid-principal"), limit=40, window_seconds=60)
        metrics_registry.record_auth_failure()
        await append_audit_event_async(
            "auth.invalid_principal",
            payload.get("sub", "unknown"),
            {"path": request.url.path, "tenant_id": payload.get("tenant_id")},
            risk="high",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_principal")
    return user


def require_permission(permission: str) -> Callable:
    async def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        enforce_permission(user.role, permission)
        return user

    return dependency
