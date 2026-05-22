from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import bearer, client_key, get_current_user
from app.core.rate_limit import enforce_rate_limit
from app.core.security import decode_access_token
from app.schemas.common import CurrentUser, LoginRequest, TokenResponse
from app.services.auth_service import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request) -> TokenResponse:
    login_key = client_key(request, f"login:{payload.username.lower()}")
    enforce_rate_limit(login_key, limit=25, window_seconds=60)
    if await auth_service.is_login_locked(payload.username, login_key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="login_temporarily_locked")
    token = await auth_service.authenticate(payload.username, payload.password)
    if token is None:
        await auth_service.record_login_failure(payload.username, login_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    await auth_service.record_login_success(payload.username, login_key)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=CurrentUser)
async def me(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return user


@router.post("/logout")
async def logout(
    credentials=Depends(bearer),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    payload = decode_access_token(credentials.credentials)
    await auth_service.revoke_token(payload)
    return {"status": "revoked", "tenant_id": user.tenant_id}
