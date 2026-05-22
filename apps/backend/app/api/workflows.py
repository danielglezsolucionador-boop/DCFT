from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.schemas.common import CurrentUser, WorkflowAdvanceIn, WorkflowIn
from app.services.workflow_service import workflow_service


router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("")
def list_workflows(limit: int = 100, user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    return workflow_service.list(user.tenant_id, limit)


@router.post("")
def create_workflow(payload: WorkflowIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return workflow_service.create(payload.model_dump(), user.username, user.tenant_id)


@router.post("/{workflow_id}/advance")
def advance_workflow(workflow_id: str, payload: WorkflowAdvanceIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    result = workflow_service.advance(workflow_id, payload.model_dump(), user.username, user.tenant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="workflow_not_found")
    return result