from __future__ import annotations


class SunatApiConnectorError(RuntimeError):
    def __init__(self, code: str, message: str, *, status_code: int | None = None, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict:
        return {"code": self.code, "message": str(self), "status_code": self.status_code, "details": self.details}


API_CREDENTIALS_MISSING = "API_CREDENTIALS_MISSING"
SOL_CREDENTIALS_MISSING = "SOL_CREDENTIALS_MISSING"
API_NOT_AUTHORIZED = "API_NOT_AUTHORIZED"
API_NOT_AVAILABLE = "API_NOT_AVAILABLE"
API_REQUIRES_SCOPE = "API_REQUIRES_SCOPE"
ONLY_SOL_WEB = "ONLY_SOL_WEB"
BLOCKED_BY_CAPTCHA = "BLOCKED_BY_CAPTCHA"
OFFICIAL_ENDPOINT_FAILED = "OFFICIAL_ENDPOINT_FAILED"
TEST_DATA_REQUIRED = "TEST_DATA_REQUIRED"
