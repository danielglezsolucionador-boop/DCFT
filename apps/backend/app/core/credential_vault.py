from __future__ import annotations

from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class CredentialVaultError(RuntimeError):
    pass


class CredentialVaultNotConfigured(CredentialVaultError):
    pass


class CredentialVaultInvalidKey(CredentialVaultError):
    pass


@dataclass(frozen=True)
class CredentialVault:
    key: str

    @classmethod
    def from_settings(cls) -> "CredentialVault":
        key = settings.credential_encryption_key.strip()
        if not key:
            raise CredentialVaultNotConfigured("credential encryption key missing")
        try:
            Fernet(key.encode("utf-8"))
        except Exception as exc:
            raise CredentialVaultInvalidKey("credential encryption key invalid") from exc
        return cls(key=key)

    def _fernet(self) -> Fernet:
        return Fernet(self.key.encode("utf-8"))

    def encrypt(self, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise CredentialVaultError("credential value is empty")
        return self._fernet().encrypt(clean.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet().decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise CredentialVaultError("credential value cannot be decrypted") from exc


def credential_vault_status() -> dict:
    key = settings.credential_encryption_key.strip()
    if not key:
        return {"configured": False, "valid": False, "reason": "credential_encryption_key_missing"}
    try:
        Fernet(key.encode("utf-8"))
    except Exception:
        return {"configured": True, "valid": False, "reason": "credential_encryption_key_invalid"}
    return {"configured": True, "valid": True, "reason": "credential_encryption_ready"}


def mask_identifier(value: str, *, visible_prefix: int = 2, visible_suffix: int = 2) -> str:
    clean = value.strip()
    if not clean:
        return ""
    if len(clean) <= visible_prefix + visible_suffix:
        return "*" * len(clean)
    return f"{clean[:visible_prefix]}{'*' * (len(clean) - visible_prefix - visible_suffix)}{clean[-visible_suffix:]}"
