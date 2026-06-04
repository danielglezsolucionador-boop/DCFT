from __future__ import annotations

import re
import uuid

from fastapi import HTTPException, status

from app.core.audit import append_audit_event_async
from app.core.security import create_access_token, hash_password
from app.db import repositories
from app.schemas.common import CurrentUser
from app.services.subscription_service import subscription_service


ONBOARDING_VIDEO_SLOTS = [
    {
        "id": "sunat_auxiliary_user",
        "title": "Como crear usuario secundario / auxiliar SUNAT",
        "description": "Antes de conectar tu empresa, mira este video de 2 minutos para crear un acceso seguro de consulta.",
        "placeholder": True,
        "duration_hint": "2 minutos",
    },
    {
        "id": "connect_company",
        "title": "Como conectar tu empresa a DCFT",
        "description": "Prepara RUC, razon social y workspace para que DCFT lea el contexto correcto sin acciones oficiales.",
        "placeholder": True,
        "duration_hint": "2 minutos",
    },
    {
        "id": "interpret_diagnosis",
        "title": "Como interpretar tu diagnostico empresarial",
        "description": "Aprende a leer alertas, semaforo empresarial y prioridades antes de abrir un flujo operativo.",
        "placeholder": True,
        "duration_hint": "2 minutos",
    },
]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:46] or "tenant"


class OnboardingService:
    async def status(self) -> dict:
        return {
            "signup_enabled": True,
            "plans": subscription_service.plans(),
            "steps": [
                "Elegir Estudiante, MYPE o Premium",
                "Crear cuenta segura",
                "Registrar RUC solo para MYPE/Premium",
                "Activar trial Premium de 7 dias cuando aplique",
                "Preparar Clave SOL auxiliar solo lectura sin conectar SUNAT real",
            ],
            "boundaries": [
                "DCFT no ejecuta declaraciones ni acciones oficiales autonomas.",
                "Los workflows de riesgo requieren aprobacion humana.",
                "La foundation SUNAT solo prepara usuario secundario/auxiliar y consentimiento.",
            ],
        }

    async def create_tenant(self, payload: dict) -> dict:
        plan = subscription_service.normalize_plan(payload["plan"])
        if not any(item["id"] == plan for item in subscription_service.plans()):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_plan")
        plan_definition = subscription_service.current(plan)
        account_type = payload.get("account_type") or ("student" if plan == "student" else "business")
        requires_ruc = bool(plan_definition.get("requires_ruc"))
        ruc = (payload.get("ruc") or "").strip()
        razon_social = (payload.get("razon_social") or payload["tenant_name"]).strip()
        if plan == "student":
            account_type = "student"
            ruc = ""
        elif requires_ruc and not ruc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "ruc_required_for_business_plan", "plan": plan},
            )
        company_payload = None
        if ruc:
            company_payload = {
                "ruc": ruc,
                "razon_social": razon_social,
                "nombre_comercial": payload.get("nombre_comercial") or razon_social,
                "regimen_tributario": payload.get("regimen_tributario") or "mype_tributario",
                "estado": "active",
                "pais": "PE",
                "moneda": "PEN",
            }
        trial_days = int(plan_definition.get("trial_days") or 0) if payload.get("trial_requested", True) else 0
        tenant_id = payload.get("tenant_id") or f"{_slug(payload['tenant_name'])}-{uuid.uuid4().hex[:8]}"
        result = await repositories.create_tenant_with_admin(
            tenant_id=tenant_id,
            tenant_name=payload["tenant_name"],
            admin_username=payload["admin_username"],
            password_hash=hash_password(payload["admin_password"]),
            plan=plan,
            limits=subscription_service.limits_for(plan),
            account_type=account_type,
            trial_days=trial_days,
            company_payload=company_payload,
        )
        if not result["created"]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result["reason"])
        await append_audit_event_async(
            "onboarding.tenant_created",
            payload["admin_username"],
            {"tenant_id": tenant_id, "plan": plan, "account_type": account_type, "trial_days": trial_days},
            risk="medium",
            tenant_id=tenant_id,
        )
        await repositories.record_runtime_event(
            "product.onboarding_completed",
            "ok",
            {"plan": plan, "admin_username": payload["admin_username"], "account_type": account_type},
            tenant_id=tenant_id,
        )
        token = create_access_token(payload["admin_username"], [], tenant_id, plan)
        return {
            "tenant_id": tenant_id,
            "admin_username": payload["admin_username"],
            "plan": plan_definition,
            "trial": {
                "status": result["trial_status"],
                "started_at": result["trial_started_at"],
                "ends_at": result["trial_ends_at"],
                "days": trial_days,
            },
            "company": result.get("company"),
            "workspace": result.get("workspace"),
            "context": result.get("context"),
            "access_token": token,
            "token_type": "bearer",
            "next_steps": [
                "Completar diagnostico inicial guiado",
                "Ver modulos premium bloqueados antes de upgrade",
                "Preparar usuario SUNAT secundario con permisos minimos cuando corresponda",
                "No ingresar Clave SOL principal ni credenciales reales en esta foundation",
            ],
        }

    async def progress(self, user: CurrentUser) -> dict:
        progress = await repositories.onboarding_progress(user.tenant_id, user.user_id)
        seen = set(progress["videos_seen"])
        return {
            **progress,
            "videos": [
                {
                    **video,
                    "seen": video["id"] in seen,
                    "button_label": "Visto" if video["id"] in seen else "Marcar como visto",
                }
                for video in ONBOARDING_VIDEO_SLOTS
            ],
        }

    async def mark_video_seen(self, user: CurrentUser, video_id: str) -> dict:
        if video_id not in {video["id"] for video in ONBOARDING_VIDEO_SLOTS}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "onboarding_video_not_found"})
        progress = await repositories.mark_onboarding_video_seen(user.tenant_id, user.user_id, video_id)
        await repositories.record_runtime_event(
            "product.onboarding_video_seen",
            "ok",
            {"video_id": video_id},
            tenant_id=user.tenant_id,
        )
        await append_audit_event_async(
            "onboarding.video_seen",
            user.username,
            {"video_id": video_id},
            risk="low",
            tenant_id=user.tenant_id,
        )
        return await self.progress(user)


onboarding_service = OnboardingService()
