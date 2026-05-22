from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import require_permission
from app.schemas.common import CurrentUser
from app.services.knowledge_service import knowledge_service
from app.services.regulatory_service import regulatory_service


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/items")
async def knowledge_items(_: CurrentUser = Depends(require_permission("knowledge:read"))) -> list[dict]:
    return knowledge_service.list_items()


@router.get("/regulatory")
async def regulatory_items(_: CurrentUser = Depends(require_permission("knowledge:read"))) -> list[dict]:
    return regulatory_service.list_items()
