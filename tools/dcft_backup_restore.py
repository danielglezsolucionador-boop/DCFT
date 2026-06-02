from __future__ import annotations

import argparse
import asyncio
import base64
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import asyncpg
import httpx
from sqlalchemy import MetaData, insert, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = Path("D:/AIC-REPORTS/DCFT/ETAPA_A/BACKUPS")
SKIP_DATA_TABLES = {"alembic_version"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return {"__dcft_type": "datetime", "value": value.isoformat()}
    if isinstance(value, date):
        return {"__dcft_type": "date", "value": value.isoformat()}
    if isinstance(value, bytes):
        return {"__dcft_type": "bytes", "value": base64.b64encode(value).decode("ascii")}
    if isinstance(value, Decimal):
        return {"__dcft_type": "decimal", "value": str(value)}
    return value


def deserialize_value(value: Any) -> Any:
    if not isinstance(value, dict) or "__dcft_type" not in value:
        return value
    value_type = value.get("__dcft_type")
    raw = value.get("value")
    if value_type == "datetime":
        return datetime.fromisoformat(raw)
    if value_type == "date":
        return date.fromisoformat(raw)
    if value_type == "bytes":
        return base64.b64decode(raw.encode("ascii"))
    if value_type == "decimal":
        return Decimal(raw)
    return raw


def safe_url_summary(database_url: str) -> dict:
    url = make_url(database_url)
    return {
        "driver": url.drivername,
        "host_configured": bool(url.host),
        "port_configured": bool(url.port),
        "database": url.database,
        "username_configured": bool(url.username),
        "password_configured": bool(url.password),
    }


def target_database_url(source_url: str, target_database: str) -> str:
    url = make_url(source_url)
    return str(url.set(database=target_database))


def asyncpg_connection_kwargs(database_url: str, database: str | None = None) -> dict:
    url = make_url(database_url)
    kwargs = {
        "user": url.username,
        "password": url.password,
        "host": url.host or "127.0.0.1",
        "port": url.port or 5432,
        "database": database or url.database,
    }
    if os.getenv("DCFT_DATABASE_SSL", "").strip().lower() in {"1", "true", "yes", "on"}:
        kwargs["ssl"] = True
    return kwargs


def quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


async def source_database_url() -> str:
    sys.path.insert(0, str(ROOT / "apps" / "backend"))
    from app.core.config import settings

    if settings.database_backend != "postgresql":
        raise RuntimeError("postgresql_database_required_for_a7_backup")
    return settings.effective_database_url


async def reflect_metadata(database_url: str, schema: str | None = None) -> MetaData:
    engine = create_async_engine(database_url, pool_pre_ping=True, future=True)
    metadata = MetaData(schema=schema)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(lambda sync_connection: metadata.reflect(sync_connection, schema=schema))
    finally:
        await engine.dispose()
    return metadata


async def table_counts(database_url: str, schema: str | None = None) -> dict[str, int]:
    metadata = await reflect_metadata(database_url, schema)
    engine = create_async_engine(database_url, pool_pre_ping=True, future=True)
    counts: dict[str, int] = {}
    try:
        async with engine.connect() as connection:
            for table in metadata.sorted_tables:
                result = await connection.execute(select(text("count(*)")).select_from(table))
                counts[table.name] = int(result.scalar_one())
    finally:
        await engine.dispose()
    return counts


async def alembic_revision(database_url: str, schema: str | None = None) -> str | None:
    metadata = await reflect_metadata(database_url, schema)
    table_key = f"{schema}.alembic_version" if schema else "alembic_version"
    if table_key not in metadata.tables:
        return None
    engine = create_async_engine(database_url, pool_pre_ping=True, future=True)
    try:
        async with engine.connect() as connection:
            prefix = f"{quote_ident(schema)}." if schema else ""
            result = await connection.execute(text(f"select version_num from {prefix}alembic_version limit 1"))
            value = result.scalar_one_or_none()
            return str(value) if value else None
    finally:
        await engine.dispose()


async def backup_database(database_url: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = output_dir / f"dcft-postgres-backup-{timestamp}.json"
    metadata = await reflect_metadata(database_url)
    engine = create_async_engine(database_url, pool_pre_ping=True, future=True)
    tables: list[dict] = []
    try:
        async with engine.connect() as connection:
            for table in metadata.sorted_tables:
                if table.name in SKIP_DATA_TABLES:
                    continue
                result = await connection.execute(select(table))
                rows = [
                    {key: serialize_value(value) for key, value in dict(row).items()}
                    for row in result.mappings().all()
                ]
                tables.append({"name": table.name, "rows": rows, "row_count": len(rows)})
    finally:
        await engine.dispose()
    payload = {
        "format": "dcft-postgresql-logical-backup-v1",
        "generated_at": utc_now(),
        "source": safe_url_summary(database_url),
        "alembic_revision": await alembic_revision(database_url),
        "sensitive_data": True,
        "secrets_exposed": False,
        "tables": tables,
    }
    backup_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return backup_path


async def create_restore_database(source_url: str, target_database: str) -> None:
    source = make_url(source_url)
    maintenance_database = "postgres" if source.database != "postgres" else "template1"
    connection = await asyncpg.connect(**asyncpg_connection_kwargs(source_url, maintenance_database))
    try:
        await connection.execute("select pg_terminate_backend(pid) from pg_stat_activity where datname = $1", target_database)
        await connection.execute(f"drop database if exists {quote_ident(target_database)}")
        await connection.execute(f"create database {quote_ident(target_database)} template template0")
    finally:
        await connection.close()


async def create_restore_schema(source_url: str, schema: str) -> None:
    connection = await asyncpg.connect(**asyncpg_connection_kwargs(source_url))
    try:
        await connection.execute(f"drop schema if exists {quote_ident(schema)} cascade")
        await connection.execute(f"create schema {quote_ident(schema)}")
    finally:
        await connection.close()


async def drop_restore_schema(source_url: str, schema: str) -> None:
    connection = await asyncpg.connect(**asyncpg_connection_kwargs(source_url))
    try:
        await connection.execute(f"drop schema if exists {quote_ident(schema)} cascade")
    finally:
        await connection.close()


def run_alembic_upgrade(database_url: str, schema: str | None = None) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "apps" / "backend")
    env["DCFT_DATABASE_URL"] = database_url
    env["DCFT_DB_AUTO_MIGRATE"] = "false"
    env.setdefault("DCFT_APP_ENV", "local")
    env.setdefault("DCFT_JWT_SECRET", "restore-validation-jwt-secret-32-plus")
    env.setdefault("DCFT_ADMIN_PASSWORD", "")
    if schema:
        env["DCFT_DATABASE_SCHEMA"] = schema
    completed = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"alembic_restore_migration_failed:{completed.stderr[-500:]}")


async def restore_database(backup_path: Path, target_url: str, schema: str | None = None) -> dict:
    payload = json.loads(backup_path.read_text(encoding="utf-8"))
    metadata = await reflect_metadata(target_url, schema)
    tables_by_name = metadata.tables
    engine = create_async_engine(target_url, pool_pre_ping=True, future=True)
    restored: dict[str, int] = {}
    try:
        async with engine.begin() as connection:
            for table_payload in payload["tables"]:
                table_name = table_payload["name"]
                table_key = f"{schema}.{table_name}" if schema else table_name
                if table_key not in tables_by_name:
                    raise RuntimeError(f"restore_table_missing:{table_name}")
                rows = [
                    {key: deserialize_value(value) for key, value in row.items()}
                    for row in table_payload["rows"]
                ]
                if rows:
                    await connection.execute(insert(tables_by_name[table_key]), rows)
                restored[table_name] = len(rows)
    finally:
        await engine.dispose()
    return restored


async def validate_backend_health(database_url: str, port: int, schema: str | None = None) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "apps" / "backend")
    env["DCFT_DATABASE_URL"] = database_url
    env["DCFT_DB_AUTO_MIGRATE"] = "false"
    env["DCFT_APP_ENV"] = "local"
    env["DCFT_ADMIN_PASSWORD"] = ""
    env["DCFT_JWT_SECRET"] = "restore-validation-jwt-secret-32-plus"
    env["DCFT_BASE_DIR"] = str(Path(os.getenv("TEMP", str(ROOT / ".dcft" / "tmp"))) / f"dcft-restore-health-{port}")
    if schema:
        env["DCFT_DATABASE_SCHEMA"] = schema
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        deadline = time.time() + 45
        last_error = ""
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}", timeout=5.0) as client:
            while time.time() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"backend_restore_health_process_exited:{process.returncode}")
                try:
                    response = await client.get("/health")
                    if response.status_code == 200:
                        body = response.json()
                        return {
                            "status": "pass",
                            "http_status": response.status_code,
                            "health_status": body.get("status"),
                            "database_status": (body.get("database") or {}).get("status"),
                            "production_ready": body.get("production_ready"),
                        }
                except Exception as exc:
                    last_error = exc.__class__.__name__
                await asyncio.sleep(1)
        raise RuntimeError(f"backend_restore_health_timeout:{last_error}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


async def e2e(output_dir: Path, keep_restore: bool, port: int) -> dict:
    source_url = await source_database_url()
    source_database = make_url(source_url).database or "dcft"
    restore_database_name = f"{source_database}_restore_validation_{int(time.time())}"
    restore_schema_name = f"dcft_restore_validation_{int(time.time())}"
    target_url = target_database_url(source_url, restore_database_name)

    source_counts_before = await table_counts(source_url)
    backup_path = await backup_database(source_url, output_dir)
    restore_mode = "database"
    restore_target = restore_database_name
    restore_schema: str | None = None
    try:
        await create_restore_database(source_url, restore_database_name)
    except Exception:
        restore_mode = "schema"
        restore_target = restore_schema_name
        restore_schema = restore_schema_name
        target_url = source_url
        await create_restore_schema(source_url, restore_schema_name)
    run_alembic_upgrade(target_url, schema=restore_schema)
    restored_counts = await restore_database(backup_path, target_url, schema=restore_schema)
    target_counts = await table_counts(target_url, schema=restore_schema)
    mismatches = {
        table: {"source": count, "target": target_counts.get(table)}
        for table, count in source_counts_before.items()
        if table not in SKIP_DATA_TABLES and target_counts.get(table) != count
    }
    backend_health = await validate_backend_health(target_url, port, schema=restore_schema)
    if not keep_restore:
        if restore_mode == "database":
            source = make_url(source_url)
            maintenance_database = "postgres" if source.database != "postgres" else "template1"
            connection = await asyncpg.connect(**asyncpg_connection_kwargs(source_url, maintenance_database))
            try:
                await connection.execute("select pg_terminate_backend(pid) from pg_stat_activity where datname = $1", restore_database_name)
                await connection.execute(f"drop database if exists {quote_ident(restore_database_name)}")
            finally:
                await connection.close()
        else:
            await drop_restore_schema(source_url, restore_schema_name)

    status = "pass" if not mismatches and backend_health["status"] == "pass" else "fail"
    return {
        "status": status,
        "generated_at": utc_now(),
        "backup_path": str(backup_path),
        "backup_sha256": sha256_file(backup_path),
        "backup_size_bytes": backup_path.stat().st_size,
        "source": safe_url_summary(source_url),
        "restore_mode": restore_mode,
        "restore_target": restore_target if keep_restore else "dropped_after_validation",
        "source_table_count": len(source_counts_before),
        "restored_table_count": len(restored_counts),
        "row_count_mismatches": mismatches,
        "backend_health_post_restore": backend_health,
        "restore_kept": keep_restore,
        "secrets_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="DCFT PostgreSQL backup/restore validation without exposing secrets.")
    parser.add_argument("command", choices=["e2e"], help="Operation to run.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--drop-restore", action="store_true", help="Drop restore validation database after checks.")
    parser.add_argument("--port", type=int, default=8291, help="Temporary backend health validation port.")
    args = parser.parse_args()

    try:
        result = asyncio.run(e2e(Path(args.output_dir), keep_restore=not args.drop_restore, port=args.port))
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "pass" else 1
    except Exception as exc:
        print(json.dumps({"status": "fail", "error": exc.__class__.__name__, "detail": str(exc)[-500:], "secrets_exposed": False}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
