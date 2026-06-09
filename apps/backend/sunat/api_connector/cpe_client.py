from __future__ import annotations

import httpx

from .credentials import SunatApiCredentials
from .errors import OFFICIAL_ENDPOINT_FAILED, TEST_DATA_REQUIRED, SunatApiConnectorError
from .token_client import SunatApiToken, SunatTokenClient


CPE_VALIDATE_URL = "https://api.sunat.gob.pe/v1/contribuyente/contribuyentes/{ruc}/validarcomprobante"


class SunatCpeClient:
    def __init__(self, token_client: SunatTokenClient | None = None, *, timeout_seconds: float = 30.0) -> None:
        self.token_client = token_client or SunatTokenClient(timeout_seconds=timeout_seconds)
        self.timeout_seconds = timeout_seconds

    async def test_auth(self, credentials: SunatApiCredentials) -> dict:
        token = await self.token_client.cpe_token(credentials)
        return {"status": "TOKEN_OK", "service": "cpe", "token": token.public_metadata()}

    async def validate_comprobante(self, credentials: SunatApiCredentials, payload: dict) -> dict:
        required = ["numRuc", "codComp", "numeroSerie", "numero", "fechaEmision"]
        missing = [key for key in required if not payload.get(key)]
        if missing:
            raise SunatApiConnectorError(TEST_DATA_REQUIRED, "Faltan datos de comprobante para probar CPE.", details={"missing": missing})
        token = await self.token_client.cpe_token(credentials)
        return await self.validate_comprobante_with_token(credentials.ruc, token, payload)

    async def validate_comprobante_with_token(self, ruc: str, token: SunatApiToken, payload: dict) -> dict:
        url = CPE_VALIDATE_URL.format(ruc=ruc)
        headers = {"Authorization": token.authorization_header(), "Content-Type": "application/json", "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
            except httpx.HTTPError as exc:
                raise SunatApiConnectorError(OFFICIAL_ENDPOINT_FAILED, "SUNAT CPE no respondió.", details={"url": url}) from exc
        if response.status_code >= 400:
            raise SunatApiConnectorError(OFFICIAL_ENDPOINT_FAILED, "SUNAT CPE devolvió error.", status_code=response.status_code)
        return {"status": "CPE_OK", "service": "cpe", "raw": response.json(), "token": token.public_metadata()}
