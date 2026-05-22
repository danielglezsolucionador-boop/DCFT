from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import CurrentUser, DocumentIn
from app.services.document_service import document_service


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(limit: int = 100, user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    return document_service.list(user.tenant_id, limit)


@router.get("/ingestions")
def list_ingestions(limit: int = 100, user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    return document_service.list_ingestions(user.tenant_id, limit)


@router.post("/ingest")
def ingest_document(payload: DocumentIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return document_service.ingest(payload.model_dump(), user.username, user.tenant_id)