from __future__ import annotations

import uuid

from app.core.audit import append_audit_event, utc_now
from app.core.storage import store


class RecommendationService:
    def __init__(self) -> None:
        self._store = store("recommendations")

    def create(self, payload: dict, actor: str, tenant_id: str, plan: str) -> dict:
        facts = payload.get("facts", {})
        explanation = self._explain(payload["category"], facts, plan)
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": utc_now(),
            "tenant_id": tenant_id,
            "requested_by": actor,
            "status": "ready",
            "plan": plan,
            "recommendation": explanation["recommendation"],
            "explainability": explanation,
            **payload,
        }
        self._store.update([], lambda rows: rows.append(record))
        append_audit_event("recommendation.created", actor, {"id": record["id"], "category": record["category"]}, risk="medium", tenant_id=tenant_id)
        return record

    def list(self, tenant_id: str, limit: int = 100) -> list[dict]:
        return [row for row in self._store.read([]) if row["tenant_id"] == tenant_id][-limit:]

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