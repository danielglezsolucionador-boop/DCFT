from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import AlertIn, CurrentUser
from app.services.alert_service import alert_service


router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts(limit: int = 100, user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    return alert_service.list(user.tenant_id, limit)


@router.post("")
def create_alert(payload: AlertIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return alert_service.create(payload.model_dump(), user.username, user.tenant_id)