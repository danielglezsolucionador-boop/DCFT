from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import CurrentUser


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def user_profile(user: CurrentUser = Depends(get_current_user)) -> dict:
    return {"user": user.model_dump(), "tenant_isolation": "active", "privacy_boundary": "tenant_scoped"}