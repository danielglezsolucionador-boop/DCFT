from __future__ import annotations

from pathlib import PurePath

from app.core.audit import append_audit_event_async
from app.core.config import settings
from app.db import repositories


class DocumentService:
    async def ingest(self, payload: dict, actor: str, tenant_id: str) -> dict:
        safe_filename = PurePath(payload["filename"]).name
        doc_type = payload.get("declared_type") or self._classify(safe_filename)
        document_payload = {
            "document_type": doc_type,
            "metadata": {**payload, "filename": safe_filename},
        }
        ingestion_payload = {
            "status": "ocr_ready" if settings.ocr_enabled else "placeholder_disabled",
            "ocr_status": "provider_configured" if settings.ocr_enabled else "placeholder_disabled",
            "explanation": "OCR provider is disabled; DCFT registered metadata only." if not settings.ocr_enabled else "OCR provider configured for controlled processing.",
        }
        record = await repositories.create_document(document_payload, ingestion_payload, tenant_id)
        await append_audit_event_async(
            "document.ingested",
            actor,
            {
                "document_id": record["document"]["id"],
                "document_type": doc_type,
                "ocr_status": record["ingestion"]["ocr_status"],
            },
            risk="medium",
            tenant_id=tenant_id,
        )
        await repositories.record_runtime_event(
            "product.document_ingested",
            "ok",
            {"actor": actor, "document_type": doc_type, "ocr_status": record["ingestion"]["ocr_status"]},
            tenant_id=tenant_id,
        )
        return record

    async def list(self, tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        return await repositories.list_documents(tenant_id, limit, offset)

    async def list_ingestions(self, tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        return await repositories.list_document_ingestions(tenant_id, limit, offset)

    def _classify(self, filename: str) -> str:
        name = filename.lower()
        if "sunat" in name or "esquela" in name:
            return "sunat_notice"
        if "factura" in name or "invoice" in name:
            return "invoice"
        if "balance" in name or "estado" in name:
            return "financial_statement"
        return "unknown"


document_service = DocumentService()
