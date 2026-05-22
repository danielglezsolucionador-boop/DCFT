from __future__ import annotations

from app.core.audit import append_audit_event_async
from app.db import repositories


class RecommendationService:
    async def create(self, payload: dict, actor: str, tenant_id: str, plan: str) -> dict:
        facts = payload.get("facts", {})
        explanation = self._explain(payload["category"], facts, plan)
        record_payload = {
            "requested_by": actor,
            "plan": plan,
            "recommendation": explanation["recommendation"],
            "explainability": explanation,
            **payload,
        }
        record = await repositories.create_recommendation(record_payload, tenant_id, payload["category"])
        await append_audit_event_async("recommendation.created", actor, {"id": record["id"], "category": record["category"]}, risk="medium", tenant_id=tenant_id)
        return record

    async def list(self, tenant_id: str, limit: int = 100) -> list[dict]:
        return await repositories.list_recommendations(tenant_id, limit)

    def _explain(self, category: str, facts: dict, plan: str) -> dict:
        if category == "tax":
            recommendation = "Revisar obligaciones y evidencia documental antes de cualquier presentacion. DCFT no declara impuestos ni modifica SUNAT."
        elif category == "financial":
            recommendation = "Priorizar liquidez, conciliacion y trazabilidad antes de tomar decisiones de pago o financiamiento."
        else:
            recommendation = "Preparar revision humana con datos verificables y evidencia suficiente."
        return {
            "method": "deterministic_rules_no_external_ai",
            "inputs_used": sorted(facts.keys()),
            "plan_scope": plan,
            "limitations": ["No legal/accounting official advice", "No autonomous filing", "No bank/SUNAT action"],
            "recommendation": recommendation,
        }


recommendation_service = RecommendationService()
