from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.api.dependencies import client_key, get_current_user
from app.core.rate_limit import enforce_rate_limit
from app.schemas.common import CompanySunatAccessIn, CompanySunatContinueIn, CurrentUser, OnboardingTenantIn
from app.services.onboarding_service import onboarding_service


router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/status")
async def status() -> dict:
    return await onboarding_service.status()


@router.post("/tenants")
async def create_tenant(payload: OnboardingTenantIn, request: Request) -> dict:
    enforce_rate_limit(client_key(request, f"onboarding:{payload.admin_username.lower()}"), limit=5, window_seconds=300)
    return await onboarding_service.create_tenant(payload.model_dump())


@router.post("/company-sunat-access")
async def create_company_sunat_access(payload: CompanySunatAccessIn, request: Request) -> dict:
    enforce_rate_limit(client_key(request, f"company-sunat-access:{payload.ruc.lower()}"), limit=5, window_seconds=300)
    return await onboarding_service.create_company_sunat_access(payload.model_dump())


@router.get("/company-sunat-access/status")
async def company_sunat_access_status(request: Request, ruc: str = Query(min_length=8, max_length=20, pattern=r"^[0-9A-Za-z-]+$")) -> dict:
    enforce_rate_limit(client_key(request, f"company-sunat-access-status:{ruc.lower()}"), limit=20, window_seconds=300)
    return await onboarding_service.company_sunat_access_status(ruc)


@router.post("/company-sunat-access/continue")
async def continue_company_sunat_access(payload: CompanySunatContinueIn, request: Request) -> dict:
    enforce_rate_limit(client_key(request, f"company-sunat-access-continue:{payload.ruc.lower()}"), limit=8, window_seconds=300)
    return await onboarding_service.continue_existing_company_sunat_access(payload.model_dump())


@router.get("/progress")
async def progress(user: CurrentUser = Depends(get_current_user)) -> dict:
    return await onboarding_service.progress(user)


@router.post("/videos/{video_id}/seen")
async def mark_video_seen(video_id: str, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await onboarding_service.mark_video_seen(user, video_id)
