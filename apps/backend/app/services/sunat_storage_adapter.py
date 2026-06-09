from __future__ import annotations

from app.core.config import settings
from app.db import repositories


class SunatStorageAdapter:
    backend = "postgres"
    external_datalake_enabled = False

    def status(self) -> dict:
        return {
            "storage_backend": settings.sunat_storage_backend or self.backend,
            "external_datalake_enabled": settings.sunat_external_datalake_enabled,
            "raw_snapshot_storage": settings.sunat_store_raw_snapshots,
        }

    async def store_snapshot(
        self,
        tenant_id: str,
        company_id: str,
        workspace_id: str,
        ruc: str,
        run_id: str,
        snapshot: dict,
    ) -> dict | None:
        if not settings.sunat_store_raw_snapshots:
            return None
        return await repositories.record_sunat_raw_snapshot(
            tenant_id,
            company_id,
            workspace_id,
            ruc,
            run_id,
            source=snapshot.get("source") or "sunat_readonly",
            snapshot_type=snapshot.get("snapshot_type") or "raw",
            content=snapshot.get("content") or {},
            metadata=snapshot.get("metadata") or {},
        )


sunat_storage_adapter = SunatStorageAdapter()
