from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import require_permission
from app.schemas.common import CurrentUser, SubscriptionUpdateIn
from app.services.subscription_service import subscription_service


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/plans")
def plans() -> list[dict]:
    return subscription_service.plans()


@router.get("/current")
async def current(user: CurrentUser = Depends(require_permission("subscriptions:read"))) -> dict:
    return subscription_service.current(user.plan)


@router.patch("/current")
async def change_current(payload: SubscriptionUpdateIn, user: CurrentUser = Depends(require_permission("subscriptions:manage"))) -> dict:
    return await subscription_service.change_plan(user.tenant_id, user.username, payload.plan)
