from __future__ import annotations

from app.core.runtime_status import runtime_snapshot
from app.db.repositories import dashboard_counts
from app.services.knowledge_service import knowledge_service
from app.services.regulatory_service import regulatory_service
from app.services.subscription_service import subscription_service


class DashboardService:
    async def summary(self, tenant_id: str, plan: str, database: dict) -> dict:
        counts = await dashboard_counts(tenant_id)
        return {
            "product": "DCFT - Doctor Contable Financiero Tributario",
            "tagline": "Tu copiloto empresarial premium.",
            "tenant_id": tenant_id,
            "plan": subscription_service.current(plan),
            "runtime": runtime_snapshot(database),
            "counts": {
                **counts,
                "knowledge_items": len(knowledge_service.list_items()),
                "regulatory_items": len(regulatory_service.list_items()),
            },
            "boundaries": [
                "No autonomous tax filing.",
                "No SUNAT, bank, or official document modification.",
                "No fake AI or OCR responses.",
                "Human approval required for critical actions.",
            ],
        }


dashboard_service = DashboardService()
