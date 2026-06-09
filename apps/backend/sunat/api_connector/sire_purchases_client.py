from __future__ import annotations

import httpx

from .credentials import SunatApiCredentials, SunatSolCredentials
from .errors import OFFICIAL_ENDPOINT_FAILED, SunatApiConnectorError
from .token_client import SunatApiToken, SunatTokenClient


SIRE_PURCHASES_SUMMARY_URL = (
    "https://api-sire.sunat.gob.pe/v1/contribuyente/migeigv/libros/rce/"
    "propuesta/web?periodoSeleccionado={period}&tipoInfo=FV0621"
)


class SunatSirePurchasesClient:
    def __init__(self, token_client: SunatTokenClient | None = None, *, timeout_seconds: float = 30.0) -> None:
        self.token_client = token_client or SunatTokenClient(timeout_seconds=timeout_seconds)
        self.timeout_seconds = timeout_seconds

    async def test_auth(self, api_credentials: SunatApiCredentials, sol_credentials: SunatSolCredentials) -> dict:
        token = await self.token_client.sire_token(api_credentials, sol_credentials)
        return {"status": "TOKEN_OK", "service": "sire_purchases", "token": token.public_metadata()}

    async def sync_period(self, api_credentials: SunatApiCredentials, sol_credentials: SunatSolCredentials, period: str) -> dict:
        token = await self.token_client.sire_token(api_credentials, sol_credentials)
        return await self.sync_period_with_token(period, token)

    async def sync_period_with_token(self, period: str, token: SunatApiToken) -> dict:
        url = SIRE_PURCHASES_SUMMARY_URL.format(period=period)
        headers = {"Authorization": token.authorization_header(), "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.get(url, headers=headers)
            except httpx.HTTPError as exc:
                raise SunatApiConnectorError(OFFICIAL_ENDPOINT_FAILED, "SUNAT SIRE Compras no respondió.", details={"url": url}) from exc
        if response.status_code >= 400:
            raise SunatApiConnectorError(OFFICIAL_ENDPOINT_FAILED, "SUNAT SIRE Compras devolvió error.", status_code=response.status_code)
        return {
            "status": "SIRE_PURCHASES_OK",
            "service": "sire_purchases",
            "period": period,
            "raw": response.json(),
            "token": token.public_metadata(),
        }
