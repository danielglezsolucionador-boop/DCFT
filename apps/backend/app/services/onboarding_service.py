from __future__ import annotations

import re
import uuid

from fastapi import HTTPException, status

from app.core.audit import append_audit_event_async
from app.core.security import create_access_token, hash_password
from app.db import repositories
from app.services.subscription_service import subscription_service


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:46] or "tenant"


class OnboardingService:
    async def status(self) -> dict:
        return {
            "signup_enabled": True,
            "plans": subscription_service.plans(),
            "steps": [
                "Crear espacio de trabajo",
                "Entrar como tenant_admin",
                "Registrar una alerta o documento real",
                "Revisar audit trail y limites del plan",
            ],
            "boundaries": [
                "DCFT no ejecuta declaraciones ni acciones oficiales autonomas.",
                "Los workflows de riesgo requieren aprobacion humana.",
            ],
        }

    async def create_tenant(self, payload: dict) -> dict:
        plan = subscription_service.normalize_plan(payload["plan"])
        if not any(item["id"] == plan for item in subscription_service.plans()):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_plan")
        tenant_id = payload.get("tenant_id") or f"{_slug(payload['tenant_name'])}-{uuid.uuid4().hex[:8]}"
        result = await repositories.create_tenant_with_admin(
            tenant_id=tenant_id,
            tenant_name=payload["tenant_name"],
            admin_username=payload["admin_username"],
            password_hash=hash_password(payload["admin_password"]),
            plan=plan,
            limits=subscription_service.limits_for(plan),
        )
        if not result["created"]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result["reason"])
        await append_audit_event_async(
            "onboarding.tenant_created",
            payload["admin_username"],
            {"tenant_id": tenant_id, "plan": plan},
            risk="medium",
            tenant_id=tenant_id,
        )
        await repositories.record_runtime_event(
            "product.onboarding_completed",
            "ok",
            {"plan": plan, "admin_username": payload["admin_username"]},
            tenant_id=tenant_id,
        )
        token = create_access_token(payload["admin_username"], [], tenant_id, plan)
        return {
            "tenant_id": tenant_id,
            "admin_username": payload["admin_username"],
            "plan": subscription_service.current(plan),
            "access_token": token,
            "token_type": "bearer",
            "next_steps": [
                "Validar datos del negocio",
                "Crear primera alerta operativa",
                "Revisar limites del plan",
                "Invitar usuarios solo cuando sea necesario",
            ],
        }


onboarding_service = OnboardingService()
