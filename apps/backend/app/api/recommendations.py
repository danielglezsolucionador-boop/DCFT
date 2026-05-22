from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import CurrentUser, RecommendationIn
from app.services.recommendation_service import recommendation_service


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("")
def list_recommendations(limit: int = 100, user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    return recommendation_service.list(user.tenant_id, limit)


@router.post("")
def create_recommendation(payload: RecommendationIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return recommendation_service.create(payload.model_dump(), user.username, user.tenant_id, user.plan)