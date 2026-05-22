from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import require_permission
from app.schemas.common import AIRequestIn, CurrentUser
from app.services.ai_pipeline_service import ai_pipeline_service


router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/requests")
async def list_ai_requests(limit: int = 100, user: CurrentUser = Depends(require_permission("ai:read"))) -> list[dict]:
    return await ai_pipeline_service.list(user.tenant_id, limit)


@router.post("/requests")
async def create_ai_request(payload: AIRequestIn, user: CurrentUser = Depends(require_permission("ai:request"))) -> dict:
    return await ai_pipeline_service.create(payload.model_dump(), user.username, user.tenant_id)
