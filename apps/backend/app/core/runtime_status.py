from __future__ import annotations

from app.core.audit import read_audit_events
from app.core.config import settings
from app.core.observability import metrics_registry


def runtime_snapshot(database: dict | None = None) -> dict:
    return {
        "status": "active",
        "runtime_loop": "not_started_by_design",
        "busy_loop": False,
        "environment": settings.app_env,
        "staging_ready": settings.staging_ready,
        "production_ready": settings.production_ready,
        "zero_write_policy": True,
        "human_in_the_loop": True,
        "privacy_first": True,
        "ai_pipeline": "blocked_provider_disabled" if not settings.ai_provider_enabled else "provider_configured",
        "ocr_pipeline": "placeholder_disabled" if not settings.ocr_enabled else "provider_configured",
        "sunat_readonly_enabled": settings.sunat_readonly_enabled,
        "sunat_api_automation_enabled": settings.sunat_api_automation_enabled,
        "sensitive_actions_enabled": False,
        "raw_snapshot_storage": settings.sunat_store_raw_snapshots,
        "external_datalake_enabled": settings.sunat_external_datalake_enabled,
        "storage_backend": settings.sunat_storage_backend or "postgres",
        "real_sunat_session": False,
        "remote_actions_enabled": False,
        "real_connector_enabled": bool(settings.sunat_readonly_enabled or settings.sunat_api_automation_enabled),
        "database": database,
        "audit_events": len(read_audit_events(10_000)),
        "observability": metrics_registry.snapshot(),
        "notes": [
            "DCFT runtime exposes operational status only.",
            "No autonomous tax, banking, SUNAT, or legal filing action is enabled.",
            "Critical workflows require human checkpoints and approvals.",
        ],
    }
