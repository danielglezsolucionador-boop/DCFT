from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import client_key, get_current_user
from app.core.rate_limit import enforce_rate_limit
from app.schemas.common import CurrentUser, LoginRequest, TokenResponse
from app.services.auth_service import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request) -> TokenResponse:
    enforce_rate_limit(client_key(request, f"login:{payload.username.lower()}"), limit=25, window_seconds=60)
    token = await auth_service.authenticate(payload.username, payload.password)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    return TokenResponse(access_token=token)


@router.get("/me", response_model=CurrentUser)
async def me(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return user
