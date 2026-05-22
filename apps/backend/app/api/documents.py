from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import require_permission
from app.schemas.common import CurrentUser, DocumentIn
from app.services.document_service import document_service
from app.services.subscription_service import subscription_service


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
async def list_documents(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_permission("documents:read")),
) -> list[dict]:
    return await document_service.list(user.tenant_id, limit, offset)


@router.get("/ingestions")
async def list_ingestions(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_permission("documents:read")),
) -> list[dict]:
    return await document_service.list_ingestions(user.tenant_id, limit, offset)


@router.post("/ingest")
async def ingest_document(payload: DocumentIn, user: CurrentUser = Depends(require_permission("documents:write"))) -> dict:
    await subscription_service.enforce_limit(user.tenant_id, user.plan, "documents")
    return await document_service.ingest(payload.model_dump(), user.username, user.tenant_id)
