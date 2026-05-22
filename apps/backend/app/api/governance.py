from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.schemas.common import ApprovalDecisionIn, ApprovalRequestIn, CurrentUser
from app.services.governance_service import governance_service


router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/approval-requests")
def list_approval_requests(limit: int = 100, user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    return governance_service.list(user.tenant_id, limit)


@router.post("/approval-requests")
def create_approval_request(payload: ApprovalRequestIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return governance_service.create_request(payload.model_dump(), user.username, user.tenant_id)


@router.post("/approval-requests/{request_id}/decision")
def decide_approval_request(request_id: str, payload: ApprovalDecisionIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    result = governance_service.decide(request_id, payload.decision, payload.reason, user.username, user.tenant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="approval_request_not_found")
    return result