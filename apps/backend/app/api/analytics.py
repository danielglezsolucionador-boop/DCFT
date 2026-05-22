from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import require_permission
from app.schemas.common import AnalyticsEventIn, CurrentUser
from app.services.analytics_service import analytics_service


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def summary(user: CurrentUser = Depends(require_permission("analytics:read"))) -> dict:
    return await analytics_service.summary(user.tenant_id)


@router.post("/events")
async def record_event(payload: AnalyticsEventIn, user: CurrentUser = Depends(require_permission("analytics:write"))) -> dict:
    return await analytics_service.record(user.tenant_id, user.username, payload.event_type, payload.metadata)
