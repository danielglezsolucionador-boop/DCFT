from __future__ import annotations

import uuid

from app.core.audit import append_audit_event, utc_now
from app.core.config import settings
from app.core.storage import store


class DocumentService:
    def __init__(self) -> None:
        self._documents = store("documents")
        self._ingestions = store("document_ingestions")

    def ingest(self, payload: dict, actor: str, tenant_id: str) -> dict:
        doc_type = payload.get("declared_type") or self._classify(payload["filename"])
        document = {
            "id": str(uuid.uuid4()),
            "timestamp": utc_now(),
            "tenant_id": tenant_id,
            "status": "registered",
            "document_type": doc_type,
            "metadata": payload,
        }
        ingestion = {
            "id": str(uuid.uuid4()),
            "timestamp": utc_now(),
            "tenant_id": tenant_id,
            "document_id": document["id"],
            "status": "ocr_ready" if settings.ocr_enabled else "placeholder_disabled",
            "ocr_status": "provider_configured" if settings.ocr_enabled else "placeholder_disabled",
            "explanation": "OCR provider is disabled; DCFT registered metadata only." if not settings.ocr_enabled else "OCR provider configured for controlled processing.",
        }
        self._documents.update([], lambda rows: rows.append(document))
        self._ingestions.update([], lambda rows: rows.append(ingestion))
        append_audit_event("document.ingested", actor, {"document_id": document["id"], "document_type": doc_type, "ocr_status": ingestion["ocr_status"]}, risk="medium", tenant_id=tenant_id)
        return {"document": document, "ingestion": ingestion}

    def list(self, tenant_id: str, limit: int = 100) -> list[dict]:
        return [row for row in self._documents.read([]) if row["tenant_id"] == tenant_id][-limit:]

    def list_ingestions(self, tenant_id: str, limit: int = 100) -> list[dict]:
        return [row for row in self._ingestions.read([]) if row["tenant_id"] == tenant_id][-limit:]

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