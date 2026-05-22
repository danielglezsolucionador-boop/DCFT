from __future__ import annotations


KNOWLEDGE_ITEMS = [
    {"id": "kpi-liquidity", "domain": "finance", "title": "Liquidez corriente", "status": "available", "source": "internal educational registry"},
    {"id": "tax-sunat-notices", "domain": "tax", "title": "Esquelas SUNAT", "status": "review_required", "source": "internal regulatory registry"},
    {"id": "accounting-evidence", "domain": "accounting", "title": "Evidencia contable", "status": "available", "source": "internal operating standard"},
]


class KnowledgeService:
    def list_items(self) -> list[dict]:
        return KNOWLEDGE_ITEMS


knowledge_service = KnowledgeService()