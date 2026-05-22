from __future__ import annotations

from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import os
import uuid

from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str, salt: bytes | None = None) -> str:
    actual_salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), actual_salt, 160_000)
    return f"pbkdf2_sha256$160000${base64.b64encode(actual_salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_access_token(subject: str, scopes: list[str], tenant_id: str, plan: str) -> str:
    issued_at = datetime.now(timezone.utc)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_exp_minutes)
    payload = {
        "sub": subject,
        "scopes": scopes,
        "tenant_id": tenant_id,
        "plan": plan,
        "iat": issued_at,
        "exp": expires_at,
        "jti": str(uuid.uuid4()),
        "kid": "current",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    secrets = [settings.jwt_secret]
    if settings.jwt_previous_secret.strip():
        secrets.append(settings.jwt_previous_secret.strip())
    last_error: JWTError | None = None
    for secret in secrets:
        try:
            return jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
        except JWTError as exc:
            last_error = exc
    try:
        raise last_error or JWTError("invalid_token")
    except JWTError as exc:
        raise ValueError("invalid_token") from exc
