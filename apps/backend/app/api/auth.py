from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import bearer, client_key, get_current_user
from app.core.rate_limit import enforce_rate_limit
from app.core.security import decode_access_token
from app.db import repositories
from app.schemas.common import CurrentUser, EmailVerificationResendIn, EmailVerificationResponse, LoginRequest, TokenResponse
from app.services.auth_service import EmailNotVerifiedError, auth_service
from app.services.email_service import EMAIL_NOT_VERIFIED_MESSAGE, EMAIL_PROVIDER_MISSING_MESSAGE, email_service, hash_verification_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request) -> TokenResponse:
    identifier = payload.login_identifier
    login_key = client_key(request, f"login:{identifier.lower()}")
    enforce_rate_limit(login_key, limit=25, window_seconds=60)
    if await auth_service.is_login_locked(identifier, login_key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="login_temporarily_locked")
    try:
        token = await auth_service.authenticate(identifier, payload.password)
    except EmailNotVerifiedError:
        await auth_service.record_login_failure(identifier, login_key, reason="email_not_verified")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "email_not_verified", "message": EMAIL_NOT_VERIFIED_MESSAGE},
        )
    if token is None:
        await auth_service.record_login_failure(identifier, login_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    await auth_service.record_login_success(identifier, login_key)
    return TokenResponse(access_token=token)


@router.post("/resend-verification", response_model=EmailVerificationResponse)
async def resend_verification(payload: EmailVerificationResendIn, request: Request) -> EmailVerificationResponse:
    resend_key = client_key(request, f"resend-email:{payload.username.lower()}")
    enforce_rate_limit(resend_key, limit=5, window_seconds=300)
    user = await repositories.get_user_by_username(payload.username)
    if user is None:
        return EmailVerificationResponse(
            email_verified=False,
            sent=False,
            email_provider_missing=email_service.provider_status()["email_provider_missing"],
            message=EMAIL_PROVIDER_MISSING_MESSAGE if email_service.provider_status()["email_provider_missing"] else EMAIL_NOT_VERIFIED_MESSAGE,
        )
    if user["email_verified"]:
        return EmailVerificationResponse(email_verified=True, sent=False, email_provider_missing=False, message="Cuenta ya verificada.")
    result = await email_service.issue_verification_email(user_id=user["id"], tenant_id=user["tenant_id"], email=user["username"])
    return EmailVerificationResponse(
        email_verified=False,
        sent=bool(result.get("sent")),
        email_provider_missing=bool(result.get("email_provider_missing")),
        message=str(result.get("message") or EMAIL_NOT_VERIFIED_MESSAGE),
    )


@router.get("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(token: str) -> EmailVerificationResponse:
    if not token or len(token) < 24:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invalid_token"})
    result = await repositories.verify_email_token_hash(hash_verification_token(token))
    if not result["email_verified"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": result["reason"]})
    await repositories.record_runtime_event(
        "product.email_verified",
        "ok",
        {"username": result["username"], "plan": result["plan"]},
        tenant_id=result["tenant_id"],
    )
    return EmailVerificationResponse(
        email_verified=True,
        sent=False,
        email_provider_missing=False,
        message="Correo confirmado. Ya puedes iniciar sesion.",
    )


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
