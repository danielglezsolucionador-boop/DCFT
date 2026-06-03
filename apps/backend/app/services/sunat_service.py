from __future__ import annotations

from fastapi import HTTPException, status

from app.core.audit import append_audit_event_async
from app.db import repositories
from app.schemas.common import CurrentUser
from app.services.identity_service import identity_service


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
        "no_almacena_clave_sol",
        "solo_prepara_estado_consentimiento_y_auditoria",
    ],
}

CONSENT_SCOPE = {
    "connection_type": "CLAVE_SOL_AUXILIAR",
    "read_only": True,
    "remote_actions_enabled": False,
    "consultable": CONSULTABLE_DATA,
    "not_consultable": NON_CONSULTABLE_DATA,
}


class SunatService:
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
        return AUXILIARY_ACCESS_REQUIREMENTS

    def data_classification(self) -> dict:
        return {
            "CONSULTABLE": CONSULTABLE_DATA,
            "NO_CONSULTABLE": NON_CONSULTABLE_DATA,
            "read_only": True,
            "remote_actions_enabled": False,
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
        return {
            "connection": connection,
            "status": connection["estado"] if connection else "NOT_CONNECTED",
            "foundation_only": True,
            "real_connector_enabled": False,
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
            "foundation_pending_real_connector",
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


sunat_service = SunatService()
