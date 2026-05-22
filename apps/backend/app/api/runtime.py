from __future__ import annotations

from fastapi import APIRouter

from app.core.runtime_status import runtime_snapshot
from app.db.session import database_status


router = APIRouter(tags=["runtime"])


@router.get("/runtime/status")
async def runtime_status() -> dict:
    return runtime_snapshot(await database_status())