from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.audit import append_audit_event_async
from app.core.credential_vault import CredentialVault, CredentialVaultError, mask_identifier
from app.db import repositories
from app.schemas.common import CurrentUser
from app.services.identity_service import identity_service
from app.services.subscription_service import subscription_service
from sunat.api_connector import (
    SunatApiCredentials,
    SunatApiDiagnostics,
    SunatApiDiscovery,
    SunatCpeClient,
    SunatSirePurchasesClient,
    SunatSireSalesClient,
    SunatSolCredentials,
)
from sunat.api_connector.errors import (
    API_CREDENTIALS_MISSING,
    SOL_CREDENTIALS_MISSING,
    TEST_DATA_REQUIRED,
    SunatApiConnectorError,
)
from sunat.api_connector.normalization import (
    normalize_cpe_response,
    normalize_sire_purchases_response,
    normalize_sire_sales_response,
)


API_CREDENTIAL_CONSENT_TEXT = (
    "Autorizo a DCFT a guardar cifradas mis Credenciales de API SUNAT y usarlas, junto con mi usuario "
    "secundario SUNAT autorizado cuando el servicio lo requiera, para consultar servicios oficiales como "
    "CPE y SIRE. DCFT no realizará declaraciones, pagos, emisiones, modificaciones ni acciones irreversibles."
)


class SunatApiService:
    def __init__(self) -> None:
        self.discovery_client = SunatApiDiscovery()
        self.diagnostics = SunatApiDiagnostics()
        self.cpe_client = SunatCpeClient()
        self.sire_sales_client = SunatSireSalesClient()
        self.sire_purchases_client = SunatSirePurchasesClient()

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

    def _vault(self) -> CredentialVault:
        try:
            return CredentialVault.from_settings()
        except CredentialVaultError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": "credential_vault_unavailable"}) from exc

    async def _api_credentials(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> tuple[dict, SunatApiCredentials]:
        row = await repositories.get_sunat_api_credential_secret_for_user(user.tenant_id, user.user_id, workspace_id, empresa_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": API_CREDENTIALS_MISSING})
        vault = self._vault()
        try:
            client_id = vault.decrypt(row["client_id_encrypted"])
            client_secret = vault.decrypt(row["client_secret_encrypted"])
        except CredentialVaultError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": "credential_decryption_failed"}) from exc
        return row, SunatApiCredentials(ruc=row["ruc"], client_id=client_id, client_secret=client_secret)

    async def _sol_credentials(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> SunatSolCredentials | None:
        row = await repositories.get_sunat_credential_secret_for_user(user.tenant_id, user.user_id, workspace_id, empresa_id)
        if row is None or not row.get("sunat_username_encrypted") or not row.get("sunat_password_encrypted"):
            return None
        vault = self._vault()
        try:
            username = vault.decrypt(row["sunat_username_encrypted"])
            password = vault.decrypt(row["sunat_password_encrypted"])
        except CredentialVaultError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": "credential_decryption_failed"}) from exc
        return SunatSolCredentials(ruc=row["ruc"], username=username, password=password)

    def api_permission_guide(self) -> dict:
        return {
            "title": "Permiso para automatización API",
            "permission": "Credenciales de API SUNAT",
            "copy": "Credenciales de API SUNAT permite habilitar servicios oficiales para consultas automáticas. Actívalo solo si deseas que DCFT use APIs oficiales de SUNAT para automatizar consultas.",
            "warning": "Este permiso permite gestión de credenciales API. Solo actívalo si autorizas automatización mediante API.",
            "sensitive_actions_enabled": False,
            "read_only": True,
        }

    async def store_credentials(self, user: CurrentUser, payload: dict) -> dict:
        await self._ensure_workspace_company(user, payload["empresa_id"], payload["workspace_id"])
        await identity_service.require_business_permission(user, "sunat:connect", workspace_id=payload["workspace_id"])
        missing = [
            flag
            for flag in [
                "consent_accepted",
                "api_credentials_acknowledged",
                "official_api_acknowledged",
                "no_sensitive_actions_acknowledged",
            ]
            if not payload.get(flag)
        ]
        if missing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "explicit_sunat_api_consent_required", "missing": missing})
        vault = self._vault()
        client_id = payload["client_id"].strip()
        client_secret_value = payload["client_secret"]
        client_secret = client_secret_value.get_secret_value() if hasattr(client_secret_value, "get_secret_value") else str(client_secret_value)
        saved = await repositories.upsert_sunat_api_credential(
            user.tenant_id,
            user.user_id,
            payload,
            client_id_encrypted=vault.encrypt(client_id),
            client_secret_encrypted=vault.encrypt(client_secret),
            client_id_masked=mask_identifier(client_id, visible_prefix=4, visible_suffix=4),
        )
        await append_audit_event_async(
            tenant_id=user.tenant_id,
            event_type="sunat_api_credentials_stored",
            actor=user.user_id,
            risk="medium",
            payload={"empresa_id": payload["empresa_id"], "workspace_id": payload["workspace_id"], "read_only": True, "secret_echo": False},
        )
        return {"credential": saved, "consent_text": API_CREDENTIAL_CONSENT_TEXT, "secret_echo": False}

    async def status(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> dict:
        await identity_service.require_business_permission(user, "sunat:read", workspace_id=workspace_id)
        credential = await repositories.get_sunat_api_credential_for_user(user.tenant_id, user.user_id, workspace_id, empresa_id)
        sol_status = await repositories.get_sunat_credential_for_user(user.tenant_id, user.user_id, workspace_id, empresa_id)
        return {
            "api_configured": credential is not None,
            "sol_configured": bool(sol_status and sol_status.get("id") and sol_status.get("status") != "DISCONNECTED"),
            "credential": credential,
            "status": credential["status"] if credential else "API_CREDENTIALS_MISSING",
            "read_only": True,
            "sensitive_actions_enabled": False,
            "consent_text": API_CREDENTIAL_CONSENT_TEXT,
            "permission_guide": self.api_permission_guide(),
        }

    async def discovery(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> dict:
        status_body = await self.status(user, workspace_id, empresa_id)
        return self.discovery_client.catalog(
            api_configured=status_body["api_configured"],
            sol_configured=status_body["sol_configured"],
            service_status=(status_body.get("credential") or {}).get("services") or {},
        )

    async def test(self, user: CurrentUser, payload: dict) -> dict:
        await self._ensure_workspace_company(user, payload["empresa_id"], payload["workspace_id"])
        await identity_service.require_business_permission(user, "sunat:connect", workspace_id=payload["workspace_id"])
        await subscription_service.ensure_active_commercial_subscription(user.tenant_id, fallback_plan=user.plan)
        row, api_credentials = await self._api_credentials(user, payload["workspace_id"], payload["empresa_id"])
        services = dict(row.get("services") or {})
        results: list[dict] = []
        try:
            cpe = await self.cpe_client.test_auth(api_credentials)
            services["cpe"] = {"status": "TOKEN_OK", "last_tested_at": datetime.now(timezone.utc).isoformat()}
            results.append(cpe)
            token_hash = cpe["token"]["token_hash"]
            token_expires_at = datetime.fromisoformat(cpe["token"]["expires_at"])
            status_label = "TOKEN_OK"
            error = None
        except SunatApiConnectorError as exc:
            services["cpe"] = {"status": exc.code, "last_error": str(exc)}
            token_hash = None
            token_expires_at = None
            status_label = exc.code
            error = str(exc)
            results.append({"service": "cpe", "status": exc.code, "error": exc.to_dict()})
        updated = await repositories.update_sunat_api_credential_status(
            user.tenant_id,
            row["id"],
            status=status_label,
            services=services,
            token_hash=token_hash,
            token_expires_at=token_expires_at,
            last_test_status=status_label,
            last_error=error,
            validated=error is None,
        )
        return {"credential": updated, "results": results, "secret_echo": False}

    async def cpe_test(self, user: CurrentUser, payload: dict) -> dict:
        company, workspace = await self._ensure_workspace_company(user, payload["empresa_id"], payload["workspace_id"])
        await identity_service.require_business_permission(user, "sunat:connect", workspace_id=payload["workspace_id"])
        await subscription_service.ensure_active_commercial_subscription(user.tenant_id, fallback_plan=user.plan)
        row, api_credentials = await self._api_credentials(user, payload["workspace_id"], payload["empresa_id"])
        run = await repositories.start_sunat_diagnostic_run(user.tenant_id, user.user_id, company, workspace, company["ruc"])
        cpe_payload = {
            "numRuc": payload["numRuc"],
            "codComp": payload["codComp"],
            "numeroSerie": payload["numeroSerie"],
            "numero": payload["numero"],
            "fechaEmision": payload["fechaEmision"],
        }
        if payload.get("monto") is not None:
            cpe_payload["monto"] = payload["monto"]
        try:
            result = await self.cpe_client.validate_comprobante(api_credentials, cpe_payload)
            snapshot = await repositories.record_sunat_raw_snapshot(user.tenant_id, company["id"], workspace["id"], company["ruc"], run["id"], source="sunat_api_cpe", snapshot_type="cpe_validity", content=result["raw"], metadata={"service": "cpe"})
            facts = normalize_cpe_response(result)
            for fact in facts:
                fact["source_snapshot_id"] = snapshot["id"]
            normalized = await repositories.record_sunat_normalized_facts(user.tenant_id, company["id"], workspace["id"], company["ruc"], run["id"], facts)
            findings = await repositories.record_sunat_findings(user.tenant_id, company["id"], workspace["id"], company["ruc"], run["id"], self.diagnostics.findings_from_results([result]))
            completed = await repositories.complete_sunat_diagnostic_run(
                run["id"],
                user.tenant_id,
                status="completed",
                connector_status="CPE_OK",
                real_sunat_session=True,
                summary={"service": "cpe", "snapshots": 1, "facts": len(normalized), "findings": len(findings)},
                metadata={"source": "official_sunat_api", "token_hash": result["token"]["token_hash"]},
            )
            await repositories.update_sunat_api_credential_status(user.tenant_id, row["id"], status="CPE_OK", services={**(row.get("services") or {}), "cpe": {"status": "CPE_OK"}}, token_hash=result["token"]["token_hash"], token_expires_at=datetime.fromisoformat(result["token"]["expires_at"]), last_test_status="CPE_OK", validated=True)
            return {"run": completed, "snapshot": snapshot, "facts": normalized, "findings": findings, "secret_echo": False}
        except SunatApiConnectorError as exc:
            completed = await repositories.complete_sunat_diagnostic_run(
                run["id"],
                user.tenant_id,
                status="blocked" if exc.code == TEST_DATA_REQUIRED else "error",
                connector_status=exc.code,
                real_sunat_session=False,
                summary={"service": "cpe", "error": exc.code},
                metadata={"source": "official_sunat_api", "error": exc.to_dict()},
            )
            return {"run": completed, "error": exc.to_dict(), "secret_echo": False}

    async def sync_sire(self, user: CurrentUser, payload: dict, *, service: str) -> dict:
        company, workspace = await self._ensure_workspace_company(user, payload["empresa_id"], payload["workspace_id"])
        await identity_service.require_business_permission(user, "sunat:connect", workspace_id=payload["workspace_id"])
        await subscription_service.ensure_active_commercial_subscription(user.tenant_id, fallback_plan=user.plan)
        row, api_credentials = await self._api_credentials(user, payload["workspace_id"], payload["empresa_id"])
        sol_credentials = await self._sol_credentials(user, payload["workspace_id"], payload["empresa_id"])
        if sol_credentials is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": SOL_CREDENTIALS_MISSING})
        period = payload["period"]
        run = await repositories.start_sunat_diagnostic_run(user.tenant_id, user.user_id, company, workspace, company["ruc"])
        try:
            if service == "sire_sales":
                result = await self.sire_sales_client.sync_period(api_credentials, sol_credentials, period)
                source = "sunat_api_sire_sales"
                snapshot_type = "sire_sales"
                facts = normalize_sire_sales_response(result)
            else:
                result = await self.sire_purchases_client.sync_period(api_credentials, sol_credentials, period)
                source = "sunat_api_sire_purchases"
                snapshot_type = "sire_purchases"
                facts = normalize_sire_purchases_response(result)
            raw_content = {key: value for key, value in result.items() if key != "token"}
            snapshot = await repositories.record_sunat_raw_snapshot(user.tenant_id, company["id"], workspace["id"], company["ruc"], run["id"], source=source, snapshot_type=snapshot_type, content=raw_content, metadata={"service": service, "period": period})
            for fact in facts:
                fact["source_snapshot_id"] = snapshot["id"]
            normalized = await repositories.record_sunat_normalized_facts(user.tenant_id, company["id"], workspace["id"], company["ruc"], run["id"], facts)
            findings = await repositories.record_sunat_findings(user.tenant_id, company["id"], workspace["id"], company["ruc"], run["id"], self.diagnostics.findings_from_results([result]))
            completed = await repositories.complete_sunat_diagnostic_run(
                run["id"],
                user.tenant_id,
                status="completed",
                connector_status=result["status"],
                real_sunat_session=True,
                summary={"service": service, "period": period, "snapshots": 1, "facts": len(normalized), "findings": len(findings)},
                metadata={"source": "official_sunat_api", "token_hash": result["token"]["token_hash"]},
            )
            services = {**(row.get("services") or {}), service: {"status": result["status"], "period": period, "last_synced_at": datetime.now(timezone.utc).isoformat()}}
            await repositories.update_sunat_api_credential_status(user.tenant_id, row["id"], status=result["status"], services=services, token_hash=result["token"]["token_hash"], token_expires_at=datetime.fromisoformat(result["token"]["expires_at"]), last_test_status=result["status"], validated=True)
            return {"run": completed, "snapshot": snapshot, "facts": normalized, "findings": findings, "secret_echo": False}
        except SunatApiConnectorError as exc:
            completed = await repositories.complete_sunat_diagnostic_run(
                run["id"],
                user.tenant_id,
                status="error",
                connector_status=exc.code,
                real_sunat_session=False,
                summary={"service": service, "period": period, "error": exc.code},
                metadata={"source": "official_sunat_api", "error": exc.to_dict()},
            )
            return {"run": completed, "error": exc.to_dict(), "secret_echo": False}

    async def sync_status(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> dict:
        latest = await repositories.latest_sunat_diagnostic_run(user.tenant_id, workspace_id, empresa_id)
        return {"latest_run": latest, "read_only": True, "sensitive_actions_enabled": False}

    async def diagnosis(self, user: CurrentUser, workspace_id: str, empresa_id: str) -> dict:
        latest = await repositories.latest_sunat_diagnostic_run(user.tenant_id, workspace_id, empresa_id)
        findings = await repositories.list_sunat_findings(user.tenant_id, workspace_id, empresa_id, latest["id"] if latest else None)
        facts = await repositories.list_sunat_normalized_facts(user.tenant_id, workspace_id, empresa_id, latest["id"] if latest else None)
        return {"run": latest, "facts": facts, "prioritized_findings": findings, "read_only": True}


sunat_api_service = SunatApiService()
