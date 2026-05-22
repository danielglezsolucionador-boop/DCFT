from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.db.session import database_status


router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    db = await database_status()
    ok = db["status"] == "ok"
    return {
        "status": "ok" if ok else "degraded",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "production_ready": settings.production_ready,
        "staging_ready": settings.staging_ready,
        "modules": {
            "backend": "active",
            "auth": "active",
            "multi_tenant": "base_ready",
            "subscriptions": "active",
            "audit": "immutable_hash_chain",
            "governance": "hitl_required",
            "documents": "metadata_ingestion",
            "ocr": "placeholder_disabled" if not settings.ocr_enabled else "provider_configured",
            "ai_pipeline": "provider_disabled" if not settings.ai_provider_enabled else "provider_configured",
            "database": db["status"],
        },
        "database": db,
        "security_warnings": settings.security_warnings(),
    }
