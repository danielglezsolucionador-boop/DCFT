from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()

LOCAL_ENV_NAMES = {"local", "dev", "development", "test"}
DEFAULT_JWT_SECRET = "local-dcft-secret-change-before-prod"
DEFAULT_ADMIN_PASSWORD = "dcft_local_admin_change_me"


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@dataclass(frozen=True)
class Settings:
    app_name: str = field(default_factory=lambda: _env("DCFT_APP_NAME", "dcft-backend"))
    app_version: str = field(default_factory=lambda: _env("DCFT_APP_VERSION", "0.1.0"))
    app_env: str = field(default_factory=lambda: _env("DCFT_APP_ENV", "local"))
    debug: bool = field(default_factory=lambda: _bool_env("DCFT_DEBUG", True))
    log_level: str = field(default_factory=lambda: _env("DCFT_LOG_LEVEL", "INFO"))
    frontend_origin: str = field(default_factory=lambda: _env("DCFT_FRONTEND_ORIGIN", "http://localhost:5174"))
    cors_origins_raw: str = field(default_factory=lambda: _env("DCFT_CORS_ORIGINS", "http://localhost:5174,http://127.0.0.1:5174"))
    jwt_secret: str = field(default_factory=lambda: _env("DCFT_JWT_SECRET", DEFAULT_JWT_SECRET))
    jwt_algorithm: str = field(default_factory=lambda: _env("DCFT_JWT_ALGORITHM", "HS256"))
    jwt_exp_minutes: int = field(default_factory=lambda: _int_env("DCFT_JWT_EXP_MINUTES", 60))
    admin_username: str = field(default_factory=lambda: _env("DCFT_ADMIN_USERNAME", "dcft_admin"))
    admin_password: str = field(default_factory=lambda: _env("DCFT_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD))
    database_url: str = field(default_factory=lambda: _env("DCFT_DATABASE_URL", ""))
    database_ssl: bool = field(default_factory=lambda: _bool_env("DCFT_DATABASE_SSL", False))
    db_auto_migrate: bool = field(default_factory=lambda: _bool_env("DCFT_DB_AUTO_MIGRATE", False))
    ai_provider_enabled: bool = field(default_factory=lambda: _bool_env("DCFT_AI_PROVIDER_ENABLED", False))
    ocr_enabled: bool = field(default_factory=lambda: _bool_env("DCFT_OCR_ENABLED", False))
    base_dir: Path = field(default_factory=lambda: Path(_env("DCFT_BASE_DIR", str(Path(__file__).resolve().parents[4]))))

    @property
    def state_dir(self) -> Path:
        return self.base_dir / ".dcft" / "state"

    @property
    def audit_dir(self) -> Path:
        return self.base_dir / ".dcft" / "audit"

    @property
    def uploads_dir(self) -> Path:
        return self.base_dir / ".dcft" / "uploads"

    @property
    def outputs_dir(self) -> Path:
        return self.base_dir / ".dcft" / "outputs"

    @property
    def is_local(self) -> bool:
        return self.app_env.lower() in LOCAL_ENV_NAMES

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]
        if self.frontend_origin and self.frontend_origin not in origins:
            origins.append(self.frontend_origin)
        return origins

    @property
    def effective_database_url(self) -> str:
        if self.database_url.strip():
            return self.database_url.strip()
        return f"sqlite+aiosqlite:///{self.state_dir / 'dcft_local.db'}"

    @property
    def database_backend(self) -> str:
        return "postgresql" if self.effective_database_url.startswith("postgresql") else "sqlite"

    @property
    def database_connect_args(self) -> dict:
        if self.database_backend == "sqlite":
            return {"check_same_thread": False}
        return {} if self.database_ssl else {"ssl": False}

    @property
    def production_ready(self) -> bool:
        return (
            not self.is_local
            and self.jwt_secret != DEFAULT_JWT_SECRET
            and self.admin_password != DEFAULT_ADMIN_PASSWORD
            and bool(self.database_url.strip())
            and "*" not in self.cors_origins
        )

    def security_warnings(self) -> list[str]:
        warnings: list[str] = []
        if self.jwt_secret == DEFAULT_JWT_SECRET:
            warnings.append("default_jwt_secret_in_use")
        if self.admin_password == DEFAULT_ADMIN_PASSWORD:
            warnings.append("default_admin_password_in_use")
        if "*" in self.cors_origins:
            warnings.append("wildcard_cors_origin")
        if not self.database_url.strip():
            warnings.append("sqlite_local_fallback_active")
        return warnings

    def validate_runtime_safety(self) -> None:
        if self.is_local:
            return
        blockers = self.security_warnings()
        if blockers:
            raise RuntimeError(f"unsafe_non_local_configuration:{','.join(blockers)}")


settings = Settings()