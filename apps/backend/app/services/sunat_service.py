from __future__ import annotations

from fastapi import HTTPException, status
import unicodedata

from app.core.config import settings
from app.core.audit import append_audit_event_async
from app.core.credential_vault import (
    CredentialVault,
    CredentialVaultError,
    CredentialVaultInvalidKey,
    CredentialVaultNotConfigured,
    credential_vault_status,
    mask_identifier,
)
from app.db import repositories
from app.schemas.common import CurrentUser
from app.services.identity_service import identity_service
from app.services.subscription_service import subscription_service
from app.services.sunat_readonly_connector import sunat_readonly_connector
from app.services.sunat_storage_adapter import sunat_storage_adapter


CONSULTABLE_DATA = [
    "RUC",
    "razon_social",
    "estado_contribuyente",
    "condicion_contribuyente",
    "regimen_tributario",
    "datos_publicos_disponibles",
]

NON_CONSULTABLE_DATA = [
    "declaraciones_no_publicas",
    "firmas_digitales",
    "presentacion_de_formularios",
    "pagos_tributarios",
    "modificacion_de_datos_sunat",
    "credenciales_clave_sol",
]

AUXILIARY_ACCESS_REQUIREMENTS = {
    "required_permissions": [
        "usuario_secundario_clave_sol",
        "permisos_minimos_de_consulta",
        "modo_solo_lectura",
        "acceso_a_ficha_ruc_y_datos_publicos_disponibles",
    ],
    "not_required_permissions": [
        "presentar_declaraciones",
        "firmar_documentos",
        "enviar_formularios",
        "realizar_pagos",
        "modificar_datos_del_contribuyente",
        "usar_credenciales_principales",
    ],
    "risks": [
        "credenciales_auxiliares_mal_configuradas",
        "permisos_excesivos_asignados_en_sunat",
        "revocacion_no_realizada_por_el_usuario",
        "dependencia_de_conector_real_aun_no_habilitado",
    ],
    "limits": [
        "foundation_no_abre_sesion_real_sunat",
        "no_ejecuta_acciones_tributarias",
        "no_almacena_clave_sol_principal",
        "credencial_secundaria_solo_cifrada_si_vault_configurado",
        "solo_prepara_estado_consentimiento_auditoria_y_vault",
    ],
}

SUNAT_RECOMMENDED_QUERY_PERMISSIONS = [
    "Mis Declaraciones y pagos > Consultas",
    "Mis Declaraciones y pagos > Declaraciones y Pagos",
    "Mis Declaraciones y pagos > Consulta de transferencia dólares",
    "Mi RUC y Otros Registros > Mis Datos del RUC",
    "Mi RUC y Otros Registros > RUC",
    "Mi RUC y Otros Registros > Ficha RUC",
    "Mi RUC y Otros Registros > Captura de Acuse de Recibo",
    "Reporte Tributario y Aduanero > Reporte",
    "Reporte Tributario y Aduanero > Consulto mis reportes",
    "T-Registro > Consultas",
    "T-Registro > Registro de derechohabientes",
    "T-Registro > Consulta individual",
    "Envio Reporte Tributario > Envío Reporte Tributario",
    "Guía de Remisión Electrónica > Consulta de GRE",
    "Guía de Remisión Electrónica > Consulta de obligados",
    "Comprobantes de pago > Consulta de Validez de Comprobantes de Pago",
    "Comprobantes de pago > Consulta Integrada de Comprobantes de Pago",
]

SUNAT_API_AUTOMATION_PERMISSION = {
    "permission_name": "Credenciales de API SUNAT",
    "permission_type": "api_automation",
    "copy": (
        "Credenciales de API SUNAT permite habilitar servicios oficiales para consultas automáticas. "
        "Actívalo solo si deseas que DCFT use APIs oficiales de SUNAT para automatizar consultas."
    ),
    "warning": "Este permiso permite gestión de credenciales API. Solo actívalo si autorizas automatización mediante API.",
    "sensitive_actions_enabled": False,
    "read_only": True,
}

SUNAT_BLOCKED_MINIMUM_PERMISSIONS = [
]

SUNAT_MISSING_PERMISSION_MESSAGE = (
    "Para responder esta consulta falta habilitar el permiso SUNAT: {permission}. "
    "Entra a SUNAT → Administración de usuarios secundarios → Modificar programas → marca ese permiso."
)
SUNAT_SENSITIVE_PERMISSION_MESSAGE = (
    "Este permiso está disponible, pero DCFT no ejecuta acciones sensibles. Solo puede leer información consultable."
)

CONSENT_SCOPE = {
    "connection_type": "CLAVE_SOL_AUXILIAR",
    "read_only": True,
    "remote_actions_enabled": False,
    "consultable": CONSULTABLE_DATA,
    "not_consultable": NON_CONSULTABLE_DATA,
}

SUNAT_AUXILIARY_CONSENT_TEXT = (
    "Autorizo a DCFT a usar mi RUC, usuario secundario SUNAT y clave secundaria SUNAT para consultar "
    "información tributaria disponible en modo lectura, guardar evidencia, generar diagnóstico y mostrar "
    "recomendaciones. DCFT no realizará declaraciones, pagos, emisiones, modificaciones ni acciones irreversibles."
)

PILOT_REQUIREMENTS = {
    "student_tester_count": 1,
    "business_tester_count": 2,
    "business_requires_sunat_auxiliary": True,
    "mype_requires_sunat_auxiliary": True,
    "premium_requires_sunat_auxiliary": True,
    "principal_clave_sol_allowed": False,
}


def credential_security_status() -> dict:
    vault = credential_vault_status()
    enabled = bool(vault["configured"] and vault["valid"])
    return {
        "credential_capture_enabled": enabled,
        "credential_storage_enabled": enabled,
        "encrypted_credential_storage": enabled,
        "password_fields_accepted": enabled,
        "frontend_secret_echo": False,
        "vault_required_before_real_connection": True,
        "vault": vault,
    }


class SunatService:
    def readonly_flags(self) -> dict:
        return {
            "sunat_readonly_enabled": settings.sunat_readonly_enabled,
            "sensitive_actions_enabled": False,
            "raw_snapshot_storage": settings.sunat_store_raw_snapshots,
            "external_datalake_enabled": settings.sunat_external_datalake_enabled,
            "storage_backend": settings.sunat_storage_backend or "postgres",
            "real_connector_enabled": settings.sunat_readonly_enabled,
            "real_sunat_session": False,
            "remote_actions_enabled": False,
            "read_only": True,
        }

    async def _ensure_workspace_company(self, user: CurrentUser, empresa_id: str, workspace_id: str) -> tuple[dict, dict]:
        company = await repositories.get_company_for_tenant(user.tenant_id, empresa_id)
        workspace = await repositories.get_workspace_for_user(user.tenant_id, user.user_id, workspace_id)
        if company is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "company_not_found_for_tenant"})
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "workspace_not_found_for_user"})
        if workspace["empresa_id"] != empresa_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "workspace_company_mismatch"})
        return company, workspace

    def auxiliary_access_requirements(self) -> dict:
        return {
            **AUXILIARY_ACCESS_REQUIREMENTS,
            "recommended_permissions": SUNAT_RECOMMENDED_QUERY_PERMISSIONS,
            "api_automation_permission": SUNAT_API_AUTOMATION_PERMISSION,
            "blocked_minimum_permissions": SUNAT_BLOCKED_MINIMUM_PERMISSIONS,
            "pilot_requirements": PILOT_REQUIREMENTS,
            "consent_text": SUNAT_AUXILIARY_CONSENT_TEXT,
            "credential_security": credential_security_status(),
            "readonly_flags": self.readonly_flags(),
        }

    def data_classification(self) -> dict:
        return {
            "CONSULTABLE": CONSULTABLE_DATA,
            "NO_CONSULTABLE": NON_CONSULTABLE_DATA,
            "read_only": True,
            "remote_actions_enabled": False,
            "real_sunat_session": False,
            "real_connector_enabled": settings.sunat_readonly_enabled,
            "pilot_requires_auxiliary_user": True,
            "credential_capture_enabled": credential_security_status()["credential_capture_enabled"],
            "credential_storage_enabled": credential_security_status()["credential_storage_enabled"],
            "permission_discovery": True,
            "recommended_permissions": SUNAT_RECOMMENDED_QUERY_PERMISSIONS,
            "api_automation_permission": SUNAT_API_AUTOMATION_PERMISSION,
            "sensitive_actions_enabled": False,
            **self.readonly_flags(),
        }

    async def list_connections(
        self,
        user: CurrentUser,
        workspace_id: str | None = None,
        empresa_id: str | None = None,
    ) -> list[dict]:
        await identity_service.require_business_permission(user, "sunat:read", workspace_id=workspace_id)
        return await repositories.list_sunat_connections(user.tenant_id, user.user_id, workspace_id, empresa_id)

    async def status(self, user: CurrentUser, workspace_id: str | None = None, empresa_id: str | None = None) -> dict:
        connections = await self.list_connections(user, workspace_id, empresa_id)
        connection = connections[0] if connections else None
        security = credential_security_status()
        latest_run = None
        if workspace_id and empresa_id:
            latest_run = await repositories.latest_sunat_diagnostic_run(user.tenant_id, workspace_id, empresa_id)
        return {
            "connection": connection,
            "status": connection["estado"] if connection else "NOT_CONNECTED",
            "foundation_only": not settings.sunat_readonly_enabled,
            "real_connector_enabled": settings.sunat_readonly_enabled,
            "real_sunat_session": bool((latest_run or {}).get("real_sunat_session")),
            "read_only": True,
            "remote_actions_enabled": False,
            "pilot_requires_auxiliary_user": True,
            "credential_capture_enabled": security["credential_capture_enabled"],
            "credential_storage_enabled": security["credential_storage_enabled"],
            "readonly": self.readonly_flags(),
            "latest_readonly_run": latest_run,
        }

    async def get_connection(self, user: CurrentUser, connection_id: str) -> dict:
        connection = await repositories.get_sunat_connection_for_user(user.tenant_id, user.user_id, connection_id)
        if connection is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "sunat_connection_not_found"})
        await identity_service.require_business_permission(user, "sunat:read", workspace_id=connection["workspace_id"])
        return connection

    async def connect(self, user: CurrentUser, payload: dict) -> dict:
        await self._ensure_workspace_company(user, payload["empresa_id"], payload["workspace_id"])
        await identity_service.require_business_permission(user, "sunat:connect", workspace_id=payload["workspace_id"])
        required_flags = [
            "consent_accepted",
            "auxiliary_user_acknowledged",
            "read_only_acknowledged",
            "no_tax_action_acknowledged",
        ]
        missing_flags = [flag for flag in required_flags if not payload.get(flag)]
        if missing_flags:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "explicit_sunat_consent_required", "missing": missing_flags},
            )
        connection = await repositories.create_or_update_sunat_connection(user.tenant_id, user.user_id, payload)
        consent = await repositories.record_sunat_consent(user.tenant_id, user.user_id, connection, CONSENT_SCOPE)
        await repositories.record_sunat_connection_event(
            user.tenant_id,
            user.user_id,
            connection,
            "connect_requested",
            "pending_real_connector",
            {
                "consent_id": consent["id"],
                "connection_type": payload["connection_type"],
                "read_only": True,
                "remote_actions_enabled": False,
                "credential_reference_present": bool(payload.get("credential_reference")),
            },
        )
        await repositories.record_runtime_event(
            "sunat.connect_requested",
            "warning",
            {"connection_id": connection["id"], "foundation_only": True, "real_connector_enabled": False},
            user.tenant_id,
        )
        await append_audit_event_async(
            "sunat.connection_requested",
            user.username,
            {
                "connection_id": connection["id"],
                "empresa_id": connection["empresa_id"],
                "workspace_id": connection["workspace_id"],
                "consent_id": consent["id"],
                "read_only": True,
                "remote_actions_enabled": False,
            },
            risk="medium",
            tenant_id=user.tenant_id,
        )
        return {
            "connection": connection,
            "consent": consent,
            "status": connection["estado"],
            "foundation_only": True,
            "real_connector_enabled": False,
            "message": "SUNAT auxiliary foundation registered; real SUNAT connector is not enabled.",
        }

    async def prepare_auxiliary_access(self, user: CurrentUser, payload: dict) -> dict:
        company, workspace = await self._ensure_workspace_company(user, payload["empresa_id"], payload["workspace_id"])
        await identity_service.require_business_permission(user, "sunat:connect", workspace_id=payload["workspace_id"])
        if payload["ruc"] != company["ruc"]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "ruc_company_mismatch"})
        connection = await repositories.prepare_sunat_auxiliary_connection(user.tenant_id, user.user_id, payload)
        await repositories.record_sunat_connection_event(
            user.tenant_id,
            user.user_id,
            connection,
            "auxiliary_prepared",
            "pending_real_connector",
            {
                "workspace_id": workspace["id"],
                "read_only": True,
                "remote_actions_enabled": False,
                "credential_reference_present": False,
                "password_received": False,
            },
        )
        await repositories.record_runtime_event(
            "sunat.auxiliary_prepared",
            "warning",
            {"connection_id": connection["id"], "foundation_only": True, "real_connector_enabled": False},
            user.tenant_id,
        )
        await append_audit_event_async(
            "sunat.auxiliary_prepared",
            user.username,
            {
                "connection_id": connection["id"],
                "empresa_id": connection["empresa_id"],
                "workspace_id": connection["workspace_id"],
                "password_received": False,
                "read_only": True,
            },
            risk="low",
            tenant_id=user.tenant_id,
        )
        return {
            "connection": connection,
            "status": "PREPARED_PENDING_REAL_CONNECTOR",
            "foundation_only": True,
            "real_connector_enabled": False,
            "message": "Usuario SUNAT secundario preparado. DCFT no recibio ni guardo clave SUNAT.",
        }

    def _vault(self) -> CredentialVault:
        try:
            return CredentialVault.from_settings()
        except CredentialVaultNotConfigured as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "credential_vault_key_missing", "required_env": "DCFT_CREDENTIAL_ENCRYPTION_KEY"},
            ) from exc
        except CredentialVaultInvalidKey as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "credential_vault_key_invalid", "required_env": "DCFT_CREDENTIAL_ENCRYPTION_KEY"},
            ) from exc

    async def store_auxiliary_credentials(self, user: CurrentUser, payload: dict, *, require_active_subscription: bool = True) -> dict:
        company, workspace = await self._ensure_workspace_company(user, payload["empresa_id"], payload["workspace_id"])
        if require_active_subscription:
            await identity_service.require_business_permission(user, "sunat:connect", workspace_id=payload["workspace_id"])
        if payload["ruc"] != company["ruc"]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "ruc_company_mismatch"})
        required_flags = [
            "consent_accepted",
            "auxiliary_user_acknowledged",
            "read_only_acknowledged",
            "no_tax_action_acknowledged",
        ]
        missing_flags = [flag for flag in required_flags if not payload.get(flag)]
        if missing_flags:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "explicit_sunat_consent_required", "missing": missing_flags},
            )

        vault = self._vault()
        password = payload["sunat_password"].get_secret_value() if hasattr(payload["sunat_password"], "get_secret_value") else str(payload["sunat_password"])
        username = payload["sunat_username"].strip()
        try:
            username_encrypted = vault.encrypt(username)
            password_encrypted = vault.encrypt(password)
        except CredentialVaultError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "credential_vault_encrypt_failed"}) from exc

        username_masked = mask_identifier(username)
        ruc_masked = mask_identifier(payload["ruc"], visible_prefix=2, visible_suffix=3)
        stored = await repositories.upsert_sunat_credential(
            user.tenant_id,
            user.user_id,
            {**payload, "sunat_username": username, "ruc": payload["ruc"]},
            username_encrypted=username_encrypted,
            password_encrypted=password_encrypted,
            username_masked=username_masked,
            ruc_masked=ruc_masked,
        )
        credential = stored["credential"]
        connection = stored["connection"]
        consent = await repositories.record_sunat_consent(user.tenant_id, user.user_id, connection, CONSENT_SCOPE)
        await repositories.record_sunat_connection_event(
            user.tenant_id,
            user.user_id,
            connection,
            "credential_received",
            "encrypted_pending_validation",
            {
                "workspace_id": workspace["id"],
                "credential_id": credential["id"],
                "consent_id": consent["id"],
                "read_only": True,
                "remote_actions_enabled": False,
                "real_connector_enabled": False,
                "username_masked": username_masked,
                "password_received": True,
                "password_stored_plaintext": False,
            },
        )
        await repositories.record_runtime_event(
            "sunat.credential_received",
            "warning",
            {"credential_id": credential["id"], "foundation_only": True, "real_connector_enabled": False},
            user.tenant_id,
        )
        await append_audit_event_async(
            "sunat.credential_received",
            user.username,
            {
                "credential_id": credential["id"],
                "empresa_id": credential["empresa_id"],
                "workspace_id": credential["workspace_id"],
                "username_masked": username_masked,
                "password_received": True,
                "password_stored_plaintext": False,
                "read_only": True,
                "remote_actions_enabled": False,
            },
            risk="medium",
            tenant_id=user.tenant_id,
        )
        connector_status = await sunat_readonly_connector.validate_credentials(ruc=payload["ruc"], username=username, password=password)
        return {
            **credential,
            "status": credential["status"],
            "consent": consent,
            "read_only_connector": connector_status.__dict__,
        }

    async def auxiliary_credentials_status(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> dict:
        await self._ensure_workspace_company(user, empresa_id, workspace_id)
        await identity_service.require_business_permission(user, "sunat:read", workspace_id=workspace_id)
        credential = await repositories.get_sunat_credential_for_user(user.tenant_id, user.user_id, workspace_id, empresa_id)
        security = credential_security_status()
        if credential is None:
            return {
                "status": "PENDING",
                "read_only": True,
                "remote_actions_enabled": False,
                "real_sunat_session": False,
                "real_connector_enabled": False,
                "credential_capture_enabled": security["credential_capture_enabled"],
                "credential_storage_enabled": security["credential_storage_enabled"],
                "encrypted_credential_storage": security["encrypted_credential_storage"],
            }
        return {
            **credential,
            "ruc": None,
            "credential_capture_enabled": security["credential_capture_enabled"],
            "credential_storage_enabled": security["credential_storage_enabled"],
            "encrypted_credential_storage": security["encrypted_credential_storage"],
        }

    async def delete_auxiliary_credentials(self, user: CurrentUser, workspace_id: str, empresa_id: str, reason: str = "user_revoked") -> dict:
        await self._ensure_workspace_company(user, empresa_id, workspace_id)
        await identity_service.require_business_permission(user, "sunat:disconnect", workspace_id=workspace_id)
        disconnected = await repositories.disconnect_sunat_credential(user.tenant_id, user.user_id, workspace_id, empresa_id, reason)
        if disconnected is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "sunat_credential_not_found"})
        await repositories.record_runtime_event(
            "sunat.credential_disconnected",
            "ok",
            {"credential_id": disconnected["id"], "reason": reason},
            user.tenant_id,
        )
        await append_audit_event_async(
            "sunat.credential_disconnected",
            user.username,
            {"credential_id": disconnected["id"], "reason": reason, "password_active": False},
            risk="medium",
            tenant_id=user.tenant_id,
        )
        return {
            **disconnected,
            "ruc": None,
            "status": "DISCONNECTED",
            "credential_capture_enabled": credential_security_status()["credential_capture_enabled"],
            "credential_storage_enabled": credential_security_status()["credential_storage_enabled"],
            "encrypted_credential_storage": credential_security_status()["encrypted_credential_storage"],
        }

    async def disconnect(self, user: CurrentUser, connection_id: str, payload: dict) -> dict:
        connection = await self.get_connection(user, connection_id)
        await identity_service.require_business_permission(user, "sunat:disconnect", workspace_id=connection["workspace_id"])
        disconnected = await repositories.disconnect_sunat_connection(user.tenant_id, user.user_id, connection_id, payload["reason"])
        if disconnected is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "sunat_connection_not_found"})
        await repositories.record_sunat_connection_event(
            user.tenant_id,
            user.user_id,
            disconnected,
            "disconnect",
            "disabled",
            {"reason": payload["reason"], "remote_actions_enabled": False},
        )
        await repositories.record_runtime_event(
            "sunat.connection_disabled",
            "ok",
            {"connection_id": disconnected["id"], "reason": payload["reason"]},
            user.tenant_id,
        )
        await append_audit_event_async(
            "sunat.connection_disabled",
            user.username,
            {"connection_id": disconnected["id"], "reason": payload["reason"]},
            risk="medium",
            tenant_id=user.tenant_id,
        )
        return {"connection": disconnected, "status": "DISABLED", "foundation_only": True}

    async def sync(self, user: CurrentUser, connection_id: str, payload: dict) -> dict:
        connection = await self.get_connection(user, connection_id)
        await identity_service.require_business_permission(user, "sunat:sync", workspace_id=connection["workspace_id"])
        await repositories.record_sunat_connection_event(
            user.tenant_id,
            user.user_id,
            connection,
            "sync_requested",
            "not_executed_foundation_only",
            {
                "sync_scope": payload.get("sync_scope") or [],
                "real_connector_enabled": False,
                "last_sync_at_changed": False,
            },
        )
        await repositories.record_runtime_event(
            "sunat.sync_blocked_foundation_only",
            "warning",
            {"connection_id": connection["id"], "real_connector_enabled": False},
            user.tenant_id,
        )
        await append_audit_event_async(
            "sunat.sync_not_executed",
            user.username,
            {
                "connection_id": connection["id"],
                "reason": "real_sunat_connector_not_configured",
                "last_sync_at_changed": False,
            },
            risk="low",
            tenant_id=user.tenant_id,
        )
        return {
            "connection": connection,
            "sync_status": "NOT_EXECUTED_FOUNDATION_ONLY",
            "foundation_only": True,
            "real_connector_enabled": False,
            "last_sync_at_changed": False,
        }

    def _normalize_permission(self, value: str) -> str:
        clean = unicodedata.normalize("NFKD", value or "")
        clean = "".join(char for char in clean if not unicodedata.combining(char))
        return " ".join(clean.lower().replace(">", " ").replace("/", " ").split())

    def _permission_type(self, permission_name: str) -> str:
        normalized = self._normalize_permission(permission_name)
        if any(keyword in normalized for keyword in ["consulta", "consulto", "reporte", "ficha", "validez", "captura", "acuse"]):
            return "consulta"
        if any(keyword in normalized for keyword in ["declaracion", "pago", "emitir", "modificar", "administracion", "recurso", "fraccionamiento"]):
            return "sensitive_action"
        return "unknown"

    def _is_sensitive_permission(self, permission_name: str) -> bool:
        permission_type = self._permission_type(permission_name)
        normalized = self._normalize_permission(permission_name)
        read_marker = any(keyword in normalized for keyword in ["consulta", "consulto", "reporte", "ficha", "validez", "captura", "acuse"])
        return permission_type == "sensitive_action" and not read_marker

    def _build_permission_checks(self, run_id: str, connector_permissions: list[dict], connector_status: str) -> list[dict]:
        available_by_name: dict[str, dict] = {}
        for permission in connector_permissions:
            key = self._normalize_permission(str(permission.get("permission_name") or ""))
            if key:
                available_by_name[key] = permission
        checks: list[dict] = []
        for permission_name in SUNAT_RECOMMENDED_QUERY_PERMISSIONS:
            key = self._normalize_permission(permission_name)
            available = available_by_name.get(key)
            is_available = bool(available)
            permission_type = self._permission_type(permission_name)
            can_read = is_available and permission_type == "consulta"
            status_value = "available_readonly" if can_read else ("missing" if connector_status == "CONNECTED_READ_ONLY" else "not_checked")
            checks.append(
                {
                    "permission_name": permission_name,
                    "permission_path": permission_name,
                    "permission_type": permission_type,
                    "is_available": is_available,
                    "is_recommended": True,
                    "is_sensitive": False,
                    "can_read": can_read,
                    "can_execute": False,
                    "status": status_value,
                    "source": "sunat_recommended_minimum",
                    "metadata": {
                        "run_id": run_id,
                        "missing_message": SUNAT_MISSING_PERMISSION_MESSAGE.format(permission=permission_name) if not is_available else "",
                    },
                }
            )
        recommended_keys = {self._normalize_permission(name) for name in SUNAT_RECOMMENDED_QUERY_PERMISSIONS}
        for permission in connector_permissions:
            permission_name = str(permission.get("permission_name") or "")
            key = self._normalize_permission(permission_name)
            if not key or key in recommended_keys:
                continue
            sensitive = bool(permission.get("is_sensitive")) or self._is_sensitive_permission(permission_name)
            checks.append(
                {
                    "permission_name": permission_name,
                    "permission_path": permission.get("permission_path") or permission_name,
                    "permission_type": permission.get("permission_type") or self._permission_type(permission_name),
                    "is_available": True,
                    "is_recommended": False,
                    "is_sensitive": sensitive,
                    "can_read": bool(permission.get("can_read")) and not sensitive,
                    "can_execute": False,
                    "status": "sensitive_detected_blocked" if sensitive else "additional_readonly_available",
                    "source": permission.get("source") or "sunat_menu",
                    "metadata": {
                        **(permission.get("metadata") or {}),
                        "run_id": run_id,
                        "sensitive_message": SUNAT_SENSITIVE_PERMISSION_MESSAGE if sensitive else "",
                    },
                }
            )
        return checks

    def _diagnosis_summary(self, run: dict, checks: list[dict], facts: list[dict], findings: list[dict], connector_status: str) -> dict:
        missing = [item for item in checks if item.get("is_recommended") and not item.get("is_available")]
        sensitive = [item for item in checks if item.get("is_sensitive")]
        available = [item for item in checks if item.get("is_available")]
        critical_or_high = [item for item in findings if item.get("severity") in {"critical", "high"}]
        return {
            "run_id": run["id"],
            "connector_status": connector_status,
            "executive_summary": "Lectura SUNAT de solo consulta registrada." if connector_status == "CONNECTED_READ_ONLY" else "SUNAT no completó una sesión read-only automática.",
            "permissions_total": len(checks),
            "permissions_available": len(available),
            "recommended_missing": len(missing),
            "sensitive_detected": len(sensitive),
            "facts_total": len(facts),
            "findings_total": len(findings),
            "critical_or_high_findings": len(critical_or_high),
            "read_only": True,
            "remote_actions_enabled": False,
            "real_sunat_session": connector_status == "CONNECTED_READ_ONLY",
            "storage": sunat_storage_adapter.status(),
        }

    async def _active_context_for_query(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> tuple[dict, dict]:
        company, workspace = await self._ensure_workspace_company(user, empresa_id, workspace_id)
        await identity_service.require_business_permission(user, "sunat:read", workspace_id=workspace_id)
        return company, workspace

    async def readonly_run(self, user: CurrentUser, payload: dict) -> dict:
        company, workspace = await self._ensure_workspace_company(user, payload["empresa_id"], payload["workspace_id"])
        await identity_service.require_business_permission(user, "sunat:sync", workspace_id=workspace["id"])
        await subscription_service.ensure_active_commercial_subscription(user.tenant_id, user.plan)
        credential = await repositories.get_sunat_credential_secret_for_user(user.tenant_id, user.user_id, workspace["id"], company["id"])
        if credential is None or credential.get("status") == "DISCONNECTED":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "sunat_credential_not_found"})
        if not credential.get("sunat_username_encrypted") or not credential.get("sunat_password_encrypted"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "sunat_credential_not_active"})
        if credential["ruc"] != company["ruc"]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "ruc_company_mismatch"})

        vault = self._vault()
        try:
            username = vault.decrypt(credential["sunat_username_encrypted"])
            password = vault.decrypt(credential["sunat_password_encrypted"])
        except CredentialVaultError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": "credential_vault_decrypt_failed"}) from exc

        run = await repositories.start_sunat_diagnostic_run(user.tenant_id, user.user_id, company, workspace, company["ruc"])
        connector_result = await sunat_readonly_connector.run_readonly_session(ruc=company["ruc"], username=username, password=password)
        snapshots: list[dict] = []
        for snapshot in connector_result.snapshots:
            stored = await sunat_storage_adapter.store_snapshot(user.tenant_id, company["id"], workspace["id"], company["ruc"], run["id"], snapshot)
            if stored is not None:
                snapshots.append(stored)

        checks_payload = self._build_permission_checks(run["id"], connector_result.available_permissions, connector_result.status)
        checks = await repositories.record_sunat_permission_checks(user.tenant_id, company["id"], workspace["id"], company["ruc"], run["id"], checks_payload)
        facts_payload = []
        for fact in connector_result.normalized_facts:
            facts_payload.append(
                {
                    **fact,
                    "source_snapshot_id": snapshots[0]["id"] if snapshots else None,
                }
            )
        if not facts_payload:
            facts_payload.append(
                {
                    "fact_type": "connector",
                    "fact_key": "run_status",
                    "fact_value": {"status": connector_result.status, "reason": connector_result.reason},
                    "confidence": 100,
                    "status": "blocked" if connector_result.status != "CONNECTED_READ_ONLY" else "normalized",
                    "source_snapshot_id": snapshots[0]["id"] if snapshots else None,
                }
            )
        facts = await repositories.record_sunat_normalized_facts(user.tenant_id, company["id"], workspace["id"], company["ruc"], run["id"], facts_payload)
        findings_payload = list(connector_result.findings)
        for check in checks_payload:
            if check["is_recommended"] and check["status"] == "missing":
                findings_payload.append(
                    {
                        "severity": "medium",
                        "category": "permissions",
                        "title": "Permiso SUNAT recomendado faltante",
                        "message": SUNAT_MISSING_PERMISSION_MESSAGE.format(permission=check["permission_name"]),
                        "source": "sunat_permission_discovery",
                        "status": "open",
                        "metadata": {"permission_name": check["permission_name"]},
                    }
                )
            if check.get("is_sensitive"):
                findings_payload.append(
                    {
                        "severity": "info",
                        "category": "sensitive_permission",
                        "title": "Permiso sensible detectado",
                        "message": SUNAT_SENSITIVE_PERMISSION_MESSAGE,
                        "source": "sunat_permission_discovery",
                        "status": "blocked",
                        "metadata": {"permission_name": check["permission_name"]},
                    }
                )
        findings = await repositories.record_sunat_findings(user.tenant_id, company["id"], workspace["id"], company["ruc"], run["id"], findings_payload)
        summary = self._diagnosis_summary(run, checks, facts, findings, connector_result.status)
        completed = await repositories.complete_sunat_diagnostic_run(
            run["id"],
            user.tenant_id,
            status="completed" if connector_result.status == "CONNECTED_READ_ONLY" else "blocked",
            connector_status=connector_result.status,
            real_sunat_session=connector_result.real_sunat_session,
            summary=summary,
            metadata={
                **connector_result.metadata,
                "reason": connector_result.reason,
                "captcha_required": connector_result.captcha_required,
                "storage": sunat_storage_adapter.status(),
            },
        )
        await repositories.update_sunat_readonly_status(
            user.tenant_id,
            user.user_id,
            workspace["id"],
            company["id"],
            credential_status="CONNECTED_READ_ONLY" if connector_result.real_sunat_session else "ERROR",
            connection_status="CONNECTED" if connector_result.real_sunat_session else "ERROR",
            last_error=None if connector_result.real_sunat_session else connector_result.reason,
            validated=connector_result.real_sunat_session,
        )
        event_connection = await repositories.list_sunat_connections(user.tenant_id, user.user_id, workspace["id"], company["id"])
        connection = event_connection[0] if event_connection else {"id": run["id"], "empresa_id": company["id"], "workspace_id": workspace["id"]}
        await repositories.record_sunat_connection_event(
            user.tenant_id,
            user.user_id,
            connection,
            "readonly_run",
            "connected_readonly" if connector_result.real_sunat_session else "blocked_readonly",
            {
                "run_id": run["id"],
                "connector_status": connector_result.status,
                "read_only": True,
                "remote_actions_enabled": False,
                "real_sunat_session": connector_result.real_sunat_session,
                "password_logged": False,
            },
        )
        await append_audit_event_async(
            "sunat.readonly_run",
            user.username,
            {
                "run_id": run["id"],
                "empresa_id": company["id"],
                "workspace_id": workspace["id"],
                "ruc": company["ruc"],
                "connector_status": connector_result.status,
                "real_sunat_session": connector_result.real_sunat_session,
                "read_only": True,
                "remote_actions_enabled": False,
                "password_logged": False,
            },
            risk="high" if not connector_result.real_sunat_session else "medium",
            tenant_id=user.tenant_id,
        )
        return {
            "run": completed or run,
            "connector": {
                "status": connector_result.status,
                "reason": connector_result.reason,
                "real_connector_enabled": connector_result.real_connector_enabled,
                "real_sunat_session": connector_result.real_sunat_session,
                "read_only": True,
                "remote_actions_enabled": False,
                "captcha_required": connector_result.captcha_required,
            },
            "permissions": checks,
            "snapshots": snapshots,
            "facts": facts,
            "findings": findings,
            "summary": summary,
            "actions_blocked": [
                "declaraciones",
                "pagos",
                "emisión de comprobantes",
                "modificación de RUC",
                "cambio de clave",
                "administración de usuarios",
                "fraccionamientos",
                "recursos",
                "acciones irreversibles",
            ],
        }

    async def readonly_refresh(self, user: CurrentUser, payload: dict) -> dict:
        return await self.readonly_run(user, payload)

    async def readonly_status(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> dict:
        await self._active_context_for_query(user, workspace_id, empresa_id)
        latest = await repositories.latest_sunat_diagnostic_run(user.tenant_id, workspace_id, empresa_id)
        credential = await repositories.get_sunat_credential_for_user(user.tenant_id, user.user_id, workspace_id, empresa_id)
        return {
            "flags": self.readonly_flags(),
            "storage": sunat_storage_adapter.status(),
            "credential": credential,
            "latest_run": latest,
            "can_start_new_read": bool(credential and credential.get("status") != "DISCONNECTED"),
            "read_only": True,
            "remote_actions_enabled": False,
        }

    async def readonly_permissions(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> dict:
        await self._active_context_for_query(user, workspace_id, empresa_id)
        latest = await repositories.latest_sunat_diagnostic_run(user.tenant_id, workspace_id, empresa_id)
        checks = await repositories.list_sunat_permission_checks(user.tenant_id, workspace_id, empresa_id)
        return {
            "run": latest,
            "recommended_permissions": SUNAT_RECOMMENDED_QUERY_PERMISSIONS,
            "permissions": checks,
            "missing": [item for item in checks if item.get("is_recommended") and not item.get("is_available")],
            "additional": [item for item in checks if item.get("is_available") and not item.get("is_recommended") and not item.get("is_sensitive")],
            "sensitive": [item for item in checks if item.get("is_sensitive")],
            "missing_permission_message": SUNAT_MISSING_PERMISSION_MESSAGE,
            "sensitive_permission_message": SUNAT_SENSITIVE_PERMISSION_MESSAGE,
        }

    async def readonly_diagnosis(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> dict:
        await self._active_context_for_query(user, workspace_id, empresa_id)
        latest = await repositories.latest_sunat_diagnostic_run(user.tenant_id, workspace_id, empresa_id)
        facts = await repositories.list_sunat_normalized_facts(user.tenant_id, workspace_id, empresa_id)
        findings = await repositories.list_sunat_findings(user.tenant_id, workspace_id, empresa_id)
        snapshots = await repositories.list_sunat_raw_snapshots(user.tenant_id, workspace_id, empresa_id)
        return {
            "run": latest,
            "summary": (latest or {}).get("summary") or {},
            "facts": facts,
            "findings": findings,
            "snapshots": snapshots,
            "prioritized_findings": findings,
            "read_only": True,
            "remote_actions_enabled": False,
        }

    async def readonly_findings(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> dict:
        await self._active_context_for_query(user, workspace_id, empresa_id)
        return {
            "findings": await repositories.list_sunat_findings(user.tenant_id, workspace_id, empresa_id),
            "risk_order": ["critical", "high", "medium", "low", "info"],
        }

    async def readonly_history(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> dict:
        await self._active_context_for_query(user, workspace_id, empresa_id)
        return {
            "runs": await repositories.list_sunat_diagnostic_runs(user.tenant_id, workspace_id, empresa_id),
            "retention": "historical_data_retained_until_voluntary_disconnect_or_policy_change",
            "new_reads_blocked_when_subscription_pending": True,
        }


sunat_service = SunatService()
