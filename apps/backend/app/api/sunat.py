from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user
from app.schemas.common import (
    CurrentUser,
    SunatAuxiliaryCredentialIn,
    SunatAuxiliaryCredentialStatusOut,
    SunatAuxiliaryPreparationIn,
    SunatConnectIn,
    SunatConnectionOut,
    SunatConnectionStatusOut,
    SunatDisconnectIn,
    SunatSyncIn,
)
from app.services.sunat_service import sunat_service


router = APIRouter(prefix="/sunat", tags=["sunat"])


@router.get("/auxiliary-access/requirements")
async def auxiliary_access_requirements() -> dict:
    return sunat_service.auxiliary_access_requirements()


@router.get("/data-classification")
async def data_classification() -> dict:
    return sunat_service.data_classification()


@router.get("/status", response_model=SunatConnectionStatusOut)
async def status(
    workspace_id: str | None = None,
    empresa_id: str | None = None,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    return await sunat_service.status(user, workspace_id, empresa_id)


@router.get("/connections", response_model=list[SunatConnectionOut])
async def list_connections(
    workspace_id: str | None = None,
    empresa_id: str | None = None,
    user: CurrentUser = Depends(get_current_user),
) -> list[dict]:
    return await sunat_service.list_connections(user, workspace_id, empresa_id)


@router.get("/connections/{connection_id}", response_model=SunatConnectionOut)
async def get_connection(connection_id: str, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await sunat_service.get_connection(user, connection_id)


@router.post("/connections/connect")
async def connect(payload: SunatConnectIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await sunat_service.connect(user, payload.model_dump())


@router.post("/auxiliary-access/prepare")
async def prepare_auxiliary_access(payload: SunatAuxiliaryPreparationIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await sunat_service.prepare_auxiliary_access(user, payload.model_dump())


@router.post("/auxiliary/credentials", response_model=SunatAuxiliaryCredentialStatusOut)
async def store_auxiliary_credentials(payload: SunatAuxiliaryCredentialIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await sunat_service.store_auxiliary_credentials(user, payload.model_dump())


@router.get("/auxiliary/status", response_model=SunatAuxiliaryCredentialStatusOut)
async def auxiliary_credentials_status(
    workspace_id: str = Query(min_length=3, max_length=64),
    empresa_id: str = Query(min_length=3, max_length=64),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    return await sunat_service.auxiliary_credentials_status(user, workspace_id, empresa_id)


@router.delete("/auxiliary/credentials", response_model=SunatAuxiliaryCredentialStatusOut)
async def delete_auxiliary_credentials(
    workspace_id: str = Query(min_length=3, max_length=64),
    empresa_id: str = Query(min_length=3, max_length=64),
    reason: str = Query(default="user_revoked", min_length=3, max_length=240),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    return await sunat_service.delete_auxiliary_credentials(user, workspace_id, empresa_id, reason)


@router.post("/connections/{connection_id}/disconnect")
async def disconnect(connection_id: str, payload: SunatDisconnectIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await sunat_service.disconnect(user, connection_id, payload.model_dump())


@router.post("/connections/{connection_id}/sync")
async def sync(connection_id: str, payload: SunatSyncIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await sunat_service.sync(user, connection_id, payload.model_dump())
