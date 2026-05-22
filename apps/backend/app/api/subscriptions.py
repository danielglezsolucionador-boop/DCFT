from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import CurrentUser
from app.services.subscription_service import subscription_service


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/plans")
def plans() -> list[dict]:
    return subscription_service.plans()


@router.get("/current")
def current(user: CurrentUser = Depends(get_current_user)) -> dict:
    return subscription_service.current(user.plan)