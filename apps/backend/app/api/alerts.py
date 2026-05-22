from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import require_permission
from app.schemas.common import AlertIn, CurrentUser
from app.services.alert_service import alert_service


router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(limit: int = 100, user: CurrentUser = Depends(require_permission("alerts:read"))) -> list[dict]:
    return await alert_service.list(user.tenant_id, limit)


@router.post("")
async def create_alert(payload: AlertIn, user: CurrentUser = Depends(require_permission("alerts:write"))) -> dict:
    return await alert_service.create(payload.model_dump(), user.username, user.tenant_id)
