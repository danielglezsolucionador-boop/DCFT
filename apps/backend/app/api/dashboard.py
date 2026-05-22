from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import require_permission
from app.db.session import database_status
from app.schemas.common import CurrentUser
from app.services.dashboard_service import dashboard_service


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def summary(user: CurrentUser = Depends(require_permission("dashboard:read"))) -> dict:
    return await dashboard_service.summary(user.tenant_id, user.plan, await database_status())
