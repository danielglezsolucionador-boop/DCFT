from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import require_permission
from app.schemas.common import CurrentUser
from app.services.embedding_service import embedding_service
from app.services.knowledge_service import knowledge_service
from app.services.regulatory_service import regulatory_service
from app.services.retrieval_service import retrieval_service


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/items")
async def knowledge_items(_: CurrentUser = Depends(require_permission("knowledge:read"))) -> list[dict]:
    return knowledge_service.list_items()


@router.get("/regulatory")
async def regulatory_items(_: CurrentUser = Depends(require_permission("knowledge:read"))) -> list[dict]:
    return regulatory_service.list_items()


@router.get("/search")
async def search(
    q: str = Query(min_length=3, max_length=500),
    limit: int = Query(default=10, ge=1, le=50),
    user: CurrentUser = Depends(require_permission("knowledge:read")),
) -> dict:
    return await retrieval_service.search(user.tenant_id, q, limit)


@router.get("/embedding-search")
async def embedding_search(
    q: str = Query(min_length=3, max_length=500),
    limit: int = Query(default=10, ge=1, le=50),
    dimensions: int = Query(default=64, ge=16, le=256),
    user: CurrentUser = Depends(require_permission("knowledge:read")),
) -> dict:
    return await embedding_service.search(user.tenant_id, q, limit, dimensions)
