from __future__ import annotations

from fastapi import APIRouter

from app.services.knowledge_service import knowledge_service
from app.services.regulatory_service import regulatory_service


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/items")
def knowledge_items() -> list[dict]:
    return knowledge_service.list_items()


@router.get("/regulatory")
def regulatory_items() -> list[dict]:
    return regulatory_service.list_items()