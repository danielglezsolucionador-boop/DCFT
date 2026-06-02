from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import require_permission
from app.schemas.common import CurrentUser, TaxWorkflowIn
from app.services.workflow_service import workflow_service


router = APIRouter(prefix="/tax-workflows", tags=["tax-workflows"])


TEMPLATES = {
    "sunat_notice_review": {
        "name": "Revision controlada de esquela SUNAT",
        "steps": [
            "Registrar evidencia documental y verificar procedencia de la comunicacion.",
            "Consultar fuentes regulatorias SUNAT y jurisprudencia fiscal versionada.",
            "Identificar obligaciones, plazos y riesgos declarados en los facts.",
            "Preparar checklist para revision humana contable/tributaria.",
            "Bloquear cualquier presentacion, pago o modificacion oficial hasta aprobacion humana.",
        ],
        "regulatory_queries": ["SUNAT esquela plazo obligacion", "Codigo Tributario infracciones sanciones"],
    },
    "monthly_obligation_review": {
        "name": "Revision mensual de obligaciones tributarias",
        "steps": [
            "Validar periodo tributario y ultimo digito de RUC declarado.",
            "Consultar cronograma SUNAT versionado y fuentes regulatorias aplicables.",
            "Contrastar documentos, alertas y memoria operacional del tenant.",
            "Preparar resumen de obligaciones para revision humana.",
            "Bloquear cualquier declaracion o pago oficial hasta aprobacion humana.",
        ],
        "regulatory_queries": ["SUNAT cronograma obligaciones mensuales", "UIT Codigo Tributario"],
    },
}


@router.get("/templates")
async def templates(_: CurrentUser = Depends(require_permission("workflows:read"))) -> dict:
    return {"templates": TEMPLATES, "boundaries": ["no_autonomous_filing", "human_review_required", "source_provenance_required"]}


@router.post("")
async def create_tax_workflow(payload: TaxWorkflowIn, user: CurrentUser = Depends(require_permission("workflows:write"))) -> dict:
    template = TEMPLATES[payload.workflow_type]
    workflow_payload = {
        "name": template["name"],
        "objective": payload.objective,
        "steps": template["steps"],
        "risk": "high",
        "tax_workflow_type": payload.workflow_type,
        "facts": payload.facts,
        "regulatory_queries": template["regulatory_queries"],
        "boundaries": ["no_autonomous_filing", "no_sunat_modification", "human_checkpoint_required"],
    }
    return await workflow_service.create(workflow_payload, user.username, user.tenant_id)
