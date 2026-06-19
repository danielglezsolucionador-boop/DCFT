from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv


load_dotenv()

LOCAL_ENV_NAMES = {"local", "dev", "development", "test"}
STAGING_ENV_NAMES = {"staging", "stage"}
PRODUCTION_ENV_NAMES = {"prod", "production"}
MIN_JWT_SECRET_LENGTH = 32
MIN_ADMIN_PASSWORD_LENGTH = 14
INSECURE_SECRET_MARKERS = {"<", ">", "change", "changeme", "default", "example", "password"}
SCHEMA_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
POSTGRES_SCHEMES = {"postgres", "postgresql", "postgresql+asyncpg"}
ASYNC_PG_UNSUPPORTED_QUERY_KEYS = {"sslmode", "channel_binding"}


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _database_url_from_env() -> str:
    return os.getenv("DCFT_DATABASE_URL") or os.getenv("DATABASE_URL") or ""


def _database_url_source() -> str:
    if os.getenv("DCFT_DATABASE_URL"):
        return "DCFT_DATABASE_URL"
    if os.getenv("DATABASE_URL"):
        return "DATABASE_URL"
    return "missing"


def _normalize_postgres_url(database_url: str) -> str:
    parsed = urlsplit(database_url)
    if parsed.scheme not in POSTGRES_SCHEMES:
        return database_url
    scheme = "postgresql+asyncpg"
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in ASYNC_PG_UNSUPPORTED_QUERY_KEYS
    ]
    return urlunsplit((scheme, parsed.netloc, parsed.path, urlencode(query_pairs), parsed.fragment))


def _sslmode(database_url: str) -> str:
    parsed = urlsplit(database_url)
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key == "sslmode":
            return value.lower()
    return ""


def _secret_shape_warning(value: str, *, min_length: int, label: str) -> str | None:
    if not value.strip():
        return f"{label}_missing"
    normalized = value.strip().lower()
    if len(value.strip()) < min_length or any(marker in normalized for marker in INSECURE_SECRET_MARKERS):
        return f"{label}_weak_shape"
    return None


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _ai_provider_enabled_from_env() -> bool:
    explicit = os.getenv("DCFT_AI_PROVIDER_ENABLED") or os.getenv("AI_PROVIDER_ENABLED")
    if explicit is not None:
        return explicit.strip().lower() in {"1", "true", "yes", "on"}
    if _env("DCFT_AI_API_KEY", "").strip():
        return True
    provider = _env("DCFT_AI_PROVIDER", _env("AI_PROVIDER", "openrouter")).strip().lower()
    if provider == "openrouter":
        return bool(_env("DCFT_OPENROUTER_API_KEY", _env("OPENROUTER_API_KEY", "")).strip())
    if provider == "openai":
        return bool(_env("DCFT_OPENAI_API_KEY", _env("OPENAI_API_KEY", "")).strip())
    if provider == "anthropic":
        return bool(_env("DCFT_ANTHROPIC_API_KEY", _env("ANTHROPIC_API_KEY", "")).strip())
    if provider == "gemini":
        return bool(_env("DCFT_GEMINI_API_KEY", _env("GEMINI_API_KEY", "")).strip())
    return False


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _default_base_dir() -> str:
    if os.getenv("VERCEL"):
        return "/tmp/dcft"
    return str(Path(__file__).resolve().parents[4])


@dataclass(frozen=True)
class Settings:
    app_name: str = field(default_factory=lambda: _env("DCFT_APP_NAME", "dcft-backend"))
    app_version: str = field(default_factory=lambda: _env("DCFT_APP_VERSION", "0.1.0"))
    app_env: str = field(default_factory=lambda: _env("DCFT_APP_ENV", "local"))
    debug: bool = field(default_factory=lambda: _bool_env("DCFT_DEBUG", True))
    log_level: str = field(default_factory=lambda: _env("DCFT_LOG_LEVEL", "INFO"))
    frontend_origin: str = field(default_factory=lambda: _env("DCFT_FRONTEND_ORIGIN", "http://localhost:5174"))
    app_public_url: str = field(default_factory=lambda: _env("APP_PUBLIC_URL", _env("DCFT_FRONTEND_ORIGIN", "http://localhost:5174")))
    cors_origins_raw: str = field(default_factory=lambda: _env("DCFT_CORS_ORIGINS", "http://localhost:5174,http://127.0.0.1:5174"))
    jwt_secret: str = field(default_factory=lambda: _env("DCFT_JWT_SECRET", ""))
    jwt_previous_secret: str = field(default_factory=lambda: _env("DCFT_JWT_PREVIOUS_SECRET", ""))
    jwt_algorithm: str = field(default_factory=lambda: _env("DCFT_JWT_ALGORITHM", "HS256"))
    jwt_exp_minutes: int = field(default_factory=lambda: _int_env("DCFT_JWT_EXP_MINUTES", 60))
    admin_username: str = field(default_factory=lambda: _env("DCFT_ADMIN_USERNAME", "dcft_admin"))
    admin_password: str = field(default_factory=lambda: _env("DCFT_ADMIN_PASSWORD", ""))
    admin_role: str = field(default_factory=lambda: _env("DCFT_ADMIN_ROLE", "ceo"))
    admin_plan: str = field(default_factory=lambda: _env("DCFT_ADMIN_PLAN", "internal"))
    credential_encryption_key: str = field(default_factory=lambda: _env("DCFT_CREDENTIAL_ENCRYPTION_KEY", ""))
    database_url: str = field(default_factory=_database_url_from_env)
    database_url_source: str = field(default_factory=_database_url_source)
    database_ssl_raw: str = field(default_factory=lambda: _env("DCFT_DATABASE_SSL", ""))
    database_ssl: bool = field(default_factory=lambda: _bool_env("DCFT_DATABASE_SSL", False))
    database_pool_size: int = field(default_factory=lambda: _int_env("DCFT_DATABASE_POOL_SIZE", 10))
    database_max_overflow: int = field(default_factory=lambda: _int_env("DCFT_DATABASE_MAX_OVERFLOW", 20))
    database_pool_timeout: int = field(default_factory=lambda: _int_env("DCFT_DATABASE_POOL_TIMEOUT", 30))
    database_schema: str = field(default_factory=lambda: _env("DCFT_DATABASE_SCHEMA", ""))
    observability_persist_concurrency: int = field(default_factory=lambda: _int_env("DCFT_OBSERVABILITY_PERSIST_CONCURRENCY", 20))
    db_auto_migrate: bool = field(default_factory=lambda: _bool_env("DCFT_DB_AUTO_MIGRATE", False))
    ai_provider_enabled: bool = field(default_factory=_ai_provider_enabled_from_env)
    ai_provider: str = field(default_factory=lambda: _env("DCFT_AI_PROVIDER", _env("AI_PROVIDER", "openrouter")))
    ai_api_key: str = field(default_factory=lambda: _env("DCFT_AI_API_KEY", ""))
    ai_model: str = field(default_factory=lambda: _env("DCFT_AI_MODEL", _env("AI_MODEL", _env("AI_DEFAULT_MODEL", ""))))
    ai_request_timeout_seconds: int = field(default_factory=lambda: _int_env("DCFT_AI_REQUEST_TIMEOUT_SECONDS", 20))
    openrouter_api_key: str = field(default_factory=lambda: _env("DCFT_OPENROUTER_API_KEY", _env("OPENROUTER_API_KEY", "")))
    openrouter_model: str = field(default_factory=lambda: _env("DCFT_OPENROUTER_MODEL", _env("OPENROUTER_MODEL", "openai/gpt-4o-mini")))
    openrouter_base_url: str = field(default_factory=lambda: _env("DCFT_OPENROUTER_BASE_URL", _env("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")))
    openrouter_referer: str = field(default_factory=lambda: _env("DCFT_OPENROUTER_REFERER", _env("APP_PUBLIC_URL", "https://dcft-frontend.vercel.app")))
    openrouter_title: str = field(default_factory=lambda: _env("DCFT_OPENROUTER_TITLE", "DCFT Student Doctor"))
    openai_api_key: str = field(default_factory=lambda: _env("DCFT_OPENAI_API_KEY", _env("OPENAI_API_KEY", "")))
    openai_model: str = field(default_factory=lambda: _env("DCFT_OPENAI_MODEL", _env("OPENAI_MODEL", "gpt-4o-mini")))
    anthropic_api_key: str = field(default_factory=lambda: _env("DCFT_ANTHROPIC_API_KEY", _env("ANTHROPIC_API_KEY", "")))
    anthropic_model: str = field(default_factory=lambda: _env("DCFT_ANTHROPIC_MODEL", _env("ANTHROPIC_MODEL", "claude-sonnet-4-5")))
    gemini_api_key: str = field(default_factory=lambda: _env("DCFT_GEMINI_API_KEY", _env("GEMINI_API_KEY", "")))
    gemini_model: str = field(default_factory=lambda: _env("DCFT_GEMINI_MODEL", _env("GEMINI_MODEL", "gemini-2.5-flash")))
    ocr_enabled: bool = field(default_factory=lambda: _bool_env("DCFT_OCR_ENABLED", False))
    email_provider: str = field(default_factory=lambda: _env("EMAIL_PROVIDER", ""))
    email_from: str = field(default_factory=lambda: _env("EMAIL_FROM", ""))
    email_api_key: str = field(default_factory=lambda: _env("EMAIL_API_KEY", ""))
    smtp_host: str = field(default_factory=lambda: _env("SMTP_HOST", ""))
    smtp_port: int = field(default_factory=lambda: _int_env("SMTP_PORT", 587))
    smtp_user: str = field(default_factory=lambda: _env("SMTP_USER", ""))
    smtp_password: str = field(default_factory=lambda: _env("SMTP_PASSWORD", ""))
    payment_provider: str = field(default_factory=lambda: _env("PAYMENT_PROVIDER", ""))
    payment_public_key: str = field(default_factory=lambda: _env("PAYMENT_PUBLIC_KEY", ""))
    payment_secret_key: str = field(default_factory=lambda: _env("PAYMENT_SECRET_KEY", ""))
    payment_webhook_secret: str = field(default_factory=lambda: _env("PAYMENT_WEBHOOK_SECRET", ""))
    mercadopago_access_token: str = field(default_factory=lambda: _env("MERCADOPAGO_ACCESS_TOKEN", ""))
    mercadopago_public_key: str = field(default_factory=lambda: _env("MERCADOPAGO_PUBLIC_KEY", ""))
    mercadopago_webhook_secret: str = field(default_factory=lambda: _env("MERCADOPAGO_WEBHOOK_SECRET", ""))
    sunat_readonly_enabled: bool = field(default_factory=lambda: _bool_env("SUNAT_READONLY_ENABLED", False))
    sunat_api_automation_enabled: bool = field(default_factory=lambda: _bool_env("SUNAT_API_AUTOMATION_ENABLED", True))
    sunat_allow_sensitive_actions: bool = field(default_factory=lambda: _bool_env("SUNAT_ALLOW_SENSITIVE_ACTIONS", False))
    sunat_store_raw_snapshots: bool = field(default_factory=lambda: _bool_env("SUNAT_STORE_RAW_SNAPSHOTS", True))
    sunat_storage_backend: str = field(default_factory=lambda: _env("SUNAT_STORAGE_BACKEND", "postgres"))
    sunat_external_datalake_enabled: bool = field(default_factory=lambda: _bool_env("SUNAT_EXTERNAL_DATALAKE_ENABLED", False))
    base_dir: Path = field(default_factory=lambda: Path(_env("DCFT_BASE_DIR", _default_base_dir())))
    vercel_env: str = field(default_factory=lambda: _env("VERCEL_ENV", ""))

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
    def is_staging(self) -> bool:
        return self.app_env.lower() in STAGING_ENV_NAMES

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in PRODUCTION_ENV_NAMES

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]
        if self.frontend_origin and self.frontend_origin not in origins:
            origins.append(self.frontend_origin)
        return origins

    @property
    def effective_database_url(self) -> str:
        if self.database_url.strip():
            return _normalize_postgres_url(self.database_url.strip())
        return f"sqlite+aiosqlite:///{self.state_dir / 'dcft_local.db'}"

    @property
    def database_backend(self) -> str:
        return "postgresql" if self.effective_database_url.startswith("postgresql") else "sqlite"

    @property
    def database_persistent(self) -> bool:
        return self.database_backend == "postgresql"

    @property
    def database_temporal(self) -> bool:
        return self.database_backend == "sqlite"

    @property
    def database_url_sslmode(self) -> str:
        return _sslmode(self.database_url.strip())

    @property
    def email_provider_missing(self) -> bool:
        provider = self.email_provider.strip().lower()
        if provider == "smtp":
            return not (self.smtp_host.strip() and self.email_from.strip())
        if provider == "resend":
            return not (self.email_api_key.strip() and self.email_from.strip())
        return True

    @property
    def payment_provider_missing(self) -> bool:
        provider = self.payment_provider.strip().lower()
        if provider == "mercadopago":
            return not (
                self.mercadopago_access_token.strip()
                and self.mercadopago_public_key.strip()
                and self.mercadopago_webhook_secret.strip()
                and self.app_public_url.strip()
            )
        if provider == "stripe":
            return not (
                self.payment_secret_key.strip()
                and self.payment_public_key.strip()
                and self.payment_webhook_secret.strip()
                and self.app_public_url.strip()
            )
        return True

    @property
    def payment_webhook_missing(self) -> bool:
        provider = self.payment_provider.strip().lower()
        if provider == "mercadopago":
            return not self.mercadopago_webhook_secret.strip()
        if provider == "stripe":
            return not self.payment_webhook_secret.strip()
        return False

    @property
    def database_ssl_enabled(self) -> bool:
        if self.database_url_sslmode in {"require", "verify-ca", "verify-full"}:
            return True
        if self.database_ssl_raw.strip():
            return self.database_ssl
        return self.database_backend == "postgresql" and not self.is_local

    @property
    def is_vercel_production(self) -> bool:
        return self.vercel_env.lower() == "production"

    @property
    def database_connect_args(self) -> dict:
        if self.database_backend == "sqlite":
            return {"check_same_thread": False}
        connect_args = {"ssl": True} if self.database_ssl_enabled else {"ssl": False}
        if self.database_schema.strip():
            connect_args["server_settings"] = {"search_path": self.database_schema.strip()}
        return connect_args

    @property
    def production_ready(self) -> bool:
        return (
            self.is_production
            and not self.security_warnings()
            and self.database_backend == "postgresql"
        )

    @property
    def bootstrap_admin_enabled(self) -> bool:
        return bool(self.admin_username.strip() and self.admin_password.strip())

    @property
    def staging_ready(self) -> bool:
        return (
            self.is_staging
            and not self.security_warnings()
            and self.database_backend == "postgresql"
        )

    def security_warnings(self) -> list[str]:
        warnings: list[str] = []
        non_local = not self.is_local
        jwt_warning = _secret_shape_warning(self.jwt_secret, min_length=MIN_JWT_SECRET_LENGTH, label="jwt_secret")
        if jwt_warning:
            warnings.append(jwt_warning)
        previous_jwt_warning = None
        if self.jwt_previous_secret.strip():
            previous_jwt_warning = _secret_shape_warning(
                self.jwt_previous_secret,
                min_length=MIN_JWT_SECRET_LENGTH,
                label="jwt_previous_secret",
            )
        if previous_jwt_warning:
            warnings.append(previous_jwt_warning)
        admin_warning = _secret_shape_warning(self.admin_password, min_length=MIN_ADMIN_PASSWORD_LENGTH, label="admin_password")
        if admin_warning:
            warnings.append(admin_warning)
        if self.admin_role.strip().lower() not in {"ceo", "admin"}:
            warnings.append("admin_role_not_internal")
        if self.admin_plan.strip().lower() != "internal":
            warnings.append("admin_plan_not_internal")
        if "*" in self.cors_origins:
            warnings.append("wildcard_cors_origin")
        if not self.database_url.strip():
            warnings.append("sqlite_local_fallback_active")
        if self.is_vercel_production and self.app_env.lower() in LOCAL_ENV_NAMES:
            warnings.append("vercel_production_app_env_local")
        if self.is_vercel_production and self.database_backend != "postgresql":
            warnings.append("vercel_production_requires_postgresql")
        if non_local and self.database_backend != "postgresql":
            warnings.append("non_local_requires_postgresql")
        if non_local and not self.database_ssl_enabled:
            warnings.append("non_local_database_ssl_disabled")
        if non_local and self.debug:
            warnings.append("non_local_debug_enabled")
        if non_local and any(not origin.startswith("https://") for origin in self.cors_origins):
            warnings.append("non_local_cors_origin_not_https")
        if self.database_schema.strip() and not SCHEMA_NAME_RE.match(self.database_schema.strip()):
            warnings.append("database_schema_invalid")
        if self.is_staging and self.ai_provider_enabled:
            warnings.append("staging_ai_provider_enabled_requires_cto_approval")
        if self.is_staging and self.ocr_enabled:
            warnings.append("staging_ocr_enabled_requires_cto_approval")
        return warnings

    def validate_runtime_safety(self) -> None:
        if self.is_local:
            return
        blockers = self.security_warnings()
        if blockers:
            raise RuntimeError(f"unsafe_non_local_configuration:{','.join(blockers)}")


settings = Settings()
