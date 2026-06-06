from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SunatReadOnlyConnectorResult:
    status: str
    real_connector_enabled: bool
    real_sunat_session: bool
    read_only: bool
    remote_actions_enabled: bool
    reason: str


class SunatReadOnlyConnector:
    real_connector_enabled = False
    read_only = True
    remote_actions_enabled = False

    def _blocked(self, reason: str = "real_sunat_connector_not_configured") -> SunatReadOnlyConnectorResult:
        return SunatReadOnlyConnectorResult(
            status="NOT_EXECUTED_FOUNDATION_ONLY",
            real_connector_enabled=False,
            real_sunat_session=False,
            read_only=True,
            remote_actions_enabled=False,
            reason=reason,
        )

    async def validate_credentials(self, *, ruc: str, username: str, password: str) -> SunatReadOnlyConnectorResult:
        _ = (ruc, username, password)
        return self._blocked()

    async def get_ruc_status(self, *, ruc: str) -> SunatReadOnlyConnectorResult:
        _ = ruc
        return self._blocked()

    async def get_tax_obligations(self, *, ruc: str) -> SunatReadOnlyConnectorResult:
        _ = ruc
        return self._blocked()

    async def get_basic_alerts(self, *, ruc: str) -> SunatReadOnlyConnectorResult:
        _ = ruc
        return self._blocked()

    async def disconnect(self, *, ruc: str) -> SunatReadOnlyConnectorResult:
        _ = ruc
        return self._blocked("local_disconnect_only")


sunat_readonly_connector = SunatReadOnlyConnector()
