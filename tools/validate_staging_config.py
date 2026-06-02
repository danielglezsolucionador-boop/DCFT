from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv


REQUIRED = {
    "DCFT_APP_ENV",
    "DCFT_ADMIN_PASSWORD",
    "DCFT_JWT_SECRET",
    "DCFT_FRONTEND_ORIGIN",
    "DCFT_CORS_ORIGINS",
    "DCFT_DATABASE_URL",
    "DCFT_DATABASE_SSL",
    "DCFT_DB_AUTO_MIGRATE",
    "VITE_DCFT_API_URL",
}


def is_true(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def safe_env(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        return "missing"
    if any(key in name for key in {"PASSWORD", "SECRET", "DATABASE_URL"}):
        return "set"
    return value


def add(checks: list[dict], name: str, ok: bool, detail: str) -> None:
    checks.append({"check": name, "ok": ok, "detail": detail})


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate DCFT cloud environment without printing secrets.")
    parser.add_argument("--env-file", default=".env.staging", help="Optional staging env file to load before validation.")
    parser.add_argument("--mode", choices=["staging", "production"], default="staging", help="Environment mode to validate.")
    args = parser.parse_args()

    env_file = Path(args.env_file)
    if env_file.exists():
        load_dotenv(env_file, override=True)

    checks: list[dict] = []
    missing = sorted(name for name in REQUIRED if not os.getenv(name))
    add(checks, "required_env_present", not missing, ",".join(missing) if missing else "all required variables present")

    app_env = os.getenv("DCFT_APP_ENV", "")
    database_url = os.getenv("DCFT_DATABASE_URL", "")
    cors_origins = [origin.strip() for origin in os.getenv("DCFT_CORS_ORIGINS", "").split(",") if origin.strip()]
    frontend_origin = os.getenv("DCFT_FRONTEND_ORIGIN", "")
    vite_api_url = os.getenv("VITE_DCFT_API_URL", "")
    jwt_secret = os.getenv("DCFT_JWT_SECRET", "")
    admin_password = os.getenv("DCFT_ADMIN_PASSWORD", "")

    add(checks, f"environment_is_{args.mode}", app_env == args.mode, f"DCFT_APP_ENV={app_env or 'missing'}")
    add(checks, "postgresql_database", database_url.startswith("postgresql"), f"database_url={safe_env('DCFT_DATABASE_URL')}")
    add(checks, "database_ssl_enabled", is_true(os.getenv("DCFT_DATABASE_SSL", "")), f"DCFT_DATABASE_SSL={os.getenv('DCFT_DATABASE_SSL', 'missing')}")
    add(checks, "auto_migrate_explicit", os.getenv("DCFT_DB_AUTO_MIGRATE", "") in {"true", "false"}, f"DCFT_DB_AUTO_MIGRATE={os.getenv('DCFT_DB_AUTO_MIGRATE', 'missing')}")
    add(checks, "debug_disabled", not is_true(os.getenv("DCFT_DEBUG", "false")), f"DCFT_DEBUG={os.getenv('DCFT_DEBUG', 'missing')}")
    add(checks, "jwt_secret_strong_shape", len(jwt_secret) >= 32 and "change" not in jwt_secret.lower() and "<" not in jwt_secret, "set" if jwt_secret else "missing")
    add(checks, "admin_password_strong_shape", len(admin_password) >= 14 and "change" not in admin_password.lower() and "<" not in admin_password, "set" if admin_password else "missing")
    add(checks, "cors_https_only", bool(cors_origins) and "*" not in cors_origins and all(origin.startswith("https://") for origin in cors_origins), ",".join(cors_origins) or "missing")
    add(checks, "frontend_https", frontend_origin.startswith("https://"), frontend_origin or "missing")
    add(checks, "frontend_points_to_https_backend", vite_api_url.startswith("https://"), vite_api_url or "missing")
    if args.mode == "production":
        add(checks, "auto_migrate_disabled_for_production", os.getenv("DCFT_DB_AUTO_MIGRATE", "") == "false", f"DCFT_DB_AUTO_MIGRATE={os.getenv('DCFT_DB_AUTO_MIGRATE', 'missing')}")
    add(checks, "external_providers_disabled", os.getenv("DCFT_AI_PROVIDER_ENABLED", "false") == "false" and os.getenv("DCFT_OCR_ENABLED", "false") == "false", "ai/ocr must remain disabled until explicit provider approval")

    ok = all(item["ok"] for item in checks)
    report = {
        "status": "ok" if ok else "blocked",
        "mode": args.mode,
        "env_file_loaded": str(env_file) if env_file.exists() else None,
        "checks": checks,
        "safe_summary": {name: safe_env(name) for name in sorted(REQUIRED)},
    }
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
