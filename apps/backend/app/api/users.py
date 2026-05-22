from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import require_permission
from app.schemas.common import CurrentUser


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def user_profile(user: CurrentUser = Depends(require_permission("users:read"))) -> dict:
    return {"user": user.model_dump(), "tenant_isolation": "active", "privacy_boundary": "tenant_scoped"}
