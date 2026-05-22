from __future__ import annotations

import time
import asyncio

from fastapi import APIRouter

from app.core.runtime_status import runtime_snapshot
from app.db.repositories import audit_integrity_summary, runtime_event_summary
from app.db.session import database_status


router = APIRouter(tags=["runtime"])
_runtime_heavy_cache: dict[str, object] = {"expires_at": 0.0, "data": {}}
_runtime_heavy_cache_lock = asyncio.Lock()


@router.get("/runtime/status")
async def runtime_status() -> dict:
    snapshot = runtime_snapshot(await database_status())
    now = time.monotonic()
    if float(_runtime_heavy_cache["expires_at"]) <= now:
        async with _runtime_heavy_cache_lock:
            now = time.monotonic()
            if float(_runtime_heavy_cache["expires_at"]) <= now:
                _runtime_heavy_cache["data"] = {
                    "audit_integrity": await audit_integrity_summary(limit=5000),
                    "persistent_observability": await runtime_event_summary(limit=5000),
                }
                _runtime_heavy_cache["expires_at"] = now + 2.0
    snapshot.update(_runtime_heavy_cache["data"])
    return snapshot
