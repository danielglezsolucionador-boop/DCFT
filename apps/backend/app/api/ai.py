from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import AIRequestIn, CurrentUser
from app.services.ai_pipeline_service import ai_pipeline_service


router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/requests")
def list_ai_requests(limit: int = 100, user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    return ai_pipeline_service.list(user.tenant_id, limit)


@router.post("/requests")
def create_ai_request(payload: AIRequestIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return ai_pipeline_service.create(payload.model_dump(), user.username, user.tenant_id)