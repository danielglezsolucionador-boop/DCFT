from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import client_key, require_permission
from app.core.rate_limit import enforce_rate_limit
from app.core.rbac import enforce_permission
from app.schemas.common import CurrentUser, WorkflowAdvanceIn, WorkflowIn
from app.services.subscription_service import subscription_service
from app.services.workflow_service import workflow_service


router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("")
async def list_workflows(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_permission("workflows:read")),
) -> list[dict]:
    return await workflow_service.list(user.tenant_id, limit, offset)


@router.post("")
async def create_workflow(request: Request, payload: WorkflowIn, user: CurrentUser = Depends(require_permission("workflows:write"))) -> dict:
    enforce_rate_limit(client_key(request, f"workflow:{user.tenant_id}"), limit=120, window_seconds=60)
    await subscription_service.enforce_limit(user.tenant_id, user.plan, "workflows")
    if payload.risk in {"high", "critical"}:
        enforce_permission(user.role, "workflows:high_risk")
    if payload.risk == "critical":
        enforce_permission(user.role, "*")
    return await workflow_service.create(payload.model_dump(), user.username, user.tenant_id)


@router.post("/{workflow_id}/advance")
async def advance_workflow(
    request: Request,
    workflow_id: str,
    payload: WorkflowAdvanceIn,
    user: CurrentUser = Depends(require_permission("workflows:advance")),
) -> dict:
    enforce_rate_limit(client_key(request, f"workflow-advance:{user.tenant_id}"), limit=180, window_seconds=60)
    result = await workflow_service.advance(workflow_id, payload.model_dump(), user.username, user.tenant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="workflow_not_found")
    return result
