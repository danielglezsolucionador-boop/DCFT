from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import require_permission
from app.schemas.common import CurrentUser, FeedbackIn
from app.services.feedback_service import feedback_service


router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("")
async def submit_feedback(payload: FeedbackIn, user: CurrentUser = Depends(require_permission("feedback:write"))) -> dict:
    return await feedback_service.submit(payload.model_dump(), user.username, user.tenant_id)
