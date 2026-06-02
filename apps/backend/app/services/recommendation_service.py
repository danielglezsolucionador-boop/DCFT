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
        await repositories.record_runtime_event("product.recommendation_created", "ok", {"actor": actor, "category": record["category"]}, tenant_id=tenant_id)
        return record

    async def list(self, tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        return await repositories.list_recommendations(tenant_id, limit, offset)

    def _explain(self, category: str, facts: dict, plan: str) -> dict:
        if category == "tax":
            rule_id = "tax_review_before_official_action_v1"
            recommendation = "Revisar obligaciones y evidencia documental antes de cualquier presentacion. DCFT no declara impuestos ni modifica SUNAT."
            decision_path = ["category=tax", "official_action_boundary", "human_review_required"]
        elif category == "financial":
            rule_id = "financial_liquidity_traceability_v1"
            recommendation = "Priorizar liquidez, conciliacion y trazabilidad antes de tomar decisiones de pago o financiamiento."
            decision_path = ["category=financial", "liquidity_traceability_priority", "human_review_required"]
        else:
            rule_id = "generic_review_with_evidence_v1"
            recommendation = "Preparar revision humana con datos verificables y evidencia suficiente."
            decision_path = [f"category={category}", "generic_controlled_review", "human_review_required"]
        evidence = [
            {"key": key, "value_type": type(value).__name__, "value_preview": str(value)[:120]}
            for key, value in sorted(facts.items())
        ]
        return {
            "method": "deterministic_rules_no_external_ai",
            "rule_id": rule_id,
            "inputs_used": sorted(facts.keys()),
            "evidence": evidence,
            "decision_path": decision_path,
            "plan_scope": plan,
            "confidence": "bounded_by_declared_facts",
            "human_review_required": True,
            "limitations": ["No legal/accounting official advice", "No autonomous filing", "No bank/SUNAT action"],
            "recommendation": recommendation,
        }


recommendation_service = RecommendationService()
