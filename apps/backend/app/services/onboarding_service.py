from __future__ import annotations

import re
import secrets
import uuid

from fastapi import HTTPException, status

from app.core.audit import append_audit_event_async
from app.core.credential_vault import CredentialVault
from app.core.credential_vault import CredentialVaultError
from app.core.credential_vault import CredentialVaultInvalidKey
from app.core.credential_vault import CredentialVaultNotConfigured
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
        "title": "Como conectar SUNAT con Usuario SOL",
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
                "Preparar acceso SUNAT SOL cifrado para diagnóstico autorizado",
            ],
            "boundaries": [
                "DCFT no ejecuta declaraciones ni acciones oficiales autonomas.",
                "Los workflows de riesgo requieren aprobacion humana.",
                "La foundation SUNAT prepara acceso SOL cifrado y consentimiento, sin acciones irreversibles.",
            ],
        }

    def _safe_existing_company_status(self, entry: dict | None) -> dict:
        if entry is None:
            return {
                "exists": False,
                "ruc": "",
                "usuario_sol_masked": None,
                "has_sunat_connection": False,
                "subscription_status": "none",
                "plan": None,
                "can_continue": False,
                "can_update_sol": False,
                "can_checkout": False,
            }
        subscription = entry.get("subscription") or {}
        raw_status = str(subscription.get("status") or "none").lower()
        effective_plan = subscription_service.normalize_plan(str(subscription.get("plan_effective") or subscription.get("plan") or "free"))
        active_commercial = raw_status == "active" and effective_plan in {"mype", "premium"}
        if active_commercial:
            subscription_status = "active"
        elif raw_status in {"pending", "pending_payment", "past_due", "unpaid"}:
            subscription_status = "pending"
        elif raw_status in {"expired", "cancelled", "canceled"}:
            subscription_status = "expired"
        else:
            subscription_status = "none"
        credential = entry.get("credential") or {}
        connection = entry.get("connection") or {}
        checkout = entry.get("checkout") or {}
        return {
            "exists": True,
            "ruc": entry["company"]["ruc"],
            "usuario_sol_masked": credential.get("sunat_username_masked") or connection.get("auxiliary_user_alias") or None,
            "has_sunat_connection": bool(credential.get("id") or connection.get("id")),
            "subscription_status": subscription_status,
            "plan": effective_plan if effective_plan in {"mype", "premium"} else None,
            "checkout_status": checkout.get("status"),
            "checkout_url": checkout.get("checkout_url"),
            "can_continue": True,
            "can_update_sol": True,
            "can_checkout": not active_commercial,
        }

    async def company_sunat_access_status(self, ruc: str) -> dict:
        entry = await repositories.company_access_entry_by_ruc(ruc)
        status_payload = self._safe_existing_company_status(entry)
        return {**status_payload, "ruc": ruc.strip() if entry is None else status_payload["ruc"]}

    def _current_user_for_entry(self, entry: dict) -> CurrentUser:
        user = entry["user"]
        return CurrentUser(
            user_id=user["id"],
            username=user["username"],
            tenant_id=user["tenant_id"],
            role=user["role"],
            plan=user["plan"],
            email_verified=user.get("email_verified", True),
            scopes=[],
            permissions=[],
        )

    def _assert_existing_sol_username(self, entry: dict, username: str) -> None:
        encrypted = entry.get("sunat_username_encrypted")
        if not encrypted:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "sunat_sol_connection_missing",
                    "message": "Este RUC existe, pero falta actualizar el acceso SOL antes de continuar.",
                },
            )
        try:
            stored_username = CredentialVault.from_settings().decrypt(encrypted)
        except CredentialVaultNotConfigured as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "credential_vault_key_missing", "message": "No se puede validar Usuario SOL sin vault configurado."},
            ) from exc
        except CredentialVaultInvalidKey as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "credential_vault_key_invalid", "message": "No se puede validar Usuario SOL con vault inválido."},
            ) from exc
        except CredentialVaultError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "credential_vault_decrypt_failed", "message": "No se pudo validar el Usuario SOL guardado."},
            ) from exc
        if stored_username.strip().lower() != username.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "usuario_sol_mismatch",
                    "message": "El Usuario SOL no coincide con el acceso guardado. Actualiza el acceso SOL para continuar.",
                },
            )

    async def _existing_company_response(self, entry: dict, payload: dict, *, credential: dict | None = None, event_type: str) -> dict:
        plan = subscription_service.normalize_plan(payload["plan"])
        billing_cycle = payload.get("billing_cycle") or "monthly"
        current_user = self._current_user_for_entry(entry)
        safe_status = self._safe_existing_company_status(entry)
        active_commercial = safe_status["subscription_status"] == "active"
        provider_status = payment_service.provider_status()
        checkout = None
        if not active_commercial and not provider_status["payment_provider_missing"] and provider_status.get("provider_supported", False):
            latest_checkout = entry.get("checkout") or {}
            if (
                latest_checkout.get("status") == "pending"
                and latest_checkout.get("checkout_url")
                and latest_checkout.get("plan") == plan
                and latest_checkout.get("billing_cycle") == billing_cycle
            ):
                checkout = latest_checkout
            else:
                checkout = await payment_service.create_checkout(current_user, plan, billing_cycle)
        token_plan = (entry.get("subscription") or {}).get("plan_effective") or current_user.plan or "free"
        token = create_access_token(current_user.username, [], current_user.tenant_id, token_plan)
        credential_payload = credential or entry.get("credential") or {}
        if credential is not None:
            safe_status = {
                **safe_status,
                "usuario_sol_masked": credential.get("sunat_username_masked") or safe_status.get("usuario_sol_masked"),
                "has_sunat_connection": True,
            }
        message = (
            "Cuenta empresarial activa. Puedes entrar al dashboard empresa."
            if active_commercial
            else (
                "Checkout creado. Tu plan se activa solo cuando Mercado Pago confirme el pago."
                if checkout
                else "Pago pendiente de configuración. Tu acceso no se activará hasta completar el pago."
            )
        )
        await repositories.record_runtime_event(
            event_type,
            "warning" if not active_commercial else "ok",
            {
                "ruc": entry["company"]["ruc"],
                "plan_requested": plan,
                "billing_cycle": billing_cycle,
                "subscription_status": safe_status["subscription_status"],
                "payment_provider": provider_status.get("provider"),
                "payment_provider_missing": provider_status["payment_provider_missing"],
                "sunat_username_masked": credential_payload.get("sunat_username_masked") or safe_status.get("usuario_sol_masked"),
                "password_echo": False,
            },
            tenant_id=current_user.tenant_id,
        )
        return {
            "tenant_id": current_user.tenant_id,
            "admin_username": current_user.username,
            "access_token": token,
            "token_type": "bearer",
            "existing_company": True,
            "ruc_status": safe_status,
            "plan_requested": plan,
            "billing_cycle": billing_cycle,
            "subscription_status": "active" if active_commercial else "pending_payment",
            "company": entry.get("company"),
            "workspace": entry.get("workspace"),
            "context": entry.get("context"),
            "sunat_credential": {
                "status": credential_payload.get("status") or ("CREDENTIAL_RECEIVED" if safe_status["has_sunat_connection"] else "PENDING"),
                "sunat_username_masked": credential_payload.get("sunat_username_masked") or safe_status.get("usuario_sol_masked"),
                "read_only": True,
                "remote_actions_enabled": False,
                "real_connector_enabled": False,
                "real_sunat_session": False,
            },
            "payment": {
                **provider_status,
                "message": message,
                "checkout": checkout,
            },
            "checkout_url": (checkout or {}).get("checkout_url"),
            "message": message,
            "next_steps": [
                "Continuar con el RUC existente.",
                "Actualizar acceso SOL solo si necesitas reconectar SUNAT.",
                "El plan se activa solo con webhook aprobado de Mercado Pago.",
            ],
        }

    async def continue_existing_company_sunat_access(self, payload: dict) -> dict:
        entry = await repositories.company_access_entry_by_ruc(payload["ruc"].strip())
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "ruc_not_found"})
        self._assert_existing_sol_username(entry, payload["sunat_username"])
        return await self._existing_company_response(entry, payload, event_type="product.company_sunat_existing_continue")

    async def create_tenant(self, payload: dict) -> dict:
        plan = subscription_service.normalize_plan(payload["plan"])
        if subscription_service.is_internal_plan(plan):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "internal_plan_forbidden"})
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
                "Conectar SUNAT con RUC, Usuario SOL y Clave SOL si la empresa autoriza el diagnóstico automático",
                "DCFT cifra la Clave SOL y no ejecuta pagos, declaraciones, emisiones ni modificaciones",
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
        existing_entry = await repositories.company_access_entry_by_ruc(ruc)
        if existing_entry is not None:
            current_user = self._current_user_for_entry(existing_entry)
            credential = await sunat_service.store_auxiliary_credentials(
                current_user,
                {
                    "empresa_id": existing_entry["company"]["id"],
                    "workspace_id": existing_entry["workspace"]["id"],
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
            refreshed_entry = await repositories.company_access_entry_by_ruc(ruc) or existing_entry
            await append_audit_event_async(
                "onboarding.company_sunat_access_existing_updated",
                current_user.username,
                {
                    "tenant_id": current_user.tenant_id,
                    "plan_requested": plan,
                    "billing_cycle": payload.get("billing_cycle") or "monthly",
                    "sunat_username_masked": credential.get("sunat_username_masked"),
                    "password_stored_plaintext": False,
                    "real_connector_enabled": False,
                },
                risk="medium",
                tenant_id=current_user.tenant_id,
            )
            return await self._existing_company_response(
                refreshed_entry,
                payload,
                credential=credential,
                event_type="product.company_sunat_existing_updated",
            )

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
                "sunat_sol_vault": "stored",
                "legacy_endpoint": "sunat_auxiliary_credentials",
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
