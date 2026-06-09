from __future__ import annotations

import re
import secrets
import uuid

from fastapi import HTTPException, status

from app.core.audit import append_audit_event_async
from app.core.security import create_access_token
from app.core.security import hash_password
from app.db import repositories
from app.schemas.common import CurrentUser
from app.services.payment_service import payment_service
from app.services.email_service import EMAIL_NOT_VERIFIED_MESSAGE, email_service
from app.services.subscription_service import subscription_service
from app.services.sunat_service import sunat_service


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
            email_verified=False,
        )
        if not result["created"]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result["reason"])
        email_result = await email_service.issue_verification_email(
            user_id=result["user_id"],
            tenant_id=tenant_id,
            email=payload["admin_username"],
        )
        await append_audit_event_async(
            "onboarding.tenant_created_pending_email_verification",
            payload["admin_username"],
            {
                "tenant_id": tenant_id,
                "plan": plan,
                "account_type": account_type,
                "trial_days": trial_days,
                "email_provider_missing": bool(email_result.get("email_provider_missing")),
            },
            risk="medium",
            tenant_id=tenant_id,
        )
        await repositories.record_runtime_event(
            "product.onboarding_completed",
            "ok",
            {
                "plan": plan,
                "admin_username": payload["admin_username"],
                "account_type": account_type,
                "email_verification_required": True,
                "email_provider_missing": bool(email_result.get("email_provider_missing")),
            },
            tenant_id=tenant_id,
        )
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
            "email_verification": {
                "required": True,
                "email_verified": False,
                "sent": bool(email_result.get("sent")),
                "email_provider_missing": bool(email_result.get("email_provider_missing")),
                "message": email_result.get("message") or EMAIL_NOT_VERIFIED_MESSAGE,
            },
            "next_steps": [
                "Confirmar correo antes de iniciar sesion.",
                "Completar diagnostico inicial guiado",
                "Ver modulos premium bloqueados antes de upgrade",
                "Preparar usuario SUNAT secundario con permisos minimos cuando corresponda",
                "No ingresar Clave SOL principal ni credenciales reales en esta foundation",
            ],
        }

    async def create_company_sunat_access(self, payload: dict) -> dict:
        plan = subscription_service.normalize_plan(payload["plan"])
        if plan not in {"mype", "premium"}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "invalid_company_plan"})
        if not payload.get("consent_accepted"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "sunat_consent_required", "message": "Debes aceptar el consentimiento SUNAT para continuar."},
            )

        ruc = payload["ruc"].strip()
        tenant_id = f"empresa-{_slug(ruc)}-{uuid.uuid4().hex[:8]}"
        tenant_name = f"Empresa RUC {ruc}"
        pending_reason_social = "Razón social pendiente de validación"
        admin_username = f"empresa_{ruc}_{uuid.uuid4().hex[:8]}@dcft.local"
        generated_password = secrets.token_urlsafe(36)
        result = await repositories.create_tenant_with_admin(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            admin_username=admin_username,
            password_hash=hash_password(generated_password),
            plan="free",
            limits=subscription_service.limits_for("free"),
            account_type="business",
            trial_days=0,
            company_payload={
                "ruc": ruc,
                "razon_social": pending_reason_social,
                "nombre_comercial": pending_reason_social,
                "regimen_tributario": "mype_tributario",
                "estado": "pending_payment",
                "pais": "PE",
                "moneda": "PEN",
            },
            email_verified=True,
            subscription_status="pending",
        )
        if not result["created"]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result["reason"])

        current_user = CurrentUser(
            user_id=result["user_id"],
            username=admin_username,
            tenant_id=tenant_id,
            role="tenant_admin",
            plan="free",
            email_verified=True,
            scopes=[],
            permissions=[],
        )
        credential = await sunat_service.store_auxiliary_credentials(
            current_user,
            {
                "empresa_id": result["company"]["id"],
                "workspace_id": result["workspace"]["id"],
                "ruc": ruc,
                "sunat_username": payload["sunat_username"],
                "sunat_password": payload["sunat_password"],
                "consent_accepted": True,
                "auxiliary_user_acknowledged": True,
                "read_only_acknowledged": True,
                "no_tax_action_acknowledged": True,
            },
            require_active_subscription=False,
        )

        provider_status = payment_service.provider_status()
        checkout = None
        if not provider_status["payment_provider_missing"] and provider_status.get("provider_supported", False):
            checkout = await payment_service.create_checkout(current_user, plan, payload.get("billing_cycle") or "monthly")

        await repositories.record_runtime_event(
            "product.company_sunat_access_pending_payment",
            "warning",
            {
                "plan_requested": plan,
                "billing_cycle": payload.get("billing_cycle") or "monthly",
                "payment_provider": provider_status.get("provider"),
                "payment_provider_missing": provider_status["payment_provider_missing"],
                "sunat_auxiliary_vault": "stored",
                "real_connector_enabled": False,
                "real_sunat_session": False,
            },
            tenant_id=tenant_id,
        )
        await append_audit_event_async(
            "onboarding.company_sunat_access_pending_payment",
            admin_username,
            {
                "tenant_id": tenant_id,
                "plan_requested": plan,
                "billing_cycle": payload.get("billing_cycle") or "monthly",
                "payment_provider_missing": provider_status["payment_provider_missing"],
                "sunat_username_masked": credential.get("sunat_username_masked"),
                "password_stored_plaintext": False,
                "real_connector_enabled": False,
            },
            risk="medium",
            tenant_id=tenant_id,
        )
        token = create_access_token(admin_username, [], tenant_id, "free")
        payment_message = (
            "Pago pendiente de configuración. Tu acceso no se activará hasta completar el pago."
            if provider_status["payment_provider_missing"]
            else "Checkout creado. Tu plan se activa solo cuando Mercado Pago confirme el pago."
        )
        return {
            "tenant_id": tenant_id,
            "admin_username": admin_username,
            "access_token": token,
            "token_type": "bearer",
            "plan_requested": plan,
            "billing_cycle": payload.get("billing_cycle") or "monthly",
            "subscription_status": "pending_payment",
            "company": result.get("company"),
            "workspace": result.get("workspace"),
            "context": result.get("context"),
            "sunat_credential": {
                "status": credential.get("status"),
                "sunat_username_masked": credential.get("sunat_username_masked"),
                "read_only": True,
                "remote_actions_enabled": False,
                "real_connector_enabled": False,
                "real_sunat_session": False,
            },
            "payment": {
                **provider_status,
                "message": payment_message,
                "checkout": checkout,
            },
            "checkout_url": (checkout or {}).get("checkout_url"),
            "message": payment_message,
            "next_steps": [
                "Completar pago MYPE/Premium.",
                "El plan no se activa hasta webhook aprobado de Mercado Pago.",
                "SUNAT real automático sigue apagado.",
                "Razón social pendiente de validación; no bloquea el flujo.",
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
