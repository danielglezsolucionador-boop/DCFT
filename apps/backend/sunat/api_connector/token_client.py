from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib

import httpx

from .credentials import SunatApiCredentials, SunatSolCredentials
from .errors import API_NOT_AUTHORIZED, OFFICIAL_ENDPOINT_FAILED, SunatApiConnectorError


CPE_SCOPE = "https://api.sunat.gob.pe/v1/contribuyente/contribuyentes"
SIRE_SCOPE = "https://api-sire.sunat.gob.pe"
CPE_TOKEN_URL = "https://api-seguridad.sunat.gob.pe/v1/clientesextranet/{client_id}/oauth2/token/"
SIRE_TOKEN_URL = "https://api-seguridad.sunat.gob.pe/v1/clientessol/{client_id}/oauth2/token/"


@dataclass(frozen=True)
class SunatApiToken:
    access_token: str
    token_type: str
    expires_in: int
    scope: str
    obtained_at: datetime

    @property
    def expires_at(self) -> datetime:
        return self.obtained_at + timedelta(seconds=max(self.expires_in - 30, 0))

    @property
    def token_hash(self) -> str:
        return hashlib.sha256(self.access_token.encode("utf-8")).hexdigest()

    def authorization_header(self) -> str:
        return f"Bearer {self.access_token}"

    def public_metadata(self) -> dict:
        return {
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "expires_at": self.expires_at.isoformat(),
            "scope": self.scope,
            "token_hash": self.token_hash,
        }


class SunatTokenClient:
    def __init__(self, *, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def cpe_token(self, credentials: SunatApiCredentials) -> SunatApiToken:
        data = {
            "grant_type": "client_credentials",
            "scope": CPE_SCOPE,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
        }
        return await self._post_token(CPE_TOKEN_URL.format(client_id=credentials.client_id), data, CPE_SCOPE)

    async def sire_token(self, api_credentials: SunatApiCredentials, sol_credentials: SunatSolCredentials) -> SunatApiToken:
        data = {
            "grant_type": "password",
            "scope": SIRE_SCOPE,
            "client_id": api_credentials.client_id,
            "client_secret": api_credentials.client_secret,
            "username": sol_credentials.sire_username,
            "password": sol_credentials.password,
        }
        return await self._post_token(SIRE_TOKEN_URL.format(client_id=api_credentials.client_id), data, SIRE_SCOPE)

    async def _post_token(self, url: str, data: dict[str, str], scope: str) -> SunatApiToken:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            except httpx.HTTPError as exc:
                raise SunatApiConnectorError(OFFICIAL_ENDPOINT_FAILED, "SUNAT token endpoint no respondió.", details={"url": url}) from exc
        if response.status_code in {401, 403}:
            raise SunatApiConnectorError(API_NOT_AUTHORIZED, "SUNAT rechazó las credenciales API o el alcance solicitado.", status_code=response.status_code)
        if response.status_code >= 400:
            raise SunatApiConnectorError(OFFICIAL_ENDPOINT_FAILED, "SUNAT token endpoint devolvió error.", status_code=response.status_code)
        body = response.json()
        access_token = str(body.get("access_token") or "")
        if not access_token:
            raise SunatApiConnectorError(OFFICIAL_ENDPOINT_FAILED, "SUNAT no devolvió access_token.", status_code=response.status_code)
        return SunatApiToken(
            access_token=access_token,
            token_type=str(body.get("token_type") or "Bearer"),
            expires_in=int(body.get("expires_in") or 0),
            scope=scope,
            obtained_at=datetime.now(timezone.utc),
        )
