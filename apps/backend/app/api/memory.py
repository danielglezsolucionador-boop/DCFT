from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import require_permission
from app.schemas.common import CurrentUser, MemoryRecordIn
from app.services.memory_service import memory_service


router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/records")
async def list_records(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_permission("memory:read")),
) -> list[dict]:
    return await memory_service.list(user.tenant_id, limit, offset)


@router.post("/records")
async def record_memory(payload: MemoryRecordIn, user: CurrentUser = Depends(require_permission("memory:write"))) -> dict:
    return await memory_service.record(user.tenant_id, user.username, payload.memory_type, payload.model_dump())
