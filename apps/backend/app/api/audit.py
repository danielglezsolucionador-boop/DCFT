from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import require_permission
from app.db.repositories import audit_integrity_summary, list_audit_events
from app.schemas.common import CurrentUser


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events")
async def events(
    limit: int = Query(default=100, ge=1, le=500),
    user: CurrentUser = Depends(require_permission("audit:read")),
) -> dict:
    return {
        "tenant_id": user.tenant_id,
        "events": await list_audit_events(user.tenant_id, limit=min(limit, 500)),
        "integrity": await audit_integrity_summary(user.tenant_id, limit=5000),
    }
