from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import (
    ActiveCompanyIn,
    ActiveOperationalContextOut,
    ActiveWorkspaceIn,
    CompanyIn,
    CompanyOut,
    CurrentUser,
    PermissionMatrixOut,
    WorkspaceIn,
    WorkspaceMembershipIn,
    WorkspaceMembershipOut,
    WorkspaceOut,
)
from app.services.identity_service import identity_service


router = APIRouter(prefix="/identity", tags=["identity"])


@router.post("/companies", response_model=CompanyOut)
async def create_company(payload: CompanyIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await identity_service.create_company(user, payload.model_dump())


@router.get("/companies", response_model=list[CompanyOut])
async def list_companies(user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    return await identity_service.list_companies(user)


@router.post("/workspaces", response_model=WorkspaceOut)
async def create_workspace(payload: WorkspaceIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await identity_service.create_workspace(user, payload.model_dump())


@router.get("/workspaces", response_model=list[WorkspaceOut])
async def list_workspaces(user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    return await identity_service.list_workspaces(user)


@router.post("/workspaces/{workspace_id}/memberships", response_model=WorkspaceMembershipOut)
async def assign_membership(
    workspace_id: str,
    payload: WorkspaceMembershipIn,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    return await identity_service.assign_membership(user, workspace_id, payload.model_dump())


@router.get("/permissions", response_model=PermissionMatrixOut)
async def permissions(user: CurrentUser = Depends(get_current_user)) -> dict:
    return await identity_service.permission_matrix(user)


@router.get("/context", response_model=ActiveOperationalContextOut)
async def active_context(user: CurrentUser = Depends(get_current_user)) -> dict:
    return await identity_service.get_context(user)


@router.post("/context/company", response_model=ActiveOperationalContextOut)
async def select_active_company(payload: ActiveCompanyIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await identity_service.set_active_company(user, payload.company_id)


@router.post("/context/workspace", response_model=ActiveOperationalContextOut)
async def select_active_workspace(payload: ActiveWorkspaceIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await identity_service.set_active_workspace(user, payload.workspace_id)
