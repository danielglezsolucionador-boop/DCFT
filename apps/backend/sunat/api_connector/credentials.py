from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SunatApiCredentials:
    ruc: str
    client_id: str
    client_secret: str


@dataclass(frozen=True)
class SunatSolCredentials:
    ruc: str
    username: str
    password: str

    @property
    def sire_username(self) -> str:
        return f"{self.ruc}{self.username}"
