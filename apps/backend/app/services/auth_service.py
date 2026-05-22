from __future__ import annotations

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.core.audit import append_audit_event


class AuthService:
    def __init__(self) -> None:
        self._tenant_id = "local-demo"
        self._username = settings.admin_username
        self._password_hash = hash_password(settings.admin_password, salt=b"dcft-local-salt")
        self._scopes = ["admin", "governance:approve", "workflow:run", "documents:ingest"]
        self._plan = "business_premium"

    def authenticate(self, username: str, password: str) -> str | None:
        if username != self._username or not verify_password(password, self._password_hash):
            append_audit_event("auth.login_failed", username, {"username": username}, risk="medium")
            return None
        append_audit_event("auth.login_success", username, {"username": username}, tenant_id=self._tenant_id)
        return create_access_token(username, self._scopes, self._tenant_id, self._plan)

    def public_user(self) -> dict:
        return {"username": self._username, "tenant_id": self._tenant_id, "role": "admin", "plan": self._plan}


auth_service = AuthService()