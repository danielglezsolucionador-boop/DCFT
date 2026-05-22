from __future__ import annotations

from app.core.audit import read_audit_events
from app.core.runtime_status import runtime_snapshot
from app.services.alert_service import alert_service
from app.services.document_service import document_service
from app.services.knowledge_service import knowledge_service
from app.services.recommendation_service import recommendation_service
from app.services.regulatory_service import regulatory_service
from app.services.subscription_service import subscription_service
from app.services.workflow_service import workflow_service


class DashboardService:
    def summary(self, tenant_id: str, plan: str, database: dict) -> dict:
        alerts = alert_service.list(tenant_id)
        recommendations = recommendation_service.list(tenant_id)
        documents = document_service.list(tenant_id)
        workflows = workflow_service.list(tenant_id)
        audit_events = read_audit_events(10_000)
        return {
            "product": "DCFT - Doctor Contable Financiero Tributario",
            "tagline": "Tu copiloto empresarial premium.",
            "tenant_id": tenant_id,
            "plan": subscription_service.current(plan),
            "runtime": runtime_snapshot(database),
            "counts": {
                "alerts": len(alerts),
                "open_alerts": len([item for item in alerts if item["status"] == "open"]),
                "recommendations": len(recommendations),
                "documents": len(documents),
                "workflows": len(workflows),
                "audit_events": len(audit_events),
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