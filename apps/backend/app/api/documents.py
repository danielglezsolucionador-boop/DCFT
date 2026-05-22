from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import require_permission
from app.schemas.common import CurrentUser, DocumentIn
from app.services.document_service import document_service


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
async def list_documents(limit: int = 100, user: CurrentUser = Depends(require_permission("documents:read"))) -> list[dict]:
    return await document_service.list(user.tenant_id, limit)


@router.get("/ingestions")
async def list_ingestions(limit: int = 100, user: CurrentUser = Depends(require_permission("documents:read"))) -> list[dict]:
    return await document_service.list_ingestions(user.tenant_id, limit)


@router.post("/ingest")
async def ingest_document(payload: DocumentIn, user: CurrentUser = Depends(require_permission("documents:write"))) -> dict:
    return await document_service.ingest(payload.model_dump(), user.username, user.tenant_id)
