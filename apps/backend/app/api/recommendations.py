from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import require_permission
from app.schemas.common import CurrentUser, RecommendationIn
from app.services.recommendation_service import recommendation_service


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("")
async def list_recommendations(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_permission("recommendations:read")),
) -> list[dict]:
    return await recommendation_service.list(user.tenant_id, limit, offset)


@router.post("")
async def create_recommendation(payload: RecommendationIn, user: CurrentUser = Depends(require_permission("recommendations:write"))) -> dict:
    return await recommendation_service.create(payload.model_dump(), user.username, user.tenant_id, user.plan)
