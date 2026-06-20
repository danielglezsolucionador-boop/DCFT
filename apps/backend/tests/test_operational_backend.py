from __future__ import annotations

import os
import tempfile

os.environ["DCFT_BASE_DIR"] = tempfile.mkdtemp(prefix="dcft-tests-")
os.environ["DCFT_APP_ENV"] = "test"
os.environ["DCFT_DATABASE_URL"] = ""
os.environ["DCFT_DB_AUTO_MIGRATE"] = "true"
os.environ["DCFT_AI_PROVIDER_ENABLED"] = "false"
os.environ["DCFT_OCR_ENABLED"] = "false"
os.environ["DCFT_JWT_SECRET"] = "test-dcft-secret-change-before-prod"
os.environ["DCFT_ADMIN_PASSWORD"] = "test-admin-pass-strong-123"
os.environ["DCFT_CREDENTIAL_ENCRYPTION_KEY"] = "ZGNmdC1zdW5hdC12YXVsdC10ZXN0LWtleS0wMDAxISE="
os.environ["APP_PUBLIC_URL"] = "http://localhost:5174"

from datetime import datetime, timedelta, timezone
import asyncio
import hashlib
import hmac
import json
from pathlib import Path
import time
import uuid

from fastapi import HTTPException
from fastapi.testclient import TestClient
from jose import jwt
import pytest
from sqlalchemy import func, select

from app.core.audit import audit_hash
from app.core.config import Settings, settings
from app.core.security import hash_password, verify_password
from app.db import repositories
from app.db.bootstrap import bootstrap_local_identity
from app.db.models import (
    AuditEvent,
    Company,
    Subscription,
    SunatConnectionEvent,
    SunatApiCredential,
    SunatCredential,
    SunatDiagnosticRun,
    SunatFinding,
    SunatNormalizedFact,
    SunatPermissionCheck,
    SunatRawSnapshot,
    User,
    UserBusinessPlan,
)
from app.db.session import async_session
from app.main import app
from app.services.payment_service import payment_service
from app.services.student_doctor_service import QUOTA_EXCEEDED_MESSAGE, student_doctor_service
from app.services.subscription_service import subscription_service
from app.services.sunat_readonly_connector import SunatReadOnlyConnectorResult
from app.services.sunat_api_service import sunat_api_service


def test_ai_provider_auto_enabled_with_official_openrouter_vars(monkeypatch) -> None:
    monkeypatch.delenv("DCFT_AI_PROVIDER_ENABLED", raising=False)
    monkeypatch.delenv("AI_PROVIDER_ENABLED", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-openrouter-placeholder")
    monkeypatch.setenv("AI_MODEL", "unit-openrouter-model")

    config = Settings()

    assert config.ai_provider_enabled is True
    assert config.ai_provider == "openrouter"
    assert config.openrouter_api_key == "unit-openrouter-placeholder"
    assert config.ai_model == "unit-openrouter-model"


def test_ai_provider_explicit_false_keeps_doctor_disabled(monkeypatch) -> None:
    monkeypatch.setenv("DCFT_AI_PROVIDER_ENABLED", "false")
    monkeypatch.setenv("AI_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-openrouter-placeholder")

    assert Settings().ai_provider_enabled is False


def test_dcft_ai_api_key_enables_minimal_ai_provider(monkeypatch) -> None:
    monkeypatch.delenv("DCFT_AI_PROVIDER_ENABLED", raising=False)
    monkeypatch.delenv("AI_PROVIDER_ENABLED", raising=False)
    monkeypatch.setenv("DCFT_AI_PROVIDER", "openrouter")
    monkeypatch.setenv("DCFT_AI_API_KEY", "unit-generic-ai-key")

    config = Settings()

    assert config.ai_provider_enabled is True
    assert config.ai_provider == "openrouter"
    assert config.ai_api_key == "unit-generic-ai-key"


def test_mercadopago_provider_requires_official_variables(monkeypatch) -> None:
    monkeypatch.setenv("PAYMENT_PROVIDER", "mercadopago")
    monkeypatch.delenv("MERCADOPAGO_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("MERCADOPAGO_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("MERCADOPAGO_WEBHOOK_SECRET", raising=False)
    monkeypatch.setenv("APP_PUBLIC_URL", "https://dcft-frontend.vercel.app")

    missing = Settings()
    assert missing.payment_provider_missing is True

    monkeypatch.setenv("MERCADOPAGO_ACCESS_TOKEN", "unit-mercadopago-token")
    monkeypatch.setenv("MERCADOPAGO_PUBLIC_KEY", "unit-mercadopago-public")
    monkeypatch.setenv("MERCADOPAGO_WEBHOOK_SECRET", "unit-mercadopago-webhook")

    configured = Settings()
    assert configured.payment_provider_missing is False
    assert configured.payment_webhook_missing is False


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": "dcft_admin", "password": "test-admin-pass-strong-123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def forged_token(username: str = "dcft_admin", tenant_id: str = "tenant-forged") -> str:
    return jwt.encode(
        {
            "sub": username,
            "tenant_id": tenant_id,
            "scopes": ["admin"],
            "plan": "business_premium",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def test_admin_ceo_internal_access_has_premium_without_payment_and_ai_fallback() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)

        me = client.get("/auth/me", headers=headers)
        assert me.status_code == 200
        me_body = me.json()
        assert me_body["role"] == "ceo"
        assert me_body["plan"] == "internal"
        assert me_body["premium"] is True
        assert me_body["payment_required"] is False
        assert me_body["internal"] is True

        subscription = client.get("/subscriptions/status", headers=headers)
        assert subscription.status_code == 200
        subscription_body = subscription.json()
        assert subscription_body["plan_effective"] == "internal"
        assert subscription_body["premium"] is True
        assert subscription_body["payment_required"] is False
        assert subscription_body["payment_status"] == "not_required"

        checkout = client.post("/subscriptions/checkout", headers=headers, json={"plan": "premium", "billing_cycle": "monthly"})
        assert checkout.status_code == 403
        assert checkout.json()["detail"]["error"] == "internal_user_payment_not_required"

        dashboard = client.get("/dashboard/summary", headers=headers)
        assert dashboard.status_code == 200
        assert dashboard.json()["premium"] is True
        assert dashboard.json()["payment_required"] is False
        assert dashboard.json()["internal"] is True

        ai = client.post("/ai/tax/ask", headers=headers, json={"question": "Que es detraccion?"})
        assert ai.status_code == 200
        assert ai.json()["answer"] == "Proveedor IA no configurado"
        assert ai.json()["ai_provider_missing"] is True


def test_admin_bootstrap_reconciles_existing_username_without_duplicates() -> None:
    target_username = f"existing_admin_{uuid.uuid4().hex[:10]}"
    target_password = "replacement-admin-pass-123"
    original_username = settings.admin_username
    original_password = settings.admin_password
    original_role = settings.admin_role
    original_plan = settings.admin_plan

    async def exercise() -> None:
        target_user_id = f"user-{uuid.uuid4().hex}"
        async with async_session() as session:
            async with session.begin():
                session.add(
                    User(
                        id=target_user_id,
                        tenant_id="local-demo",
                        username=target_username,
                        password_hash=hash_password("old-admin-pass-123"),
                        role="operator",
                        plan="free",
                        active=True,
                        email_verified=True,
                    )
                )

        object.__setattr__(settings, "admin_username", target_username)
        object.__setattr__(settings, "admin_password", target_password)
        object.__setattr__(settings, "admin_role", "ceo")
        object.__setattr__(settings, "admin_plan", "internal")
        await bootstrap_local_identity()
        await bootstrap_local_identity()

        async with async_session() as session:
            users = (await session.execute(select(User).where(User.username == target_username))).scalars().all()
            assert len(users) == 1
            target = users[0]
            assert target.tenant_id == "local-demo"
            assert target.role == "ceo"
            assert target.plan == "internal"
            assert target.active is True
            assert target.email_verified is True
            assert verify_password(target_password, target.password_hash) is True
            assert await session.get(UserBusinessPlan, target.id) is not None

            canonical = await session.get(User, "user-local-admin")
            assert canonical is not None
            assert canonical.active is False
            assert canonical.role == "readonly"
            assert canonical.plan == "free"

        object.__setattr__(settings, "admin_username", original_username)
        object.__setattr__(settings, "admin_password", original_password)
        object.__setattr__(settings, "admin_role", original_role)
        object.__setattr__(settings, "admin_plan", original_plan)
        await bootstrap_local_identity()

        async with async_session() as session:
            async with session.begin():
                target = await session.get(User, target_user_id)
                target_plan = await session.get(UserBusinessPlan, target_user_id)
                if target_plan is not None:
                    await session.delete(target_plan)
                if target is not None:
                    await session.delete(target)

    try:
        asyncio.run(exercise())
    finally:
        object.__setattr__(settings, "admin_username", original_username)
        object.__setattr__(settings, "admin_password", original_password)
        object.__setattr__(settings, "admin_role", original_role)
        object.__setattr__(settings, "admin_plan", original_plan)


async def create_test_user(username: str, role: str, password: str = "operator-pass") -> None:
    async with async_session() as session:
        async with session.begin():
            session.add(
                User(
                    id=f"user-{username}",
                    tenant_id="local-demo",
                    username=username,
                    password_hash=hash_password(password, salt=f"salt-{username}".encode()),
                    role=role,
                    plan="business_basic",
                    active=True,
                    email_verified=True,
                )
            )


def verified_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    verified = asyncio.run(repositories.mark_user_email_verified(username))
    assert verified is not None
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_verified_student_headers(client: TestClient, unique: str) -> tuple[dict[str, str], str]:
    username = f"student_doctor_{unique}@example.com"
    password = "student-doctor-pass-123"
    created = client.post(
        "/onboarding/tenants",
        json={
            "tenant_name": f"Student Doctor {unique}",
            "admin_username": username,
            "admin_password": password,
            "plan": "student",
            "account_type": "student",
        },
    )
    assert created.status_code == 200
    return verified_headers(client, username, password), username


def stripe_signature(raw_body: bytes, secret: str) -> str:
    timestamp = str(int(time.time()))
    signature = hmac.new(secret.encode("utf-8"), f"{timestamp}.".encode("utf-8") + raw_body, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def mercadopago_signature(data_id: str, request_id: str, secret: str) -> str:
    timestamp = str(int(time.time() * 1000))
    manifest = f"id:{data_id};request-id:{request_id};ts:{timestamp};"
    signature = hmac.new(secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"ts={timestamp},v1={signature}"


async def insert_historical_audit_fork(tenant_id: str) -> None:
    base = datetime(2026, 6, 6, 0, 0, tzinfo=timezone.utc)
    root_id = f"root-{tenant_id}"
    child_a_id = f"child-a-{tenant_id}"
    child_b_id = f"child-b-{tenant_id}"
    root_hash = audit_hash(
        event_id=root_id,
        timestamp=base.isoformat(),
        request_id=None,
        tenant_id=tenant_id,
        event_type="test.root",
        actor="tester",
        risk="low",
        payload={"case": "historical_fork"},
        previous_hash=None,
    )
    child_a_hash = audit_hash(
        event_id=child_a_id,
        timestamp=(base + timedelta(seconds=1)).isoformat(),
        request_id=None,
        tenant_id=tenant_id,
        event_type="test.child_a",
        actor="tester",
        risk="low",
        payload={"branch": "a"},
        previous_hash=root_hash,
    )
    child_b_hash = audit_hash(
        event_id=child_b_id,
        timestamp=(base + timedelta(seconds=2)).isoformat(),
        request_id=None,
        tenant_id=tenant_id,
        event_type="test.child_b",
        actor="tester",
        risk="low",
        payload={"branch": "b"},
        previous_hash=root_hash,
    )
    async with async_session() as session:
        async with session.begin():
            session.add_all(
                [
                    AuditEvent(
                        id=root_id,
                        tenant_id=tenant_id,
                        event_type="test.root",
                        actor="tester",
                        risk="low",
                        payload={"case": "historical_fork"},
                        previous_hash=None,
                        event_hash=root_hash,
                        created_at=base,
                    ),
                    AuditEvent(
                        id=child_a_id,
                        tenant_id=tenant_id,
                        event_type="test.child_a",
                        actor="tester",
                        risk="low",
                        payload={"branch": "a"},
                        previous_hash=root_hash,
                        event_hash=child_a_hash,
                        created_at=base + timedelta(seconds=1),
                    ),
                    AuditEvent(
                        id=child_b_id,
                        tenant_id=tenant_id,
                        event_type="test.child_b",
                        actor="tester",
                        risk="low",
                        payload={"branch": "b"},
                        previous_hash=root_hash,
                        event_hash=child_b_hash,
                        created_at=base + timedelta(seconds=2),
                    ),
                ]
            )


async def latest_sunat_credential(tenant_id: str, empresa_id: str, workspace_id: str) -> SunatCredential | None:
    async with async_session() as session:
        result = await session.execute(
            select(SunatCredential)
            .where(
                SunatCredential.tenant_id == tenant_id,
                SunatCredential.empresa_id == empresa_id,
                SunatCredential.workspace_id == workspace_id,
            )
            .order_by(SunatCredential.created_at.desc(), SunatCredential.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def count_companies_by_ruc(ruc: str) -> int:
    async with async_session() as session:
        return int(await session.scalar(select(func.count(Company.id)).where(Company.ruc == ruc)) or 0)


async def latest_sunat_api_credential(tenant_id: str, empresa_id: str, workspace_id: str) -> SunatApiCredential | None:
    async with async_session() as session:
        result = await session.execute(
            select(SunatApiCredential)
            .where(
                SunatApiCredential.tenant_id == tenant_id,
                SunatApiCredential.empresa_id == empresa_id,
                SunatApiCredential.workspace_id == workspace_id,
            )
            .order_by(SunatApiCredential.created_at.desc(), SunatApiCredential.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def sunat_connection_event_statuses(tenant_id: str, empresa_id: str, workspace_id: str) -> list[str]:
    async with async_session() as session:
        result = await session.execute(
            select(SunatConnectionEvent.status).where(
                SunatConnectionEvent.tenant_id == tenant_id,
                SunatConnectionEvent.empresa_id == empresa_id,
                SunatConnectionEvent.workspace_id == workspace_id,
            )
        )
        return list(result.scalars().all())


async def sunat_readonly_table_counts(run_id: str) -> dict[str, int]:
    async with async_session() as session:
        return {
            "runs": int(await session.scalar(select(func.count(SunatDiagnosticRun.id)).where(SunatDiagnosticRun.id == run_id)) or 0),
            "permissions": int(await session.scalar(select(func.count(SunatPermissionCheck.id)).where(SunatPermissionCheck.run_id == run_id)) or 0),
            "snapshots": int(await session.scalar(select(func.count(SunatRawSnapshot.id)).where(SunatRawSnapshot.run_id == run_id)) or 0),
            "facts": int(await session.scalar(select(func.count(SunatNormalizedFact.id)).where(SunatNormalizedFact.run_id == run_id)) or 0),
            "findings": int(await session.scalar(select(func.count(SunatFinding.id)).where(SunatFinding.run_id == run_id)) or 0),
        }


async def expire_latest_subscription(tenant_id: str) -> None:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Subscription)
                .where(Subscription.tenant_id == tenant_id)
                .order_by(Subscription.created_at.desc(), Subscription.id.desc())
                .limit(1)
            )
            row = result.scalar_one()
            row.status = "active"
            row.plan = "premium"
            row.provider = "mercadopago"
            row.billing_cycle = "monthly"
            row.current_period_start = datetime.now(timezone.utc) - timedelta(days=45)
            row.current_period_end = datetime.now(timezone.utc) - timedelta(days=1)


def test_health_and_runtime_are_honest() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        body = health.json()
        assert body["status"] in {"ok", "degraded"}
        assert body["production_ready"] is False
        assert body["staging_ready"] is False
        assert body["database"]["backend"] == "sqlite"
        assert body["database"]["persistent"] is False
        assert body["database"]["temporal"] is True
        assert body["database"]["source"] == "missing"

        runtime = client.get("/runtime/status")
        assert runtime.status_code == 200
        data = runtime.json()
        assert data["busy_loop"] is False
        assert data["staging_ready"] is False
        assert data["zero_write_policy"] is True
        assert data["human_in_the_loop"] is True
        assert data["ai_pipeline"] == "blocked_provider_disabled"
        assert data["database"]["sqlite"] is True
        assert data["database"]["postgres"] is False
        assert "observability" in data
        assert "persistent_observability" in data


def test_staging_settings_are_separated_from_production(monkeypatch) -> None:
    monkeypatch.setenv("DCFT_APP_ENV", "staging")
    monkeypatch.setenv("DCFT_DEBUG", "false")
    monkeypatch.setenv("DCFT_ADMIN_PASSWORD", "safe-staging-admin-pass")
    monkeypatch.setenv("DCFT_JWT_SECRET", "safe-staging-jwt-secret-at-least-32-chars")
    monkeypatch.setenv("DCFT_FRONTEND_ORIGIN", "https://dcft-staging.example.com")
    monkeypatch.setenv("DCFT_CORS_ORIGINS", "https://dcft-staging.example.com")
    monkeypatch.setenv("DCFT_DATABASE_URL", "postgresql+asyncpg://user:pass@db.example.com:5432/dcft")
    monkeypatch.setenv("DCFT_DATABASE_SSL", "true")
    monkeypatch.setenv("DCFT_AI_PROVIDER_ENABLED", "false")
    monkeypatch.setenv("DCFT_OCR_ENABLED", "false")
    staging_settings = Settings()
    assert staging_settings.security_warnings() == []
    assert staging_settings.staging_ready is True
    assert staging_settings.production_ready is False


def test_non_local_runtime_safety_blocks_missing_and_weak_secrets(monkeypatch) -> None:
    monkeypatch.setenv("DCFT_APP_ENV", "production")
    monkeypatch.setenv("DCFT_DEBUG", "false")
    monkeypatch.setenv("DCFT_FRONTEND_ORIGIN", "https://dcft.example.com")
    monkeypatch.setenv("DCFT_CORS_ORIGINS", "https://dcft.example.com")
    monkeypatch.setenv("DCFT_DATABASE_URL", "postgresql+asyncpg://user:pass@db.example.com:5432/dcft")
    monkeypatch.setenv("DCFT_DATABASE_SSL", "true")
    monkeypatch.setenv("DCFT_JWT_SECRET", "change-me")
    monkeypatch.setenv("DCFT_ADMIN_PASSWORD", "password")
    production_settings = Settings()
    warnings = production_settings.security_warnings()
    assert "jwt_secret_weak_shape" in warnings
    assert "admin_password_weak_shape" in warnings
    with pytest.raises(RuntimeError, match="unsafe_non_local_configuration"):
        production_settings.validate_runtime_safety()


def test_production_settings_require_explicit_strong_secrets(monkeypatch) -> None:
    monkeypatch.setenv("DCFT_APP_ENV", "production")
    monkeypatch.setenv("DCFT_DEBUG", "false")
    monkeypatch.setenv("DCFT_FRONTEND_ORIGIN", "https://dcft.example.com")
    monkeypatch.setenv("DCFT_CORS_ORIGINS", "https://dcft.example.com")
    monkeypatch.setenv("DCFT_DATABASE_URL", "postgresql+asyncpg://user:pass@db.example.com:5432/dcft")
    monkeypatch.setenv("DCFT_DATABASE_SSL", "true")
    monkeypatch.setenv("DCFT_AI_PROVIDER_ENABLED", "false")
    monkeypatch.setenv("DCFT_OCR_ENABLED", "false")
    monkeypatch.setenv("DCFT_JWT_SECRET", "prod-jwt-secret-realistic-32-plus-chars")
    monkeypatch.setenv("DCFT_ADMIN_PASSWORD", "prod-admin-pass-strong-123")
    production_settings = Settings()
    assert production_settings.security_warnings() == []
    assert production_settings.production_ready is True


def test_render_postgres_url_is_normalized_for_async_sqlalchemy(monkeypatch) -> None:
    monkeypatch.setenv("DCFT_DATABASE_URL", "postgresql://user:pass@db.example.com:5432/dcft")
    render_settings = Settings()
    assert render_settings.effective_database_url == "postgresql+asyncpg://user:pass@db.example.com:5432/dcft"
    assert render_settings.database_url_source == "DCFT_DATABASE_URL"


def test_database_url_alias_is_supported_for_vercel_marketplace(monkeypatch) -> None:
    monkeypatch.delenv("DCFT_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db.example.com:5432/dcft")
    marketplace_settings = Settings()
    assert marketplace_settings.effective_database_url == "postgresql+asyncpg://user:pass@db.example.com:5432/dcft"
    assert marketplace_settings.database_url_source == "DATABASE_URL"
    assert marketplace_settings.database_persistent is True
    assert marketplace_settings.database_temporal is False


def test_postgres_sslmode_query_is_translated_for_asyncpg(monkeypatch) -> None:
    monkeypatch.delenv("DCFT_DATABASE_URL", raising=False)
    monkeypatch.delenv("DCFT_DATABASE_SSL", raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:pass@db.example.com:5432/dcft?sslmode=require&channel_binding=require",
    )
    marketplace_settings = Settings()
    assert marketplace_settings.effective_database_url == "postgresql+asyncpg://user:pass@db.example.com:5432/dcft"
    assert marketplace_settings.database_url_sslmode == "require"
    assert marketplace_settings.database_ssl_enabled is True
    assert marketplace_settings.database_connect_args["ssl"] is True


def test_vercel_production_warns_when_sqlite_fallback_is_active(monkeypatch) -> None:
    monkeypatch.delenv("DCFT_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DCFT_APP_ENV", "local")
    monkeypatch.setenv("VERCEL_ENV", "production")
    vercel_settings = Settings()
    warnings = vercel_settings.security_warnings()
    assert "sqlite_local_fallback_active" in warnings
    assert "vercel_production_app_env_local" in warnings
    assert "vercel_production_requires_postgresql" in warnings


def test_postgresql_schema_search_path_is_supported(monkeypatch) -> None:
    monkeypatch.setenv("DCFT_DATABASE_URL", "postgresql://user:pass@db.example.com:5432/dcft")
    monkeypatch.setenv("DCFT_DATABASE_SSL", "false")
    monkeypatch.setenv("DCFT_DATABASE_SCHEMA", "dcft_restore_validation")
    schema_settings = Settings()
    assert schema_settings.database_connect_args["server_settings"]["search_path"] == "dcft_restore_validation"


def test_auth_rejects_invalid_missing_bad_and_forged_tokens() -> None:
    with TestClient(app) as client:
        assert client.post("/auth/login", json={"username": "bad", "password": "bad"}).status_code == 401
        assert client.get("/auth/me").status_code == 401
        assert client.get("/auth/me", headers={"Authorization": "Bearer bad-token"}).status_code == 401
        forged = {"Authorization": f"Bearer {forged_token()}"}
        assert client.get("/auth/me", headers=forged).status_code == 401
        assert client.get("/dashboard/summary", headers=forged).status_code == 401


def test_logout_revokes_token_and_audit_integrity_is_visible() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        assert client.get("/auth/me", headers=headers).status_code == 200
        logout = client.post("/auth/logout", headers=headers, json={})
        assert logout.status_code == 200
        assert client.get("/auth/me", headers=headers).status_code == 401

        fresh_headers = auth_headers(client)
        audit = client.get("/audit/events", headers=fresh_headers)
        assert audit.status_code == 200
        body = audit.json()
        assert body["tenant_id"] == "local-demo"
        assert body["integrity"]["tamper_detected"] is False
        assert body["integrity"]["checked_events"] >= 1
        assert body["integrity"]["future_chain_hardened"] is True
        assert body["integrity"]["chain_status"] in {
            "ok",
            "historical_forks_no_tamper",
            "legacy_unhashed_events",
            "tamper_detected",
        }


def test_audit_integrity_marks_historical_forks_without_hiding_them() -> None:
    tenant_id = f"fork-{uuid.uuid4().hex[:8]}"
    with TestClient(app):
        asyncio.run(insert_historical_audit_fork(tenant_id))

        summary = asyncio.run(repositories.audit_integrity_summary(tenant_id=tenant_id))

    assert summary["checked_events"] == 3
    assert summary["legacy_unhashed_events"] == 0
    assert summary["tamper_detected"] is False
    assert summary["hash_mismatch_event_ids"] == []
    assert summary["broken_link_event_ids"] == []
    assert summary["chain_forks_detected"] is True
    assert summary["chain_fork_count"] == 1
    assert summary["historical_forks"] is True
    assert summary["future_chain_hardened"] is True
    assert summary["chain_status"] == "historical_forks_no_tamper"


def test_audit_append_serializes_future_events_without_forks() -> None:
    tenant_id = f"serial-{uuid.uuid4().hex[:8]}"

    async def append_events() -> dict:
        base = datetime(2026, 6, 6, 1, 0, tzinfo=timezone.utc)
        for index in range(5):
            await repositories.add_audit_event(
                "test.future_event",
                "tester",
                {"index": index},
                "low",
                tenant_id,
                event_id=f"evt-{index}-{tenant_id}",
                created_at=(base + timedelta(seconds=index)).isoformat(),
            )
        return await repositories.audit_integrity_summary(tenant_id=tenant_id)

    with TestClient(app):
        summary = asyncio.run(append_events())

    assert summary["checked_events"] == 5
    assert summary["tamper_detected"] is False
    assert summary["chain_forks_detected"] is False
    assert summary["chain_fork_count"] == 0
    assert summary["historical_forks"] is False
    assert summary["future_chain_hardened"] is True
    assert summary["chain_status"] == "ok"


def test_login_lockout_is_persistent_security_control() -> None:
    with TestClient(app) as client:
        for _ in range(10):
            response = client.post("/auth/login", json={"username": "locked-user", "password": "bad"})
            assert response.status_code == 401
        locked = client.post("/auth/login", json={"username": "locked-user", "password": "bad"})
        assert locked.status_code == 429


def test_student_doctor_provider_missing_does_not_consume_quota() -> None:
    with TestClient(app) as client:
        headers, _ = create_verified_student_headers(client, uuid.uuid4().hex[:8])

        status_response = client.get("/student/doctor/status", headers=headers)
        assert status_response.status_code == 200
        status_body = status_response.json()
        assert status_body["ai_provider_missing"] is True
        assert status_body["quota"]["questions_used"] == 0
        assert status_body["quota"]["questions_limit"] == 5

        ask_response = client.post("/student/doctor/ask", headers=headers, json={"question": "Que es capital de trabajo?"})
        assert ask_response.status_code == 503
        assert ask_response.json()["detail"]["error"] == "ai_provider_missing"
        assert ask_response.json()["detail"]["ai_provider_missing"] is True

        status_after = client.get("/student/doctor/status", headers=headers)
        assert status_after.status_code == 200
        assert status_after.json()["quota"]["questions_used"] == 0


def test_student_doctor_success_quota_and_provider_errors(monkeypatch) -> None:
    call_count = {"value": 0}

    async def failing_provider(provider: dict, question: str) -> dict:
        call_count["value"] += 1
        raise RuntimeError("provider unavailable")

    async def successful_provider(provider: dict, question: str) -> dict:
        call_count["value"] += 1
        return {"answer": f"Respuesta guiada para: {question}", "model": "test-model"}

    monkeypatch.setattr(
        student_doctor_service,
        "_provider_config",
        lambda: {"provider": "openrouter", "api_key": "test-key", "model": "test-model", "timeout": 1, "base_url": "https://example.invalid"},
    )
    monkeypatch.setattr(student_doctor_service, "_call_provider", failing_provider)

    with TestClient(app) as client:
        headers, _ = create_verified_student_headers(client, uuid.uuid4().hex[:8])

        failed = client.post("/student/doctor/ask", headers=headers, json={"question": "Explica credito fiscal"})
        assert failed.status_code == 502
        assert client.get("/student/doctor/status", headers=headers).json()["quota"]["questions_used"] == 0

        monkeypatch.setattr(student_doctor_service, "_call_provider", successful_provider)
        for index in range(5):
            response = client.post("/student/doctor/ask", headers=headers, json={"question": f"Pregunta {index}"})
            assert response.status_code == 200
            body = response.json()
            assert body["doctor_name"] == "Doctor de estudio contable, financiero y tributario"
            assert body["quota"]["questions_used"] == index + 1
            assert body["quota"]["questions_remaining"] == max(0, 4 - index)

        blocked = client.post("/student/doctor/ask", headers=headers, json={"question": "Una mas"})
        assert blocked.status_code == 429
        assert blocked.json()["detail"]["message"] == QUOTA_EXCEEDED_MESSAGE
        assert client.get("/student/doctor/status", headers=headers).json()["quota"]["questions_used"] == 5
        assert call_count["value"] == 6


def test_server_side_rbac_blocks_operator_high_risk_and_governance_decision() -> None:
    with TestClient(app) as client:
        asyncio.run(create_test_user("operator_user", "operator"))
        login = client.post("/auth/login", json={"username": "operator_user", "password": "operator-pass"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        high = client.post(
            "/workflows",
            headers=headers,
            json={"name": "operator high", "objective": "should fail", "steps": ["a"], "risk": "high"},
        )
        assert high.status_code == 403
        governance = client.post(
            "/governance/approval-requests",
            headers=headers,
            json={"scope": "workflow", "action": "approve", "risk": "high", "reason": "operator bypass"},
        )
        assert governance.status_code == 403


def test_auditor_can_read_audit_but_cannot_write_operational_records() -> None:
    with TestClient(app) as client:
        asyncio.run(create_test_user("auditor_user", "auditor", password="auditor-pass"))
        login = client.post("/auth/login", json={"username": "auditor_user", "password": "auditor-pass"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert client.get("/audit/events", headers=headers).status_code == 200
        write = client.post(
            "/alerts",
            headers=headers,
            json={"title": "auditor write blocked", "severity": "low", "source": "test"},
        )
        assert write.status_code == 403


def test_dashboard_records_and_tenant_audit_are_scoped() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        assert client.get("/dashboard/summary").status_code == 401
        assert client.get("/alerts?limit=501", headers=headers).status_code == 422
        summary = client.get("/dashboard/summary", headers=headers)
        assert summary.status_code == 200
        assert summary.json()["product"].startswith("DCFT")

        alert = client.post(
            "/alerts",
            headers=headers,
            json={"title": "Caja con vencimientos cercanos", "severity": "high", "source": "test"},
        )
        assert alert.status_code == 200
        assert alert.json()["tenant_id"] == "local-demo"

        other_tenant = {"Authorization": f"Bearer {forged_token(username='missing-user', tenant_id='tenant-b')}"}
        assert client.get("/alerts", headers=other_tenant).status_code == 401

        updated_summary = client.get("/dashboard/summary", headers=headers)
        assert updated_summary.status_code == 200
        assert updated_summary.json()["counts"]["audit_events"] >= 1


def test_onboarding_creates_real_tenant_admin_and_product_analytics() -> None:
    with TestClient(app) as client:
        unique = uuid.uuid4().hex[:8]
        status_response = client.get("/onboarding/status")
        assert status_response.status_code == 200
        assert status_response.json()["signup_enabled"] is True

        onboarding = client.post(
            "/onboarding/tenants",
            json={
                "tenant_name": f"Tenant Producto {unique}",
                "admin_username": f"tenant_admin_{unique}",
                "admin_password": "tenant-admin-pass-123",
                "plan": "student",
            },
        )
        assert onboarding.status_code == 200
        body = onboarding.json()
        assert "access_token" not in body
        assert body["email_verification"]["required"] is True
        assert body["email_verification"]["email_provider_missing"] is True
        assert body["email_verification"]["message"] == "Falta configurar proveedor de correo para activar cuentas."

        blocked_login = client.post("/auth/login", json={"username": f"tenant_admin_{unique}", "password": "tenant-admin-pass-123"})
        assert blocked_login.status_code == 403
        assert blocked_login.json()["detail"]["error"] == "email_not_verified"
        assert blocked_login.json()["detail"]["message"] == "Confirma tu correo para activar tu cuenta."

        resend = client.post("/auth/resend-verification", json={"username": f"tenant_admin_{unique}"})
        assert resend.status_code == 200
        assert resend.json()["email_provider_missing"] is True

        headers = verified_headers(client, f"tenant_admin_{unique}", "tenant-admin-pass-123")

        me = client.get("/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["role"] == "tenant_admin"
        assert me.json()["plan"] == "student"
        assert body["trial"]["status"] == "none"
        assert body["company"] is None

        event = client.post("/analytics/events", headers=headers, json={"event_type": "onboarding.viewed", "metadata": {"step": "welcome"}})
        assert event.status_code == 200

        feedback = client.post(
            "/feedback",
            headers=headers,
            json={"category": "onboarding", "severity": "medium", "message": "Onboarding was understandable."},
        )
        assert feedback.status_code == 200

        alert = client.post(
            "/alerts",
            headers=headers,
            json={"title": "Primer hito operacional", "severity": "low", "source": "onboarding"},
        )
        assert alert.status_code == 200

        analytics = client.get("/analytics/summary", headers=headers)
        assert analytics.status_code == 200
        assert analytics.json()["activation"]["onboarding_completed"] is True
        assert analytics.json()["activation"]["first_business_signal"] is True


def test_onboarding_business_plan_requires_ruc_and_creates_initial_company_workspace() -> None:
    with TestClient(app) as client:
        unique = uuid.uuid4().hex[:8]

        missing_ruc = client.post(
            "/onboarding/tenants",
            json={
                "tenant_name": f"MYPE Sin RUC {unique}",
                "admin_username": f"mype_missing_{unique}",
                "admin_password": "mype-admin-pass-123",
                "plan": "mype",
            },
        )
        assert missing_ruc.status_code == 422
        assert missing_ruc.json()["detail"]["error"] == "ruc_required_for_business_plan"

        created = client.post(
            "/onboarding/tenants",
            json={
                "tenant_name": f"MYPE Con RUC {unique}",
                "admin_username": f"mype_admin_{unique}",
                "admin_password": "mype-admin-pass-123",
                "plan": "mype",
                "ruc": f"204{unique}",
                "razon_social": f"Empresa MYPE {unique}",
            },
        )
        assert created.status_code == 200
        body = created.json()
        assert body["plan"]["id"] == "mype"
        assert body["trial"]["status"] == "active"
        assert body["company"]["ruc"] == f"204{unique}"
        assert body["workspace"]["empresa_id"] == body["company"]["id"]
        assert body["context"]["active_workspace_id"] == body["workspace"]["id"]

        assert "access_token" not in body
        headers = verified_headers(client, f"mype_admin_{unique}", "mype-admin-pass-123")
        assert client.get("/identity/companies", headers=headers).json()[0]["id"] == body["company"]["id"]
        assert client.get("/identity/workspaces", headers=headers).json()[0]["id"] == body["workspace"]["id"]


def test_admin_ceo_can_manage_trials_and_plans_but_regular_users_cannot() -> None:
    with TestClient(app) as client:
        unique = uuid.uuid4().hex[:8]
        created = client.post(
            "/onboarding/tenants",
            json={
                "tenant_name": f"Admin Trial {unique}",
                "admin_username": f"admin_trial_{unique}",
                "admin_password": "trial-admin-pass-123",
                "plan": "free",
                "trial_requested": False,
            },
        )
        assert created.status_code == 200
        assert "access_token" not in created.json()
        tenant_headers = verified_headers(client, f"admin_trial_{unique}", "trial-admin-pass-123")
        me = client.get("/auth/me", headers=tenant_headers).json()

        missing_token = client.get("/admin/ceo/users")
        assert missing_token.status_code == 401

        regular_admin = client.get("/admin/ceo/users", headers=tenant_headers)
        assert regular_admin.status_code == 403

        ceo_headers = auth_headers(client)
        listed = client.get("/admin/ceo/users", headers=ceo_headers)
        assert listed.status_code == 200
        assert any(user["user_id"] == me["user_id"] for user in listed.json()["users"])

        activated = client.post(f"/admin/ceo/users/{me['user_id']}/trial", headers=ceo_headers, json={"active": True, "days": 7})
        assert activated.status_code == 200
        assert activated.json()["subscription"]["trial_active"] is True
        assert activated.json()["subscription"]["plan_effective"] == "premium"

        summary = client.get("/dashboard/summary", headers=tenant_headers)
        assert summary.status_code == 200
        assert summary.json()["trial"]["active"] is True
        assert summary.json()["trial"]["plan_effective"] == "premium"
        assert summary.json()["plan"]["id"] == "premium"

        changed = client.patch(f"/admin/ceo/users/{me['user_id']}/plan", headers=ceo_headers, json={"plan": "mype"})
        assert changed.status_code == 200
        assert changed.json()["subscription"]["plan"] == "mype"

        deactivated = client.post(f"/admin/ceo/users/{me['user_id']}/trial", headers=ceo_headers, json={"active": False, "days": 7})
        assert deactivated.status_code == 200
        assert deactivated.json()["subscription"]["trial_active"] is False


def test_onboarding_videos_and_checklist_are_persisted() -> None:
    with TestClient(app) as client:
        unique = uuid.uuid4().hex[:8]
        created = client.post(
            "/onboarding/tenants",
            json={
                "tenant_name": f"Videos {unique}",
                "admin_username": f"videos_{unique}",
                "admin_password": "video-admin-pass-123",
                "plan": "student",
            },
        )
        assert created.status_code == 200
        assert "access_token" not in created.json()
        headers = verified_headers(client, f"videos_{unique}", "video-admin-pass-123")

        progress = client.get("/onboarding/progress", headers=headers)
        assert progress.status_code == 200
        assert len(progress.json()["videos"]) == 3
        assert progress.json()["checklist"]["account_created"] is True

        for video_id in ["sunat_auxiliary_user", "connect_company", "interpret_diagnosis"]:
            marked = client.post(f"/onboarding/videos/{video_id}/seen", headers=headers, json={})
            assert marked.status_code == 200

        persisted = client.get("/onboarding/progress", headers=headers)
        assert persisted.status_code == 200
        assert persisted.json()["checklist"]["videos_seen"] is True
        assert len(persisted.json()["videos_seen"]) == 3


def test_sunat_auxiliary_preparation_is_read_only_and_rejects_secret_fields() -> None:
    with TestClient(app) as client:
        unique = uuid.uuid4().hex[:8]
        created = client.post(
            "/onboarding/tenants",
            json={
                "tenant_name": f"SUNAT Aux {unique}",
                "admin_username": f"sunat_aux_{unique}",
                "admin_password": "sunat-aux-pass-123",
                "plan": "mype",
                "ruc": f"206{unique}",
                "razon_social": f"SUNAT Auxiliar {unique}",
            },
        )
        assert created.status_code == 200
        body = created.json()
        assert "access_token" not in body
        headers = verified_headers(client, f"sunat_aux_{unique}", "sunat-aux-pass-123")
        payload = {
            "empresa_id": body["company"]["id"],
            "workspace_id": body["workspace"]["id"],
            "ruc": body["company"]["ruc"],
            "auxiliary_user_alias": f"aux_{unique}",
        }

        rejected_secret = client.post("/sunat/auxiliary-access/prepare", headers=headers, json={**payload, "password": "never-store"})
        assert rejected_secret.status_code == 422

        prepared = client.post("/sunat/auxiliary-access/prepare", headers=headers, json=payload)
        assert prepared.status_code == 200
        prepared_body = prepared.json()
        assert prepared_body["foundation_only"] is True
        assert prepared_body["real_connector_enabled"] is False
        assert prepared_body["connection"]["estado"] == "NOT_CONNECTED"
        assert prepared_body["connection"]["remote_actions_enabled"] is False
        assert prepared_body["connection"]["read_only"] is True

        progress = client.get("/onboarding/progress", headers=headers)
        assert progress.status_code == 200
        assert progress.json()["checklist"]["sunat_auxiliary_prepared"] is True


def test_plan_limits_upgrade_and_downgrade_are_enforced() -> None:
    with TestClient(app) as client:
        unique = uuid.uuid4().hex[:8]
        onboarding = client.post(
            "/onboarding/tenants",
            json={
                "tenant_name": f"Tenant Free {unique}",
                "admin_username": f"free_admin_{unique}",
                "admin_password": "free-admin-pass-123",
                "plan": "free",
            },
        )
        assert onboarding.status_code == 200
        assert "access_token" not in onboarding.json()
        headers = verified_headers(client, f"free_admin_{unique}", "free-admin-pass-123")

        for index in range(5):
            response = client.post(
                "/alerts",
                headers=headers,
                json={"title": f"Free alert {index}", "severity": "low", "source": "limit-test"},
            )
            assert response.status_code == 200

        blocked = client.post(
            "/alerts",
            headers=headers,
            json={"title": "Blocked free alert", "severity": "low", "source": "limit-test"},
        )
        assert blocked.status_code == 402
        assert blocked.json()["detail"]["error"] == "plan_limit_reached"

        self_upgrade = client.patch("/subscriptions/current", headers=headers, json={"plan": "business_basic"})
        assert self_upgrade.status_code == 402
        assert self_upgrade.json()["detail"]["error"] == "checkout_required_for_commercial_plan"

        me = client.get("/auth/me", headers=headers).json()
        upgraded = client.patch(f"/admin/ceo/users/{me['user_id']}/plan", headers=auth_headers(client), json={"plan": "business_basic"})
        assert upgraded.status_code == 200
        assert upgraded.json()["subscription"]["plan"] == "mype"

        allowed = client.post(
            "/alerts",
            headers=headers,
            json={"title": "Allowed after upgrade", "severity": "low", "source": "limit-test"},
        )
        assert allowed.status_code == 200

        downgraded = client.patch("/subscriptions/current", headers=headers, json={"plan": "free"})
        assert downgraded.status_code == 200
        assert downgraded.json()["over_limit"]["alerts"]["current"] == 6


def test_checkout_blocks_without_payment_provider_and_does_not_activate_plan() -> None:
    with TestClient(app) as client:
        unique = uuid.uuid4().hex[:8]
        created = client.post(
            "/onboarding/tenants",
            json={
                "tenant_name": f"Checkout MYPE {unique}",
                "admin_username": f"checkout_{unique}",
                "admin_password": "checkout-pass-123",
                "plan": "mype",
                "ruc": f"212{unique}",
                "razon_social": f"Checkout SAC {unique}",
            },
        )
        assert created.status_code == 200
        assert "access_token" not in created.json()
        headers = verified_headers(client, f"checkout_{unique}", "checkout-pass-123")

        status_response = client.get("/subscriptions/checkout/status", headers=headers)
        assert status_response.status_code == 200
        status_body = status_response.json()
        assert status_body["payment_provider_missing"] is True
        assert status_body["message"] == "Falta configurar proveedor de pago para activar checkout real."
        assert status_body["plans"]["student"]["monthly"]["amount_cents"] == 0
        assert status_body["plans"]["mype"]["monthly"]["amount_cents"] == 8900
        assert status_body["plans"]["mype"]["annual"]["amount_cents"] == 89000
        assert status_body["plans"]["premium"]["monthly"]["amount_cents"] == 19900
        assert status_body["plans"]["premium"]["annual"]["amount_cents"] == 199000

        before = client.get("/subscriptions/current", headers=headers)
        assert before.status_code == 200
        assert before.json()["id"] == "mype"

        checkout = client.post("/subscriptions/checkout", headers=headers, json={"plan": "premium", "billing_cycle": "monthly"})
        assert checkout.status_code == 503
        assert checkout.json()["detail"]["payment_provider_missing"] is True
        assert checkout.json()["detail"]["message"] == "Falta configurar proveedor de pago para activar checkout real."

        after = client.get("/subscriptions/current", headers=headers)
        assert after.status_code == 200
        assert after.json()["id"] == "mype"


def test_checkout_creation_does_not_activate_plan_before_webhook(monkeypatch) -> None:
    original_provider = settings.payment_provider
    original_public_key = settings.payment_public_key
    original_secret = settings.payment_secret_key
    original_webhook_secret = settings.payment_webhook_secret
    object.__setattr__(settings, "payment_provider", "stripe")
    object.__setattr__(settings, "payment_public_key", "pk_test_checkout_creation")
    object.__setattr__(settings, "payment_secret_key", "sk_test_checkout_creation")
    object.__setattr__(settings, "payment_webhook_secret", "unit-stripe-webhook-checkout-creation")
    monkeypatch.setattr(
        payment_service,
        "_create_stripe_checkout",
        lambda user, plan, billing_cycle, amount_cents, currency: {
            "id": f"cs_test_{uuid.uuid4().hex}",
            "url": "https://checkout.stripe.test/session",
        },
    )
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            created = client.post(
                "/onboarding/tenants",
                json={
                    "tenant_name": f"Checkout Stripe {unique}",
                    "admin_username": f"stripe_checkout_{unique}",
                    "admin_password": "checkout-pass-123",
                    "plan": "mype",
                    "ruc": f"213{unique}",
                    "razon_social": f"Stripe Checkout SAC {unique}",
                    "trial_requested": False,
                },
            )
            assert created.status_code == 200
            headers = verified_headers(client, f"stripe_checkout_{unique}", "checkout-pass-123")

            checkout = client.post("/subscriptions/checkout", headers=headers, json={"plan": "premium", "billing_cycle": "annual"})
            assert checkout.status_code == 200
            assert checkout.json()["status"] == "pending"
            assert checkout.json()["checkout_url"] == "https://checkout.stripe.test/session"

            current = client.get("/subscriptions/current", headers=headers)
            assert current.status_code == 200
            assert current.json()["id"] == "mype"
            assert current.json()["provider"] is None
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "payment_public_key", original_public_key)
        object.__setattr__(settings, "payment_secret_key", original_secret)
        object.__setattr__(settings, "payment_webhook_secret", original_webhook_secret)


def test_mercadopago_checkout_creation_does_not_activate_plan_before_webhook(monkeypatch) -> None:
    original_provider = settings.payment_provider
    original_access_token = settings.mercadopago_access_token
    original_public_key = settings.mercadopago_public_key
    original_webhook_secret = settings.mercadopago_webhook_secret
    object.__setattr__(settings, "payment_provider", "mercadopago")
    object.__setattr__(settings, "mercadopago_access_token", "unit-mercadopago-token")
    object.__setattr__(settings, "mercadopago_public_key", "unit-mercadopago-public")
    object.__setattr__(settings, "mercadopago_webhook_secret", "unit-mercadopago-webhook")
    monkeypatch.setattr(
        payment_service,
        "_create_mercadopago_checkout",
        lambda user, plan, billing_cycle, amount_cents, currency, checkout_session_id, company_id=None: {
            "id": f"preapproval-{uuid.uuid4().hex}",
            "init_point": "https://www.mercadopago.com.pe/subscriptions/checkout",
        },
    )
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            created = client.post(
                "/onboarding/tenants",
                json={
                    "tenant_name": f"Checkout Mercado Pago {unique}",
                    "admin_username": f"mp_checkout_{unique}@example.com",
                    "admin_password": "checkout-pass-123",
                    "plan": "mype",
                    "ruc": f"217{unique}",
                    "razon_social": f"Mercado Pago Checkout SAC {unique}",
                    "trial_requested": False,
                },
            )
            assert created.status_code == 200
            headers = verified_headers(client, f"mp_checkout_{unique}@example.com", "checkout-pass-123")

            status_response = client.get("/subscriptions/checkout/status", headers=headers)
            assert status_response.status_code == 200
            status_body = status_response.json()
            assert status_body["provider"] == "mercadopago"
            assert status_body["payment_provider_missing"] is False
            assert status_body["provider_primary"] == "mercadopago"

            checkout = client.post("/subscriptions/checkout", headers=headers, json={"plan": "premium", "billing_cycle": "annual"})
            assert checkout.status_code == 200
            checkout_body = checkout.json()
            assert checkout_body["provider"] == "mercadopago"
            assert checkout_body["status"] == "pending"
            assert checkout_body["checkout_url"] == "https://www.mercadopago.com.pe/subscriptions/checkout"

            current = client.get("/subscriptions/current", headers=headers)
            assert current.status_code == 200
            assert current.json()["id"] == "mype"
            assert current.json()["provider"] is None
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "mercadopago_access_token", original_access_token)
        object.__setattr__(settings, "mercadopago_public_key", original_public_key)
        object.__setattr__(settings, "mercadopago_webhook_secret", original_webhook_secret)


def test_stripe_webhook_signed_activates_subscription_and_duplicate_is_idempotent() -> None:
    original_provider = settings.payment_provider
    original_public_key = settings.payment_public_key
    original_secret = settings.payment_secret_key
    original_webhook_secret = settings.payment_webhook_secret
    object.__setattr__(settings, "payment_provider", "stripe")
    object.__setattr__(settings, "payment_public_key", "pk_test_webhook_activation")
    object.__setattr__(settings, "payment_secret_key", "sk_test_webhook_activation")
    object.__setattr__(settings, "payment_webhook_secret", "unit-stripe-webhook-activation")
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            created = client.post(
                "/onboarding/tenants",
                json={
                    "tenant_name": f"Webhook Stripe {unique}",
                    "admin_username": f"stripe_webhook_{unique}",
                    "admin_password": "checkout-pass-123",
                    "plan": "mype",
                    "ruc": f"214{unique}",
                    "razon_social": f"Webhook Stripe SAC {unique}",
                    "trial_requested": False,
                },
            )
            assert created.status_code == 200
            tenant_id = created.json()["tenant_id"]
            headers = verified_headers(client, f"stripe_webhook_{unique}", "checkout-pass-123")
            me = client.get("/auth/me", headers=headers).json()
            stripe_session_id = f"cs_test_{uuid.uuid4().hex}"
            asyncio.run(
                repositories.create_checkout_session_record(
                    tenant_id=tenant_id,
                    user_id=me["user_id"],
                    plan="premium",
                    billing_cycle="annual",
                    provider="stripe",
                    provider_session_id=stripe_session_id,
                    checkout_url="https://checkout.stripe.test/session",
                    amount_cents=199000,
                    currency="PEN",
                    status="pending",
                    metadata={"provider_status": "created"},
                )
            )
            raw_body = json.dumps(
                {
                    "id": f"evt_{uuid.uuid4().hex}",
                    "type": "checkout.session.completed",
                    "created": int(time.time()),
                    "data": {
                        "object": {
                            "id": stripe_session_id,
                            "customer": "cus_test_dcft",
                            "subscription": "sub_test_dcft",
                            "amount_total": 199000,
                            "currency": "pen",
                            "created": int(time.time()),
                            "metadata": {
                                "tenant_id": tenant_id,
                                "user_id": me["user_id"],
                                "plan": "premium",
                                "billing_cycle": "annual",
                            },
                        }
                    },
                },
                separators=(",", ":"),
            ).encode("utf-8")

            response = client.post(
                "/subscriptions/stripe/webhook",
                content=raw_body,
                headers={"stripe-signature": stripe_signature(raw_body, "unit-stripe-webhook-activation")},
            )
            assert response.status_code == 200
            assert response.json()["status"] == "processed"
            assert response.json()["activation"]["plan"] == "premium"
            assert response.json()["activation"]["billing_cycle"] == "annual"

            current = client.get("/subscriptions/current", headers=headers)
            assert current.status_code == 200
            body = current.json()
            assert body["id"] == "premium"
            assert body["status"] == "active"
            assert body["provider"] == "stripe"
            assert body["billing_cycle"] == "annual"
            assert body["interval"] == "yearly"

            duplicate = client.post(
                "/subscriptions/stripe/webhook",
                content=raw_body,
                headers={"stripe-signature": stripe_signature(raw_body, "unit-stripe-webhook-activation")},
            )
            assert duplicate.status_code == 200
            assert duplicate.json()["status"] == "duplicate"
            after_duplicate = client.get("/subscriptions/current", headers=headers).json()
            assert after_duplicate["id"] == "premium"
            assert after_duplicate["provider"] == "stripe"
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "payment_public_key", original_public_key)
        object.__setattr__(settings, "payment_secret_key", original_secret)
        object.__setattr__(settings, "payment_webhook_secret", original_webhook_secret)


def test_stripe_webhook_invalid_signature_does_not_activate_subscription() -> None:
    original_provider = settings.payment_provider
    original_public_key = settings.payment_public_key
    original_secret = settings.payment_secret_key
    original_webhook_secret = settings.payment_webhook_secret
    object.__setattr__(settings, "payment_provider", "stripe")
    object.__setattr__(settings, "payment_public_key", "pk_test_invalid_signature")
    object.__setattr__(settings, "payment_secret_key", "sk_test_invalid_signature")
    object.__setattr__(settings, "payment_webhook_secret", "unit-stripe-webhook-invalid-signature")
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            created = client.post(
                "/onboarding/tenants",
                json={
                    "tenant_name": f"Invalid Stripe {unique}",
                    "admin_username": f"stripe_invalid_{unique}",
                    "admin_password": "checkout-pass-123",
                    "plan": "mype",
                    "ruc": f"215{unique}",
                    "razon_social": f"Invalid Stripe SAC {unique}",
                    "trial_requested": False,
                },
            )
            assert created.status_code == 200
            tenant_id = created.json()["tenant_id"]
            headers = verified_headers(client, f"stripe_invalid_{unique}", "checkout-pass-123")
            me = client.get("/auth/me", headers=headers).json()
            stripe_session_id = f"cs_test_{uuid.uuid4().hex}"
            asyncio.run(
                repositories.create_checkout_session_record(
                    tenant_id=tenant_id,
                    user_id=me["user_id"],
                    plan="premium",
                    billing_cycle="monthly",
                    provider="stripe",
                    provider_session_id=stripe_session_id,
                    checkout_url="https://checkout.stripe.test/session",
                    amount_cents=19900,
                    currency="PEN",
                    status="pending",
                    metadata={"provider_status": "created"},
                )
            )
            raw_body = json.dumps(
                {
                    "id": f"evt_{uuid.uuid4().hex}",
                    "type": "checkout.session.completed",
                    "created": int(time.time()),
                    "data": {
                        "object": {
                            "id": stripe_session_id,
                            "amount_total": 19900,
                            "currency": "pen",
                            "metadata": {
                                "tenant_id": tenant_id,
                                "user_id": me["user_id"],
                                "plan": "premium",
                                "billing_cycle": "monthly",
                            },
                        }
                    },
                },
                separators=(",", ":"),
            ).encode("utf-8")

            response = client.post(
                "/subscriptions/stripe/webhook",
                content=raw_body,
                headers={"stripe-signature": stripe_signature(raw_body, "wrong_secret")},
            )
            assert response.status_code == 400

            current = client.get("/subscriptions/current", headers=headers)
            assert current.status_code == 200
            assert current.json()["id"] == "mype"
            assert current.json()["provider"] is None
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "payment_public_key", original_public_key)
        object.__setattr__(settings, "payment_secret_key", original_secret)
        object.__setattr__(settings, "payment_webhook_secret", original_webhook_secret)


@pytest.mark.parametrize(
    ("plan", "billing_cycle", "amount_cents", "expected_interval"),
    [
        ("mype", "monthly", 8900, "monthly"),
        ("mype", "annual", 89000, "yearly"),
        ("premium", "monthly", 19900, "monthly"),
        ("premium", "annual", 199000, "yearly"),
    ],
)
def test_stripe_webhook_activates_each_commercial_plan_cycle(
    plan: str,
    billing_cycle: str,
    amount_cents: int,
    expected_interval: str,
) -> None:
    original_provider = settings.payment_provider
    original_public_key = settings.payment_public_key
    original_secret = settings.payment_secret_key
    original_webhook_secret = settings.payment_webhook_secret
    webhook_secret = f"unit-stripe-webhook-cycle-{plan}-{billing_cycle}"
    object.__setattr__(settings, "payment_provider", "stripe")
    object.__setattr__(settings, "payment_public_key", f"pk_test_cycle_{plan}_{billing_cycle}")
    object.__setattr__(settings, "payment_secret_key", f"sk_test_cycle_{plan}_{billing_cycle}")
    object.__setattr__(settings, "payment_webhook_secret", webhook_secret)
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            created = client.post(
                "/onboarding/tenants",
                json={
                    "tenant_name": f"Cycle Stripe {plan} {billing_cycle} {unique}",
                    "admin_username": f"stripe_cycle_{unique}",
                    "admin_password": "checkout-pass-123",
                    "plan": "mype",
                    "ruc": f"216{unique}",
                    "razon_social": f"Cycle Stripe SAC {unique}",
                    "trial_requested": False,
                },
            )
            assert created.status_code == 200
            tenant_id = created.json()["tenant_id"]
            headers = verified_headers(client, f"stripe_cycle_{unique}", "checkout-pass-123")
            me = client.get("/auth/me", headers=headers).json()
            stripe_session_id = f"cs_test_{uuid.uuid4().hex}"
            asyncio.run(
                repositories.create_checkout_session_record(
                    tenant_id=tenant_id,
                    user_id=me["user_id"],
                    plan=plan,
                    billing_cycle=billing_cycle,
                    provider="stripe",
                    provider_session_id=stripe_session_id,
                    checkout_url="https://checkout.stripe.test/session",
                    amount_cents=amount_cents,
                    currency="PEN",
                    status="pending",
                    metadata={"provider_status": "created"},
                )
            )
            raw_body = json.dumps(
                {
                    "id": f"evt_{uuid.uuid4().hex}",
                    "type": "checkout.session.completed",
                    "created": int(time.time()),
                    "data": {
                        "object": {
                            "id": stripe_session_id,
                            "customer": "cus_test_dcft",
                            "subscription": f"sub_test_{plan}_{billing_cycle}",
                            "amount_total": amount_cents,
                            "currency": "pen",
                            "created": int(time.time()),
                            "metadata": {
                                "tenant_id": tenant_id,
                                "user_id": me["user_id"],
                                "plan": plan,
                                "billing_cycle": billing_cycle,
                            },
                        }
                    },
                },
                separators=(",", ":"),
            ).encode("utf-8")

            response = client.post(
                "/subscriptions/stripe/webhook",
                content=raw_body,
                headers={"stripe-signature": stripe_signature(raw_body, webhook_secret)},
            )
            assert response.status_code == 200
            assert response.json()["status"] == "processed"
            assert response.json()["activation"]["plan"] == plan
            assert response.json()["activation"]["billing_cycle"] == billing_cycle
            assert response.json()["activation"]["amount_cents"] == amount_cents
            assert response.json()["activation"]["currency"] == "PEN"

            current = client.get("/subscriptions/current", headers=headers)
            assert current.status_code == 200
            assert current.json()["id"] == plan
            assert current.json()["status"] == "active"
            assert current.json()["provider"] == "stripe"
            assert current.json()["billing_cycle"] == billing_cycle
            assert current.json()["interval"] == expected_interval

            status_response = client.get("/subscriptions/status", headers=headers)
            assert status_response.status_code == 200
            status_body = status_response.json()
            assert status_body["plan"] == plan
            assert status_body["status"] == "active"
            assert status_body["provider"] == "stripe"
            assert status_body["billing_cycle"] == billing_cycle
            assert status_body["interval"] == expected_interval
            assert status_body["payment_status"] == "paid"
            assert status_body["checkout"]["status"] == "paid"
            assert status_body["checkout"]["amount_cents"] == amount_cents
            assert status_body["checkout"]["currency"] == "PEN"
            assert status_body["checkout"]["paid_at"] is not None
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "payment_public_key", original_public_key)
        object.__setattr__(settings, "payment_secret_key", original_secret)
        object.__setattr__(settings, "payment_webhook_secret", original_webhook_secret)


def test_mercadopago_webhook_simulation_payment_updated_is_received_without_activation(monkeypatch) -> None:
    original_provider = settings.payment_provider
    original_access_token = settings.mercadopago_access_token
    original_public_key = settings.mercadopago_public_key
    original_webhook_secret = settings.mercadopago_webhook_secret
    object.__setattr__(settings, "payment_provider", "mercadopago")
    object.__setattr__(settings, "mercadopago_access_token", "unit-mercadopago-token-simulation")
    object.__setattr__(settings, "mercadopago_public_key", "unit-mercadopago-public-simulation")
    object.__setattr__(settings, "mercadopago_webhook_secret", "unit-mercadopago-webhook-simulation")
    monkeypatch.setattr(
        payment_service,
        "_fetch_mercadopago_payment",
        lambda data_id: pytest.fail("simulation must not call Mercado Pago API"),
    )
    try:
        with TestClient(app) as client:
            raw_body = json.dumps(
                {
                    "action": "payment.updated",
                    "api_version": "v1",
                    "data": {"id": "123456"},
                    "date_created": "2021-11-01T02:02:02Z",
                    "id": "123456",
                    "live_mode": False,
                    "type": "payment",
                    "user_id": 251156592,
                },
                separators=(",", ":"),
            ).encode("utf-8")

            response = client.post("/subscriptions/mercadopago/webhook", content=raw_body)
            assert response.status_code == 200
            body = response.json()
            assert body["status"] == "received_simulation"
            assert body["activation"]["activated"] is False
            assert body["activation"]["ignored"] is True
            assert body["activation"]["reason"] == "mercadopago_simulation_no_activation"

            duplicate = client.post("/subscriptions/mercadopago/webhook", content=raw_body)
            assert duplicate.status_code == 200
            assert duplicate.json()["status"] == "duplicate"
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "mercadopago_access_token", original_access_token)
        object.__setattr__(settings, "mercadopago_public_key", original_public_key)
        object.__setattr__(settings, "mercadopago_webhook_secret", original_webhook_secret)


def test_mercadopago_webhook_real_payment_missing_signature_is_forbidden() -> None:
    original_provider = settings.payment_provider
    original_access_token = settings.mercadopago_access_token
    original_public_key = settings.mercadopago_public_key
    original_webhook_secret = settings.mercadopago_webhook_secret
    object.__setattr__(settings, "payment_provider", "mercadopago")
    object.__setattr__(settings, "mercadopago_access_token", "unit-mercadopago-token-missing-signature")
    object.__setattr__(settings, "mercadopago_public_key", "unit-mercadopago-public-missing-signature")
    object.__setattr__(settings, "mercadopago_webhook_secret", "unit-mercadopago-webhook-missing-signature")
    try:
        with TestClient(app) as client:
            raw_body = json.dumps(
                {
                    "id": "payment-real-missing-signature",
                    "type": "payment",
                    "action": "payment.updated",
                    "live_mode": True,
                    "data": {"id": "payment-real-missing-signature"},
                },
                separators=(",", ":"),
            ).encode("utf-8")

            response = client.post("/subscriptions/mercadopago/webhook", content=raw_body)
            assert response.status_code == 403
            assert response.json()["detail"]["error"] == "mercadopago_signature_missing"
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "mercadopago_access_token", original_access_token)
        object.__setattr__(settings, "mercadopago_public_key", original_public_key)
        object.__setattr__(settings, "mercadopago_webhook_secret", original_webhook_secret)


def test_mercadopago_webhook_provider_error_is_controlled_without_502(monkeypatch) -> None:
    original_provider = settings.payment_provider
    original_access_token = settings.mercadopago_access_token
    original_public_key = settings.mercadopago_public_key
    original_webhook_secret = settings.mercadopago_webhook_secret
    webhook_secret = "unit-mercadopago-webhook-provider-error"
    object.__setattr__(settings, "payment_provider", "mercadopago")
    object.__setattr__(settings, "mercadopago_access_token", "unit-mercadopago-token-provider-error")
    object.__setattr__(settings, "mercadopago_public_key", "unit-mercadopago-public-provider-error")
    object.__setattr__(settings, "mercadopago_webhook_secret", webhook_secret)
    monkeypatch.setattr(
        payment_service,
        "_fetch_mercadopago_payment",
        lambda data_id: (_ for _ in ()).throw(
            HTTPException(
                status_code=502,
                detail={"error": "payment_provider_error", "provider_status": 404},
            )
        ),
    )
    try:
        with TestClient(app) as client:
            payment_id = f"missing-payment-{uuid.uuid4().hex}"
            raw_body = json.dumps(
                {
                    "id": payment_id,
                    "type": "payment",
                    "action": "payment.updated",
                    "live_mode": True,
                    "data": {"id": payment_id},
                },
                separators=(",", ":"),
            ).encode("utf-8")
            request_id = str(uuid.uuid4())

            response = client.post(
                "/subscriptions/mercadopago/webhook",
                content=raw_body,
                headers={
                    "x-request-id": request_id,
                    "x-signature": mercadopago_signature(payment_id, request_id, webhook_secret),
                },
            )
            assert response.status_code == 200
            body = response.json()
            assert body["status"] == "provider_error"
            assert body["activation"]["activated"] is False
            assert body["activation"]["ignored"] is True
            assert body["activation"]["provider_status"] == 404
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "mercadopago_access_token", original_access_token)
        object.__setattr__(settings, "mercadopago_public_key", original_public_key)
        object.__setattr__(settings, "mercadopago_webhook_secret", original_webhook_secret)


def test_mercadopago_webhook_approved_payment_event_activates_once(monkeypatch) -> None:
    original_provider = settings.payment_provider
    original_access_token = settings.mercadopago_access_token
    original_public_key = settings.mercadopago_public_key
    original_webhook_secret = settings.mercadopago_webhook_secret
    webhook_secret = "unit-mercadopago-webhook-payment-approved"
    object.__setattr__(settings, "payment_provider", "mercadopago")
    object.__setattr__(settings, "mercadopago_access_token", "unit-mercadopago-token-payment-approved")
    object.__setattr__(settings, "mercadopago_public_key", "unit-mercadopago-public-payment-approved")
    object.__setattr__(settings, "mercadopago_webhook_secret", webhook_secret)
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            created = client.post(
                "/onboarding/tenants",
                json={
                    "tenant_name": f"Mercado Pago Payment Approved {unique}",
                    "admin_username": f"mp_payment_{unique}@example.com",
                    "admin_password": "checkout-pass-123",
                    "plan": "mype",
                    "ruc": f"217{unique}",
                    "razon_social": f"Mercado Pago Payment SAC {unique}",
                    "trial_requested": False,
                },
            )
            assert created.status_code == 200
            tenant_id = created.json()["tenant_id"]
            headers = verified_headers(client, f"mp_payment_{unique}@example.com", "checkout-pass-123")
            me = client.get("/auth/me", headers=headers).json()
            preapproval_id = f"preapproval-{uuid.uuid4().hex}"
            checkout_record = asyncio.run(
                repositories.create_checkout_session_record(
                    tenant_id=tenant_id,
                    user_id=me["user_id"],
                    plan="premium",
                    billing_cycle="annual",
                    provider="mercadopago",
                    provider_session_id=preapproval_id,
                    checkout_url="https://www.mercadopago.com.pe/subscriptions/checkout",
                    amount_cents=199000,
                    currency="PEN",
                    status="pending",
                    metadata={"provider_status": "created", "checkout_mode": "preapproval"},
                )
            )
            payment_id = f"payment-{uuid.uuid4().hex}"
            monkeypatch.setattr(
                payment_service,
                "_fetch_mercadopago_payment",
                lambda data_id: {
                    "id": data_id,
                    "status": "approved",
                    "status_detail": "accredited",
                    "preapproval_id": preapproval_id,
                    "external_reference": checkout_record["id"],
                    "currency_id": "PEN",
                    "transaction_amount": "1990.00",
                    "date_approved": "2026-06-08T12:00:00.000-05:00",
                    "payer": {"id": "payer-unit"},
                    "metadata": {"plan": "premium", "billing_cycle": "annual"},
                },
            )
            raw_body = json.dumps(
                {
                    "id": payment_id,
                    "type": "payment",
                    "action": "payment.updated",
                    "live_mode": True,
                    "data": {"id": payment_id},
                },
                separators=(",", ":"),
            ).encode("utf-8")
            request_id = str(uuid.uuid4())

            response = client.post(
                "/subscriptions/mercadopago/webhook",
                content=raw_body,
                headers={
                    "x-request-id": request_id,
                    "x-signature": mercadopago_signature(payment_id, request_id, webhook_secret),
                },
            )
            assert response.status_code == 200
            assert response.json()["status"] == "processed"
            assert response.json()["activation"]["provider"] == "mercadopago"
            assert response.json()["activation"]["plan"] == "premium"
            assert response.json()["activation"]["billing_cycle"] == "annual"

            duplicate = client.post(
                "/subscriptions/mercadopago/webhook",
                content=raw_body,
                headers={
                    "x-request-id": request_id,
                    "x-signature": mercadopago_signature(payment_id, request_id, webhook_secret),
                },
            )
            assert duplicate.status_code == 200
            assert duplicate.json()["status"] == "duplicate"

            current = client.get("/subscriptions/current", headers=headers)
            assert current.status_code == 200
            assert current.json()["id"] == "premium"
            assert current.json()["status"] == "active"
            assert current.json()["provider"] == "mercadopago"
            assert current.json()["billing_cycle"] == "annual"
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "mercadopago_access_token", original_access_token)
        object.__setattr__(settings, "mercadopago_public_key", original_public_key)
        object.__setattr__(settings, "mercadopago_webhook_secret", original_webhook_secret)


@pytest.mark.parametrize(
    ("plan", "billing_cycle", "amount_cents", "amount_value", "expected_interval"),
    [
        ("mype", "monthly", 8900, "89.00", "monthly"),
        ("mype", "annual", 89000, "890.00", "yearly"),
        ("premium", "monthly", 19900, "199.00", "monthly"),
        ("premium", "annual", 199000, "1990.00", "yearly"),
    ],
)
def test_mercadopago_webhook_approved_payment_activates_each_commercial_plan_cycle(
    monkeypatch,
    plan: str,
    billing_cycle: str,
    amount_cents: int,
    amount_value: str,
    expected_interval: str,
) -> None:
    original_provider = settings.payment_provider
    original_access_token = settings.mercadopago_access_token
    original_public_key = settings.mercadopago_public_key
    original_webhook_secret = settings.mercadopago_webhook_secret
    webhook_secret = f"unit-mercadopago-webhook-{plan}-{billing_cycle}"
    object.__setattr__(settings, "payment_provider", "mercadopago")
    object.__setattr__(settings, "mercadopago_access_token", f"unit-mercadopago-token-{plan}-{billing_cycle}")
    object.__setattr__(settings, "mercadopago_public_key", f"unit-mercadopago-public-{plan}-{billing_cycle}")
    object.__setattr__(settings, "mercadopago_webhook_secret", webhook_secret)
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            created = client.post(
                "/onboarding/tenants",
                json={
                    "tenant_name": f"Mercado Pago {plan} {billing_cycle} {unique}",
                    "admin_username": f"mp_cycle_{unique}@example.com",
                    "admin_password": "checkout-pass-123",
                    "plan": "mype",
                    "ruc": f"218{unique}",
                    "razon_social": f"Mercado Pago Cycle SAC {unique}",
                    "trial_requested": False,
                },
            )
            assert created.status_code == 200
            tenant_id = created.json()["tenant_id"]
            headers = verified_headers(client, f"mp_cycle_{unique}@example.com", "checkout-pass-123")
            me = client.get("/auth/me", headers=headers).json()
            preapproval_id = f"preapproval-{uuid.uuid4().hex}"
            checkout_record = asyncio.run(
                repositories.create_checkout_session_record(
                    tenant_id=tenant_id,
                    user_id=me["user_id"],
                    plan=plan,
                    billing_cycle=billing_cycle,
                    provider="mercadopago",
                    provider_session_id=preapproval_id,
                    checkout_url="https://www.mercadopago.com.pe/subscriptions/checkout",
                    amount_cents=amount_cents,
                    currency="PEN",
                    status="pending",
                    metadata={"provider_status": "created", "checkout_mode": "preapproval"},
                )
            )
            authorized_payment_id = f"authpay-{uuid.uuid4().hex}"
            monkeypatch.setattr(
                payment_service,
                "_fetch_mercadopago_authorized_payment",
                lambda data_id: {
                    "id": data_id,
                    "preapproval_id": preapproval_id,
                    "external_reference": checkout_record["id"],
                    "currency_id": "PEN",
                    "transaction_amount": amount_value,
                    "debit_date": "2026-06-08T12:00:00.000-05:00",
                    "payer_id": "payer-unit",
                    "payment": {"id": "payment-unit", "status": "approved", "status_detail": "accredited"},
                },
            )
            raw_body = json.dumps(
                {
                    "id": authorized_payment_id,
                    "type": "subscription_authorized_payment",
                    "action": "subscription_authorized_payment.updated",
                    "data": {"id": authorized_payment_id},
                },
                separators=(",", ":"),
            ).encode("utf-8")
            request_id = str(uuid.uuid4())

            response = client.post(
                f"/subscriptions/mercadopago/webhook?data.id={authorized_payment_id}&type=subscription_authorized_payment",
                content=raw_body,
                headers={
                    "x-request-id": request_id,
                    "x-signature": mercadopago_signature(authorized_payment_id, request_id, webhook_secret),
                },
            )
            assert response.status_code == 200
            assert response.json()["status"] == "processed"
            assert response.json()["activation"]["plan"] == plan
            assert response.json()["activation"]["billing_cycle"] == billing_cycle
            assert response.json()["activation"]["provider"] == "mercadopago"
            assert response.json()["activation"]["amount_cents"] == amount_cents

            current = client.get("/subscriptions/current", headers=headers)
            assert current.status_code == 200
            assert current.json()["id"] == plan
            assert current.json()["status"] == "active"
            assert current.json()["provider"] == "mercadopago"
            assert current.json()["billing_cycle"] == billing_cycle
            assert current.json()["interval"] == expected_interval

            status_response = client.get("/subscriptions/status", headers=headers)
            assert status_response.status_code == 200
            status_body = status_response.json()
            assert status_body["plan"] == plan
            assert status_body["provider"] == "mercadopago"
            assert status_body["payment_status"] == "paid"
            assert status_body["checkout"]["status"] == "paid"

            duplicate = client.post(
                f"/subscriptions/mercadopago/webhook?data.id={authorized_payment_id}&type=subscription_authorized_payment",
                content=raw_body,
                headers={
                    "x-request-id": request_id,
                    "x-signature": mercadopago_signature(authorized_payment_id, request_id, webhook_secret),
                },
            )
            assert duplicate.status_code == 200
            assert duplicate.json()["status"] == "duplicate"
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "mercadopago_access_token", original_access_token)
        object.__setattr__(settings, "mercadopago_public_key", original_public_key)
        object.__setattr__(settings, "mercadopago_webhook_secret", original_webhook_secret)


def test_mercadopago_webhook_invalid_signature_and_not_approved_do_not_activate(monkeypatch) -> None:
    original_provider = settings.payment_provider
    original_access_token = settings.mercadopago_access_token
    original_public_key = settings.mercadopago_public_key
    original_webhook_secret = settings.mercadopago_webhook_secret
    webhook_secret = "unit-mercadopago-webhook-invalid"
    object.__setattr__(settings, "payment_provider", "mercadopago")
    object.__setattr__(settings, "mercadopago_access_token", "unit-mercadopago-token-invalid")
    object.__setattr__(settings, "mercadopago_public_key", "unit-mercadopago-public-invalid")
    object.__setattr__(settings, "mercadopago_webhook_secret", webhook_secret)
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            created = client.post(
                "/onboarding/tenants",
                json={
                    "tenant_name": f"Mercado Pago Invalid {unique}",
                    "admin_username": f"mp_invalid_{unique}@example.com",
                    "admin_password": "checkout-pass-123",
                    "plan": "mype",
                    "ruc": f"219{unique}",
                    "razon_social": f"Mercado Pago Invalid SAC {unique}",
                    "trial_requested": False,
                },
            )
            assert created.status_code == 200
            tenant_id = created.json()["tenant_id"]
            headers = verified_headers(client, f"mp_invalid_{unique}@example.com", "checkout-pass-123")
            me = client.get("/auth/me", headers=headers).json()
            preapproval_id = f"preapproval-{uuid.uuid4().hex}"
            checkout_record = asyncio.run(
                repositories.create_checkout_session_record(
                    tenant_id=tenant_id,
                    user_id=me["user_id"],
                    plan="premium",
                    billing_cycle="monthly",
                    provider="mercadopago",
                    provider_session_id=preapproval_id,
                    checkout_url="https://www.mercadopago.com.pe/subscriptions/checkout",
                    amount_cents=19900,
                    currency="PEN",
                    status="pending",
                    metadata={"provider_status": "created", "checkout_mode": "preapproval"},
                )
            )
            authorized_payment_id = f"authpay-{uuid.uuid4().hex}"
            raw_body = json.dumps(
                {
                    "id": authorized_payment_id,
                    "type": "subscription_authorized_payment",
                    "action": "subscription_authorized_payment.updated",
                    "data": {"id": authorized_payment_id},
                },
                separators=(",", ":"),
            ).encode("utf-8")
            request_id = str(uuid.uuid4())

            invalid_signature = client.post(
                f"/subscriptions/mercadopago/webhook?data.id={authorized_payment_id}&type=subscription_authorized_payment",
                content=raw_body,
                headers={
                    "x-request-id": request_id,
                    "x-signature": mercadopago_signature(authorized_payment_id, request_id, "wrong-mercadopago-webhook"),
                },
            )
            assert invalid_signature.status_code == 403

            monkeypatch.setattr(
                payment_service,
                "_fetch_mercadopago_authorized_payment",
                lambda data_id: {
                    "id": data_id,
                    "preapproval_id": preapproval_id,
                    "external_reference": checkout_record["id"],
                    "currency_id": "PEN",
                    "transaction_amount": "199.00",
                    "payment": {"id": "payment-unit", "status": "rejected", "status_detail": "cc_rejected"},
                },
            )
            not_approved = client.post(
                f"/subscriptions/mercadopago/webhook?data.id={authorized_payment_id}&type=subscription_authorized_payment",
                content=raw_body,
                headers={
                    "x-request-id": request_id,
                    "x-signature": mercadopago_signature(authorized_payment_id, request_id, webhook_secret),
                },
            )
            assert not_approved.status_code == 200
            assert not_approved.json()["status"] == "ignored"

            current = client.get("/subscriptions/current", headers=headers)
            assert current.status_code == 200
            assert current.json()["id"] == "mype"
            assert current.json()["provider"] is None
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "mercadopago_access_token", original_access_token)
        object.__setattr__(settings, "mercadopago_public_key", original_public_key)
        object.__setattr__(settings, "mercadopago_webhook_secret", original_webhook_secret)


def test_company_sunat_access_uses_minimal_fields_and_keeps_subscription_pending_when_payment_missing() -> None:
    original_provider = settings.payment_provider
    original_access_token = settings.mercadopago_access_token
    original_public_key = settings.mercadopago_public_key
    original_webhook_secret = settings.mercadopago_webhook_secret
    object.__setattr__(settings, "payment_provider", "mercadopago")
    object.__setattr__(settings, "mercadopago_access_token", "")
    object.__setattr__(settings, "mercadopago_public_key", "")
    object.__setattr__(settings, "mercadopago_webhook_secret", "")
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            response = client.post(
                "/onboarding/company-sunat-access",
                json={
                    "ruc": f"205{unique}",
                    "sunat_username": f"aux_{unique}",
                    "sunat_password": "sunat-aux-pass-123",
                    "consent_accepted": True,
                    "plan": "mype",
                    "billing_cycle": "monthly",
                },
            )

            assert response.status_code == 200
            body = response.json()
            assert body["plan_requested"] == "mype"
            assert body["billing_cycle"] == "monthly"
            assert body["subscription_status"] == "pending_payment"
            assert body["checkout_url"] is None
            assert body["payment"]["provider"] == "mercadopago"
            assert body["payment"]["payment_provider_missing"] is True
            assert "Pago pendiente de configuración" in body["message"]
            assert body["company"]["razon_social"] == "Razón social pendiente de validación"
            assert body["sunat_credential"]["read_only"] is True
            assert body["sunat_credential"]["remote_actions_enabled"] is False
            assert body["sunat_credential"]["real_connector_enabled"] is False
            assert body["sunat_credential"]["real_sunat_session"] is False

            headers = {"Authorization": f"Bearer {body['access_token']}"}
            status_response = client.get("/subscriptions/status", headers=headers)
            assert status_response.status_code == 200
            assert status_response.json()["status"] == "pending"
            assert status_response.json()["plan_effective"] == "free"
            assert status_response.json()["payment_required"] is True
            assert status_response.json()["premium"] is False

            blocked_document = client.post(
                "/documents/ingest",
                headers=headers,
                json={"filename": "empresa-pendiente.pdf", "content_type": "application/pdf", "size_bytes": 128},
            )
            assert blocked_document.status_code == 402
            assert blocked_document.json()["detail"]["error"] == "subscription_not_active"

            companies = client.get("/identity/companies", headers=headers)
            assert companies.status_code == 200
            assert companies.json()[0]["ruc"] == f"205{unique}"

            credential = asyncio.run(latest_sunat_credential(body["tenant_id"], body["company"]["id"], body["workspace"]["id"]))
            assert credential is not None
            assert credential.read_only is True
            assert credential.remote_actions_enabled is False
            assert credential.sunat_password_encrypted
            assert credential.sunat_password_encrypted != "sunat-aux-pass-123"
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "mercadopago_access_token", original_access_token)
        object.__setattr__(settings, "mercadopago_public_key", original_public_key)
        object.__setattr__(settings, "mercadopago_webhook_secret", original_webhook_secret)


def test_company_sunat_access_creates_mercadopago_checkout_without_activating_plan(monkeypatch) -> None:
    original_provider = settings.payment_provider
    original_access_token = settings.mercadopago_access_token
    original_public_key = settings.mercadopago_public_key
    original_webhook_secret = settings.mercadopago_webhook_secret
    object.__setattr__(settings, "payment_provider", "mercadopago")
    object.__setattr__(settings, "mercadopago_access_token", "unit-mercadopago-token")
    object.__setattr__(settings, "mercadopago_public_key", "unit-mercadopago-public")
    object.__setattr__(settings, "mercadopago_webhook_secret", "unit-mercadopago-webhook")
    monkeypatch.setattr(
        payment_service,
        "_create_mercadopago_checkout",
        lambda *args, **kwargs: {
            "id": "preapproval-company-flow",
            "init_point": "https://www.mercadopago.com.pe/subscriptions/company-flow",
        },
    )
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            response = client.post(
                "/onboarding/company-sunat-access",
                json={
                    "ruc": f"206{unique}",
                    "sunat_username": f"aux_{unique}",
                    "sunat_password": "sunat-aux-pass-123",
                    "consent_accepted": True,
                    "plan": "premium",
                    "billing_cycle": "annual",
                },
            )

            assert response.status_code == 200
            body = response.json()
            assert body["checkout_url"] == "https://www.mercadopago.com.pe/subscriptions/company-flow"
            assert body["payment"]["checkout"]["provider"] == "mercadopago"
            assert body["payment"]["checkout"]["status"] == "pending"
            assert body["payment"]["checkout"]["plan"] == "premium"
            assert body["payment"]["checkout"]["billing_cycle"] == "annual"

            headers = {"Authorization": f"Bearer {body['access_token']}"}
            subscription_status = client.get("/subscriptions/status", headers=headers)
            assert subscription_status.status_code == 200
            status_body = subscription_status.json()
            assert status_body["status"] == "pending"
            assert status_body["plan_effective"] == "free"
            assert status_body["payment_status"] == "pending"
            assert status_body["payment_required"] is True
            assert status_body["premium"] is False
            assert status_body["checkout"]["provider"] == "mercadopago"
            assert status_body["checkout"]["status"] == "pending"
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "mercadopago_access_token", original_access_token)
        object.__setattr__(settings, "mercadopago_public_key", original_public_key)
        object.__setattr__(settings, "mercadopago_webhook_secret", original_webhook_secret)


def test_existing_company_sunat_status_and_update_reuse_company_without_ruc_exists() -> None:
    original_provider = settings.payment_provider
    original_access_token = settings.mercadopago_access_token
    original_public_key = settings.mercadopago_public_key
    original_webhook_secret = settings.mercadopago_webhook_secret
    object.__setattr__(settings, "payment_provider", "mercadopago")
    object.__setattr__(settings, "mercadopago_access_token", "")
    object.__setattr__(settings, "mercadopago_public_key", "")
    object.__setattr__(settings, "mercadopago_webhook_secret", "")
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            ruc = f"208{unique}"
            first_username = f"aux_{unique}"
            updated_username = f"aux_new_{unique}"
            created = client.post(
                "/onboarding/company-sunat-access",
                json={
                    "ruc": ruc,
                    "sunat_username": first_username,
                    "sunat_password": "sunat-aux-pass-123",
                    "consent_accepted": True,
                    "plan": "mype",
                    "billing_cycle": "monthly",
                },
            )
            assert created.status_code == 200
            created_body = created.json()
            company_id = created_body["company"]["id"]

            status_response = client.get("/onboarding/company-sunat-access/status", params={"ruc": ruc})
            assert status_response.status_code == 200
            status_body = status_response.json()
            assert status_body["exists"] is True
            assert status_body["ruc"] == ruc
            assert status_body["usuario_sol_masked"]
            assert status_body["usuario_sol_masked"] != first_username
            assert status_body["has_sunat_connection"] is True
            assert status_body["subscription_status"] == "pending"
            assert status_body["can_continue"] is True
            assert status_body["can_update_sol"] is True
            assert status_body["can_checkout"] is True

            updated = client.post(
                "/onboarding/company-sunat-access",
                json={
                    "ruc": ruc,
                    "sunat_username": updated_username,
                    "sunat_password": "sunat-aux-pass-456",
                    "consent_accepted": True,
                    "plan": "mype",
                    "billing_cycle": "monthly",
                },
            )
            assert updated.status_code == 200
            updated_body = updated.json()
            assert updated_body["existing_company"] is True
            assert updated_body["company"]["id"] == company_id
            assert updated_body["ruc_status"]["usuario_sol_masked"]
            assert updated_body["ruc_status"]["usuario_sol_masked"] != updated_username
            assert updated_body["subscription_status"] == "pending_payment"
            assert asyncio.run(count_companies_by_ruc(ruc)) == 1

            serialized = json.dumps(updated_body)
            assert "ruc_exists" not in serialized
            assert "sunat_password" not in serialized
            assert "sunat_username_encrypted" not in serialized
            assert "sunat-aux-pass-123" not in serialized
            assert "sunat-aux-pass-456" not in serialized
            assert updated_username not in serialized
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "mercadopago_access_token", original_access_token)
        object.__setattr__(settings, "mercadopago_public_key", original_public_key)
        object.__setattr__(settings, "mercadopago_webhook_secret", original_webhook_secret)


def test_existing_company_continue_requires_usuario_sol_and_opens_pending_checkout(monkeypatch) -> None:
    original_provider = settings.payment_provider
    original_access_token = settings.mercadopago_access_token
    original_public_key = settings.mercadopago_public_key
    original_webhook_secret = settings.mercadopago_webhook_secret
    object.__setattr__(settings, "payment_provider", "mercadopago")
    object.__setattr__(settings, "mercadopago_access_token", "unit-mercadopago-token")
    object.__setattr__(settings, "mercadopago_public_key", "unit-mercadopago-public")
    object.__setattr__(settings, "mercadopago_webhook_secret", "unit-mercadopago-webhook")
    monkeypatch.setattr(
        payment_service,
        "_create_mercadopago_checkout",
        lambda *args, **kwargs: {
            "id": "preapproval-existing-ruc",
            "init_point": "https://www.mercadopago.com.pe/subscriptions/existing-ruc",
        },
    )
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            ruc = f"209{unique}"
            sunat_username = f"aux_{unique}"
            created = client.post(
                "/onboarding/company-sunat-access",
                json={
                    "ruc": ruc,
                    "sunat_username": sunat_username,
                    "sunat_password": "sunat-aux-pass-123",
                    "consent_accepted": True,
                    "plan": "premium",
                    "billing_cycle": "annual",
                },
            )
            assert created.status_code == 200

            mismatch = client.post(
                "/onboarding/company-sunat-access/continue",
                json={
                    "ruc": ruc,
                    "sunat_username": f"other_{unique}",
                    "plan": "premium",
                    "billing_cycle": "annual",
                },
            )
            assert mismatch.status_code == 403
            assert mismatch.json()["detail"]["error"] == "usuario_sol_mismatch"

            continued = client.post(
                "/onboarding/company-sunat-access/continue",
                json={
                    "ruc": ruc,
                    "sunat_username": sunat_username,
                    "plan": "premium",
                    "billing_cycle": "annual",
                },
            )
            assert continued.status_code == 200
            continued_body = continued.json()
            assert continued_body["existing_company"] is True
            assert continued_body["access_token"]
            assert continued_body["subscription_status"] == "pending_payment"
            assert continued_body["checkout_url"] == "https://www.mercadopago.com.pe/subscriptions/existing-ruc"
            assert continued_body["payment"]["checkout"]["status"] == "pending"
            assert continued_body["payment"]["checkout"]["plan"] == "premium"
            assert continued_body["sunat_credential"]["sunat_username_masked"]
            assert asyncio.run(count_companies_by_ruc(ruc)) == 1

            serialized = json.dumps(continued_body)
            assert "sunat_password" not in serialized
            assert "sunat-aux-pass-123" not in serialized
            assert "sunat_username_encrypted" not in serialized
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "mercadopago_access_token", original_access_token)
        object.__setattr__(settings, "mercadopago_public_key", original_public_key)
        object.__setattr__(settings, "mercadopago_webhook_secret", original_webhook_secret)


def test_existing_company_continue_enters_dashboard_when_plan_is_active() -> None:
    original_provider = settings.payment_provider
    original_access_token = settings.mercadopago_access_token
    original_public_key = settings.mercadopago_public_key
    original_webhook_secret = settings.mercadopago_webhook_secret
    object.__setattr__(settings, "payment_provider", "mercadopago")
    object.__setattr__(settings, "mercadopago_access_token", "")
    object.__setattr__(settings, "mercadopago_public_key", "")
    object.__setattr__(settings, "mercadopago_webhook_secret", "")
    try:
        with TestClient(app) as client:
            unique = uuid.uuid4().hex[:8]
            ruc = f"210{unique}"
            sunat_username = f"aux_{unique}"
            created = client.post(
                "/onboarding/company-sunat-access",
                json={
                    "ruc": ruc,
                    "sunat_username": sunat_username,
                    "sunat_password": "sunat-aux-pass-123",
                    "consent_accepted": True,
                    "plan": "mype",
                    "billing_cycle": "monthly",
                },
            )
            assert created.status_code == 200
            tenant_id = created.json()["tenant_id"]
            asyncio.run(repositories.update_tenant_subscription(tenant_id, "mype", subscription_service.limits_for("mype")))

            continued = client.post(
                "/onboarding/company-sunat-access/continue",
                json={
                    "ruc": ruc,
                    "sunat_username": sunat_username,
                    "plan": "mype",
                    "billing_cycle": "monthly",
                },
            )
            assert continued.status_code == 200
            continued_body = continued.json()
            assert continued_body["existing_company"] is True
            assert continued_body["subscription_status"] == "active"
            assert continued_body["checkout_url"] is None
            assert continued_body["ruc_status"]["subscription_status"] == "active"
            assert continued_body["access_token"]
    finally:
        object.__setattr__(settings, "payment_provider", original_provider)
        object.__setattr__(settings, "mercadopago_access_token", original_access_token)
        object.__setattr__(settings, "mercadopago_public_key", original_public_key)
        object.__setattr__(settings, "mercadopago_webhook_secret", original_webhook_secret)


def test_expired_subscription_blocks_company_actions_without_deleting_history() -> None:
    with TestClient(app) as client:
        unique = uuid.uuid4().hex[:8]
        username = f"expired_company_{unique}@example.com"
        password = "test-expired-pass-123"
        created = client.post(
            "/onboarding/tenants",
            json={
                "tenant_name": f"Expired Company {unique}",
                "admin_username": username,
                "admin_password": password,
                "plan": "premium",
                "ruc": f"207{unique}",
                "razon_social": f"Expired Company SAC {unique}",
                "trial_requested": False,
            },
        )
        assert created.status_code == 200
        tenant_id = created.json()["tenant_id"]
        headers = verified_headers(client, username, password)
        document = client.post(
            "/documents/ingest",
            headers=headers,
            json={"filename": "historial.pdf", "content_type": "application/pdf", "size_bytes": 256},
        )
        assert document.status_code == 200

        asyncio.run(expire_latest_subscription(tenant_id))

        status_response = client.get("/subscriptions/status", headers=headers)
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "expired"
        assert status_response.json()["plan_effective"] == "free"

        blocked_document = client.post(
            "/documents/ingest",
            headers=headers,
            json={"filename": "nuevo.pdf", "content_type": "application/pdf", "size_bytes": 256},
        )
        assert blocked_document.status_code == 402
        assert blocked_document.json()["detail"]["error"] == "subscription_not_active"

        documents = client.get("/documents", headers=headers)
        assert documents.status_code == 200
        assert any(item["metadata"]["filename"] == "historial.pdf" for item in documents.json())


def test_frontend_payment_ctas_hide_pay_buttons_when_provider_missing() -> None:
    frontend_source = Path("apps/frontend/src/App.tsx").read_text(encoding="utf-8")

    assert "const providerMissing = checkoutStatus?.payment_provider_missing ?? true;" in frontend_source
    assert "Pago pendiente de configuración." in frontend_source
    assert "Solicitar activación" in frontend_source
    assert "Pagar ahora" not in frontend_source
    assert "Pagar {plan.name} mensual" in frontend_source
    assert "Pagar {plan.name} anual" in frontend_source


def test_frontend_company_sunat_auxiliary_flow_keeps_required_copy() -> None:
    frontend_source = Path("apps/frontend/src/App.tsx").read_text(encoding="utf-8")

    for expected in [
        "Entrar como estudiante",
        "Entrar como empresa",
        "Usuario SOL",
        "Clave SOL",
        "Autorizo a DCFT a usar mi RUC, Usuario SOL y Clave SOL",
        "El acceso se guarda cifrado",
        "lectura SUNAT es solo consulta",
        "acciones irreversibles",
        "Solo lee información consultable autorizada",
        "Continuar con MYPE",
        "Continuar con Premium",
        "Mensual",
        "Anual",
        "S/ 890",
        "S/ 1,990",
        "Ver permisos SUNAT",
        "Este RUC ya tiene una cuenta empresarial en DCFT.",
        "Usuario SOL guardado:",
        "DCFT recuerda solo el Usuario SOL enmascarado",
        "Para continuar no necesitas ingresar Clave SOL.",
        "Continuar con este RUC",
        "Ir a pago pendiente",
        "Entrar al dashboard",
        "Actualizar acceso SOL",
        "Guardar acceso SOL",
        "/onboarding/company-sunat-access/status",
        "/onboarding/company-sunat-access/continue",
        "Razón social pendiente de validación",
        "Crear cuenta empresa",
        "Ver seguridad",
        "Desconectar SUNAT",
        "Consulta contable/tributaria mÃ­nima conectada al proveedor IA configurable de DCFT.",
        "/ai/tax/ask",
        "Premium operativo sin pago",
        "Mercado Pago no requerido para esta cuenta interna protegida.",
        "Esperando datos autorizados para diagnóstico completo.",
    ]:
        assert expected in frontend_source
    for legacy_required_field in [
        "Completa RUC, razon social, correo",
        "Correo empresarial",
        "Contraseña empresarial",
        "businessLoginForm.razon_social",
        "businessLoginForm.username",
        "businessLoginForm.password",
        "Usuario secundario SUNAT",
        "Clave secundaria SUNAT",
        "No uses tu Clave SOL principal",
        "409: ruc_exists",
        "Actualizar acceso SUNAT",
        "Puedes continuar con el acceso existente o actualizar la conexión SUNAT.",
        "localStorage.setItem(\"sunat_password\"",
        "localStorage.setItem('sunat_password'",
    ]:
        assert legacy_required_field not in frontend_source


def test_frontend_login_accepts_username_or_email_without_email_only_contract() -> None:
    frontend_source = Path("apps/frontend/src/App.tsx").read_text(encoding="utf-8")

    assert 'const loginIdentifier = username.trim();' in frontend_source
    assert 'username: loginIdentifier' in frontend_source
    assert 'aria-label={isAdmin ? "Usuario Admin CEO" : "Correo o usuario"}' in frontend_source
    assert 'placeholder={isAdmin ? "Usuario Admin CEO" : "Correo o usuario"}' in frontend_source
    assert 'autoComplete="username"' in frontend_source
    assert 'disabled={loading || !username.trim() || !password}' in frontend_source


def test_documents_and_ai_are_blocked_honestly_when_providers_disabled() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        document = client.post(
            "/documents/ingest",
            headers=headers,
            json={"filename": "../../factura-demo.pdf", "content_type": "application/pdf", "size_bytes": 128},
        )
        assert document.status_code == 200
        assert document.json()["ingestion"]["ocr_status"] == "placeholder_disabled"
        assert document.json()["document"]["metadata"]["filename"] == "factura-demo.pdf"

        ai_request = client.post(
            "/ai/requests",
            headers=headers,
            json={"objective": "analizar flujo de caja", "input_summary": "datos locales", "constraints": ["no external ai"]},
        )
        assert ai_request.status_code == 200
        assert ai_request.json()["status"] == "blocked_provider_disabled"


def test_knowledge_retrieval_searches_real_registries() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        search = client.get("/knowledge/search?q=SUNAT%20regulatory%20documents&limit=5", headers=headers)
        assert search.status_code == 200
        body = search.json()
        assert body["strategy"] == "lexical_token_overlap"
        assert body["candidate_count"] >= 5
        assert body["result_count"] >= 1
        assert any(result["source"] in {"knowledge_registry", "regulatory_registry"} for result in body["results"])
        assert any("sunat" in result["matched_terms"] or "regulatory" in result["matched_terms"] for result in body["results"])


def test_knowledge_embedding_search_returns_real_vectors() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        search = client.get("/knowledge/embedding-search?q=SUNAT%20tax%20documents&limit=5&dimensions=32", headers=headers)
        assert search.status_code == 200
        body = search.json()
        assert body["embedding_model"] == "local_hash_embedding_v1"
        assert body["embedding_dimensions"] == 32
        assert len(body["query_embedding"]) == 32
        assert any(abs(value) > 0 for value in body["query_embedding"])
        assert body["candidate_count"] >= 5
        assert body["result_count"] >= 1
        assert body["results"][0]["similarity"] > 0


def test_regulatory_datasets_feed_retrieval_and_embeddings() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        lexical = client.get("/knowledge/search?q=UIT%205500%20SUNAT&limit=10", headers=headers)
        assert lexical.status_code == 200
        assert any(result["source"] == "regulatory_dataset" for result in lexical.json()["results"])

        embedding = client.get("/knowledge/embedding-search?q=UIT%205500%20SUNAT&limit=10&dimensions=32", headers=headers)
        assert embedding.status_code == 200
        assert any(result["source"] == "regulatory_dataset" for result in embedding.json()["results"])


def test_memory_records_are_persisted_and_retrievable() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        record = client.post(
            "/memory/records",
            headers=headers,
            json={
                "memory_type": "operational",
                "title": "Bloqueo SUNAT validado",
                "content": "La prioridad operativa es revisar una esquela SUNAT antes del cierre mensual.",
                "tags": ["sunat", "cierre"],
                "source": "test",
            },
        )
        assert record.status_code == 200
        assert record.json()["memory_type"] == "operational"

        listed = client.get("/memory/records?limit=10", headers=headers)
        assert listed.status_code == 200
        assert any(item["id"] == record.json()["id"] for item in listed.json())

        search = client.get("/knowledge/search?q=esquela%20SUNAT%20cierre&limit=10", headers=headers)
        assert search.status_code == 200
        assert any(result["source"] == "tenant_memory" and result["source_id"] == record.json()["id"] for result in search.json()["results"])

        embedding = client.get("/knowledge/embedding-search?q=esquela%20SUNAT%20cierre&limit=10&dimensions=32", headers=headers)
        assert embedding.status_code == 200
        assert any(result["source"] == "tenant_memory" and result["source_id"] == record.json()["id"] for result in embedding.json()["results"])


def test_recommendations_include_structured_explainability() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        recommendation = client.post(
            "/recommendations",
            headers=headers,
            json={
                "category": "tax",
                "objective": "Evaluar una esquela SUNAT",
                "facts": {"document_type": "sunat_notice", "amount": 1200, "deadline_days": 5},
            },
        )
        assert recommendation.status_code == 200
        explainability = recommendation.json()["explainability"]
        assert explainability["method"] == "deterministic_rules_no_external_ai"
        assert explainability["rule_id"] == "tax_review_before_official_action_v1"
        assert explainability["human_review_required"] is True
        assert explainability["confidence"] == "bounded_by_declared_facts"
        assert explainability["inputs_used"] == ["amount", "deadline_days", "document_type"]
        assert len(explainability["evidence"]) == 3
        assert "official_action_boundary" in explainability["decision_path"]


def test_governance_blocks_critical_and_double_approval_is_idempotent() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        critical = client.post(
            "/governance/approval-requests",
            headers=headers,
            json={"scope": "tax", "action": "presentar declaracion", "risk": "critical", "reason": "control test"},
        )
        assert critical.status_code == 200
        assert critical.json()["status"] == "blocked"
        decision = client.post(
            f"/governance/approval-requests/{critical.json()['id']}/decision",
            headers=headers,
            json={"decision": "approved", "reason": "not allowed"},
        )
        assert decision.status_code == 200
        assert decision.json()["status"] == "blocked"

        approval = client.post(
            "/governance/approval-requests",
            headers=headers,
            json={"scope": "workflow", "action": "advance controlled review", "risk": "high", "reason": "human approved"},
        )
        assert approval.status_code == 200
        approved = client.post(
            f"/governance/approval-requests/{approval.json()['id']}/decision",
            headers=headers,
            json={"decision": "approved", "reason": "controlled local test"},
        )
        replay = client.post(
            f"/governance/approval-requests/{approval.json()['id']}/decision",
            headers=headers,
            json={"decision": "rejected", "reason": "replay should not mutate"},
        )
        assert approved.status_code == 200
        assert replay.status_code == 200
        assert replay.json()["status"] == "approved"


def test_high_risk_workflow_requires_human_checkpoint_and_governance() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        approval = client.post(
            "/governance/approval-requests",
            headers=headers,
            json={"scope": "workflow", "action": "advance controlled review", "risk": "high", "reason": "human approved"},
        )
        approved = client.post(
            f"/governance/approval-requests/{approval.json()['id']}/decision",
            headers=headers,
            json={"decision": "approved", "reason": "controlled local test"},
        )
        workflow = client.post(
            "/workflows",
            headers=headers,
            json={"name": "Revision mensual", "objective": "validar datos", "steps": ["revisar", "reportar"], "risk": "high"},
        )
        assert workflow.status_code == 200
        blocked = client.post(f"/workflows/{workflow.json()['id']}/advance", headers=headers, json={})
        assert blocked.status_code == 200
        assert blocked.json()["status"] == "blocked"

        advanced = client.post(
            f"/workflows/{workflow.json()['id']}/advance",
            headers=headers,
            json={"checkpoint_acknowledged": True, "approval_request_id": approved.json()["id"], "note": "checkpoint reviewed"},
        )
        assert advanced.status_code == 200
        assert advanced.json()["status"] in {"running", "completed"}


def test_tax_workflow_templates_create_controlled_high_risk_workflows() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        templates = client.get("/tax-workflows/templates", headers=headers)
        assert templates.status_code == 200
        assert "sunat_notice_review" in templates.json()["templates"]

        workflow = client.post(
            "/tax-workflows",
            headers=headers,
            json={
                "workflow_type": "sunat_notice_review",
                "objective": "Revisar esquela SUNAT declarada por el usuario",
                "facts": {"document_type": "sunat_notice", "deadline_days": 5, "amount": 1200},
            },
        )
        assert workflow.status_code == 200
        body = workflow.json()
        assert body["risk"] == "high"
        assert body["tax_workflow_type"] == "sunat_notice_review"
        assert body["human_checkpoint_required"] is True
        assert "no_sunat_modification" in body["boundaries"]
        assert len(body["regulatory_queries"]) >= 1

        blocked = client.post(f"/workflows/{body['id']}/advance", headers=headers, json={})
        assert blocked.status_code == 200
        assert blocked.json()["status"] == "blocked"
        assert blocked.json()["audit_note"] == "human checkpoint required"


def test_heart_a1_domain_identity_enforces_ruc_workspace_permissions_and_context() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        unique = uuid.uuid4().hex[:8]

        permissions = client.get("/identity/permissions", headers=headers)
        assert permissions.status_code == 200
        assert permissions.json()["enforced_by_backend"] is True
        assert {"STUDENT", "PROFESSIONAL", "PREMIUM", "ADMIN"}.issubset(set(permissions.json()["roles"].keys()))
        assert {"FREE", "PROFESSIONAL", "PREMIUM"}.issubset(set(permissions.json()["plans"].keys()))

        company = client.post(
            "/identity/companies",
            headers=headers,
            json={
                "ruc": f"206{unique}",
                "razon_social": f"Empresa Heart A1 {unique}",
                "nombre_comercial": f"Heart {unique}",
                "regimen_tributario": "mype_tributario",
                "pais": "PE",
                "moneda": "PEN",
            },
        )
        assert company.status_code == 200
        company_id = company.json()["id"]
        assert company.json()["tenant_id"] == "local-demo"

        duplicate = client.post(
            "/identity/companies",
            headers=headers,
            json={
                "ruc": f"206{unique}",
                "razon_social": "Duplicada",
                "regimen_tributario": "general",
            },
        )
        assert duplicate.status_code == 409

        workspace = client.post(
            "/identity/workspaces",
            headers=headers,
            json={"nombre": f"Workspace Heart A1 {unique}", "empresa_id": company_id, "plan_id": "PROFESSIONAL"},
        )
        assert workspace.status_code == 200
        workspace_id = workspace.json()["id"]
        assert workspace.json()["propietario"] == "user-local-admin"

        selected_company = client.post("/identity/context/company", headers=headers, json={"company_id": company_id})
        assert selected_company.status_code == 200
        assert selected_company.json()["active_company_id"] == company_id

        selected_workspace = client.post("/identity/context/workspace", headers=headers, json={"workspace_id": workspace_id})
        assert selected_workspace.status_code == 200
        assert selected_workspace.json()["active_workspace_id"] == workspace_id
        assert selected_workspace.json()["active_company_id"] == company_id

        asyncio.run(create_test_user(f"heart_student_{unique}", "auditor", password="student-pass-123"))
        membership = client.post(
            f"/identity/workspaces/{workspace_id}/memberships",
            headers=headers,
            json={"user_id": f"user-heart_student_{unique}", "role_id": "STUDENT"},
        )
        assert membership.status_code == 200
        assert membership.json()["role_id"] == "STUDENT"

        student_login = client.post("/auth/login", json={"username": f"heart_student_{unique}", "password": "student-pass-123"})
        assert student_login.status_code == 200
        student_headers = {"Authorization": f"Bearer {student_login.json()['access_token']}"}
        assert client.get("/identity/workspaces", headers=student_headers).status_code == 200
        blocked_company_create = client.post(
            "/identity/companies",
            headers=student_headers,
            json={"ruc": f"207{unique}", "razon_social": "Bloqueada", "regimen_tributario": "general"},
        )
        assert blocked_company_create.status_code == 403

        other = client.post(
            "/onboarding/tenants",
            json={
                "tenant_name": f"Other Heart A1 {unique}",
                "admin_username": f"other_heart_{unique}",
                "admin_password": "other-admin-pass-123",
                "plan": "business_basic",
                "ruc": f"208{unique}",
                "razon_social": "Empresa Otro Tenant",
            },
        )
        assert other.status_code == 200
        other_headers = verified_headers(client, f"other_heart_{unique}", "other-admin-pass-123")
        other_company_id = other.json()["company"]["id"]

        local_companies = client.get("/identity/companies", headers=headers)
        assert local_companies.status_code == 200
        assert all(item["id"] != other_company_id for item in local_companies.json())

        cross_tenant_context = client.post(
            "/identity/context/company",
            headers=headers,
            json={"company_id": other_company_id},
        )
        assert cross_tenant_context.status_code == 404


def test_heart_a2_sunat_auxiliary_foundation_is_read_only_and_requires_consent() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        unique = uuid.uuid4().hex[:8]

        requirements = client.get("/sunat/auxiliary-access/requirements")
        assert requirements.status_code == 200
        assert "presentar_declaraciones" in requirements.json()["not_required_permissions"]
        assert requirements.json()["pilot_requirements"]["business_requires_sunat_auxiliary"] is False
        assert requirements.json()["pilot_requirements"]["principal_clave_sol_allowed"] is True
        assert requirements.json()["pilot_requirements"]["sol_credentials_allowed"] is True
        assert "usuario_sol" in requirements.json()["required_permissions"]
        assert "clave_sol" in requirements.json()["required_permissions"]
        assert "usuario_secundario_obligatorio" in requirements.json()["not_required_permissions"]
        assert requirements.json()["credential_security"]["credential_capture_enabled"] is True
        assert requirements.json()["credential_security"]["credential_storage_enabled"] is True
        assert requirements.json()["credential_security"]["encrypted_credential_storage"] is True
        assert requirements.json()["credential_security"]["password_fields_accepted"] is True

        classification = client.get("/sunat/data-classification")
        assert classification.status_code == 200
        assert "RUC" in classification.json()["CONSULTABLE"]
        assert "presentacion_de_formularios" in classification.json()["NO_CONSULTABLE"]
        assert classification.json()["remote_actions_enabled"] is False
        assert classification.json()["real_sunat_session"] is False
        assert classification.json()["pilot_requires_auxiliary_user"] is False
        assert classification.json()["sol_credentials_allowed"] is True
        assert classification.json()["commercial_credential_mode"] == "SUNAT_SOL_CREDENTIALS"
        assert classification.json()["credential_capture_enabled"] is True
        assert classification.json()["credential_storage_enabled"] is True

        company = client.post(
            "/identity/companies",
            headers=headers,
            json={
                "ruc": f"209{unique}",
                "razon_social": f"SUNAT Heart A2 {unique}",
                "nombre_comercial": f"SUNAT {unique}",
                "regimen_tributario": "mype_tributario",
            },
        )
        assert company.status_code == 200
        company_id = company.json()["id"]

        workspace = client.post(
            "/identity/workspaces",
            headers=headers,
            json={"nombre": f"Workspace SUNAT A2 {unique}", "empresa_id": company_id, "plan_id": "PROFESSIONAL"},
        )
        assert workspace.status_code == 200
        workspace_id = workspace.json()["id"]

        initial_status = client.get(f"/sunat/status?workspace_id={workspace_id}&empresa_id={company_id}", headers=headers)
        assert initial_status.status_code == 200
        assert initial_status.json()["status"] == "NOT_CONNECTED"
        assert initial_status.json()["pilot_requires_auxiliary_user"] is False
        assert initial_status.json()["sol_credentials_allowed"] is True
        assert initial_status.json()["commercial_credential_mode"] == "SUNAT_SOL_CREDENTIALS"
        assert initial_status.json()["credential_capture_enabled"] is True
        assert initial_status.json()["credential_storage_enabled"] is True
        assert initial_status.json()["remote_actions_enabled"] is False

        no_consent = client.post(
            "/sunat/connections/connect",
            headers=headers,
            json={"empresa_id": company_id, "workspace_id": workspace_id},
        )
        assert no_consent.status_code == 400
        assert no_consent.json()["detail"]["error"] == "explicit_sunat_consent_required"

        direct_secret = client.post(
            "/sunat/connections/connect",
            headers=headers,
            json={
                "empresa_id": company_id,
                "workspace_id": workspace_id,
                "clave_sol": "should-not-be-accepted",
                "consent_accepted": True,
                "auxiliary_user_acknowledged": True,
                "read_only_acknowledged": True,
                "no_tax_action_acknowledged": True,
            },
        )
        assert direct_secret.status_code == 422

        connected = client.post(
            "/sunat/connections/connect",
            headers=headers,
            json={
                "empresa_id": company_id,
                "workspace_id": workspace_id,
                "auxiliary_user_alias": "usuario-sol-consulta",
                "credential_reference": "vault/sunat/a2-test",
                "consent_accepted": True,
                "auxiliary_user_acknowledged": True,
                "read_only_acknowledged": True,
                "no_tax_action_acknowledged": True,
            },
        )
        assert connected.status_code == 200
        body = connected.json()
        connection_id = body["connection"]["id"]
        assert body["status"] == "CONNECTING"
        assert body["foundation_only"] is True
        assert body["real_connector_enabled"] is False
        assert body["connection"]["read_only"] is True
        assert body["connection"]["remote_actions_enabled"] is False
        assert "credential_reference" not in body["connection"]
        assert body["consent"]["accepted"] is True

        listed = client.get(f"/sunat/connections?workspace_id={workspace_id}&empresa_id={company_id}", headers=headers)
        assert listed.status_code == 200
        assert any(item["id"] == connection_id for item in listed.json())

        sync = client.post(
            f"/sunat/connections/{connection_id}/sync",
            headers=headers,
            json={"sync_scope": ["public_taxpayer_profile"]},
        )
        assert sync.status_code == 200
        assert sync.json()["sync_status"] == "NOT_EXECUTED_FOUNDATION_ONLY"
        assert sync.json()["last_sync_at_changed"] is False
        assert sync.json()["connection"]["last_sync_at"] is None

        asyncio.run(create_test_user(f"sunat_student_{unique}", "auditor", password="student-pass-123"))
        membership = client.post(
            f"/identity/workspaces/{workspace_id}/memberships",
            headers=headers,
            json={"user_id": f"user-sunat_student_{unique}", "role_id": "STUDENT"},
        )
        assert membership.status_code == 200
        student_login = client.post("/auth/login", json={"username": f"sunat_student_{unique}", "password": "student-pass-123"})
        assert student_login.status_code == 200
        student_headers = {"Authorization": f"Bearer {student_login.json()['access_token']}"}
        assert client.get(f"/sunat/status?workspace_id={workspace_id}&empresa_id={company_id}", headers=student_headers).status_code == 200
        blocked_student_connect = client.post(
            "/sunat/connections/connect",
            headers=student_headers,
            json={
                "empresa_id": company_id,
                "workspace_id": workspace_id,
                "consent_accepted": True,
                "auxiliary_user_acknowledged": True,
                "read_only_acknowledged": True,
                "no_tax_action_acknowledged": True,
            },
        )
        assert blocked_student_connect.status_code == 403

        disconnected = client.post(
            f"/sunat/connections/{connection_id}/disconnect",
            headers=headers,
            json={"reason": "validation_complete"},
        )
        assert disconnected.status_code == 200
        assert disconnected.json()["status"] == "DISABLED"
        assert disconnected.json()["connection"]["estado"] == "DISABLED"


def test_sunat_auxiliary_credentials_are_encrypted_masked_and_revocable() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        unique = uuid.uuid4().hex[:8]
        company = client.post(
            "/identity/companies",
            headers=headers,
            json={
                "ruc": f"210{unique}",
                "razon_social": f"Vault SUNAT {unique}",
                "regimen_tributario": "mype_tributario",
            },
        )
        assert company.status_code == 200
        company_id = company.json()["id"]

        workspace = client.post(
            "/identity/workspaces",
            headers=headers,
            json={"nombre": f"Workspace Vault {unique}", "empresa_id": company_id, "plan_id": "PREMIUM"},
        )
        assert workspace.status_code == 200
        workspace_id = workspace.json()["id"]

        payload = {
            "empresa_id": company_id,
            "workspace_id": workspace_id,
            "ruc": company.json()["ruc"],
            "sunat_username": f"auxvault_{unique}",
            "sunat_password": "clave-sol-test-123",
            "auxiliary_user_acknowledged": True,
            "read_only_acknowledged": True,
            "no_tax_action_acknowledged": True,
        }

        no_consent = client.post("/sunat/auxiliary/credentials", headers=headers, json=payload)
        assert no_consent.status_code == 400
        assert no_consent.json()["detail"]["error"] == "explicit_sunat_consent_required"

        stored = client.post("/sunat/auxiliary/credentials", headers=headers, json={**payload, "consent_accepted": True})
        assert stored.status_code == 200
        body = stored.json()
        assert body["status"] == "CREDENTIAL_RECEIVED"
        assert body["sunat_username_masked"] != payload["sunat_username"]
        assert "*" in body["sunat_username_masked"]
        assert body["read_only"] is True
        assert body["remote_actions_enabled"] is False
        assert body["real_sunat_session"] is False
        assert body["real_connector_enabled"] is False
        assert body["credential_storage_enabled"] is True
        assert body["sol_credentials_allowed"] is True
        assert body["commercial_credential_mode"] == "SUNAT_SOL_CREDENTIALS"
        assert "sunat_password" not in body
        assert "sunat_password_encrypted" not in body
        assert payload["sunat_username"] not in stored.text
        assert payload["sunat_password"] not in stored.text

        row = asyncio.run(latest_sunat_credential("local-demo", company_id, workspace_id))
        assert row is not None
        assert row.sunat_username_encrypted is not None
        assert row.sunat_password_encrypted is not None
        assert payload["sunat_username"] not in row.sunat_username_encrypted
        assert payload["sunat_password"] not in row.sunat_password_encrypted
        assert row.read_only is True
        assert row.remote_actions_enabled is False

        connections = client.get(f"/sunat/connections?workspace_id={workspace_id}&empresa_id={company_id}", headers=headers)
        assert connections.status_code == 200
        assert connections.json()[0]["auxiliary_user_alias"] == body["sunat_username_masked"]
        assert payload["sunat_username"] not in json.dumps(connections.json())
        assert payload["sunat_password"] not in json.dumps(connections.json())

        status_response = client.get(
            f"/sunat/auxiliary/status?workspace_id={workspace_id}&empresa_id={company_id}",
            headers=headers,
        )
        assert status_response.status_code == 200
        status_body = status_response.json()
        assert status_body["status"] == "CREDENTIAL_RECEIVED"
        assert status_body["sunat_username_masked"] != payload["sunat_username"]
        assert "*" in status_body["sunat_username_masked"]
        assert status_body["sol_credentials_allowed"] is True
        assert status_body["commercial_credential_mode"] == "SUNAT_SOL_CREDENTIALS"
        assert "sunat_password" not in status_body
        assert "sunat_password_encrypted" not in status_body
        assert payload["sunat_username"] not in status_response.text
        assert payload["sunat_password"] not in status_response.text

        other = client.post(
            "/onboarding/tenants",
            json={
                "tenant_name": f"Other Vault {unique}",
                "admin_username": f"other_vault_{unique}",
                "admin_password": "other-vault-pass-123",
                "plan": "mype",
                "ruc": f"211{unique}",
                "razon_social": "Otro Vault SAC",
            },
        )
        assert other.status_code == 200
        other_headers = verified_headers(client, f"other_vault_{unique}", "other-vault-pass-123")
        blocked = client.get(
            f"/sunat/auxiliary/status?workspace_id={workspace_id}&empresa_id={company_id}",
            headers=other_headers,
        )
        assert blocked.status_code == 404

        deleted = client.delete(
            f"/sunat/auxiliary/credentials?workspace_id={workspace_id}&empresa_id={company_id}&reason=validation_complete",
            headers=headers,
        )
        assert deleted.status_code == 200
        assert deleted.json()["status"] == "DISCONNECTED"
        assert deleted.json()["remote_actions_enabled"] is False

        row_after = asyncio.run(latest_sunat_credential("local-demo", company_id, workspace_id))
        assert row_after is not None
        assert row_after.status == "DISCONNECTED"
        assert row_after.sunat_username_encrypted is None
        assert row_after.sunat_password_encrypted is None

        event_statuses = asyncio.run(sunat_connection_event_statuses("local-demo", company_id, workspace_id))
        assert event_statuses
        assert all(len(event_status) <= 32 for event_status in event_statuses)


def test_sunat_readonly_run_discovers_permissions_stores_evidence_and_blocks_sensitive_actions(monkeypatch) -> None:
    original_readonly = settings.sunat_readonly_enabled
    object.__setattr__(settings, "sunat_readonly_enabled", True)

    async def fake_run_readonly_session(*, ruc: str, username: str, password: str) -> SunatReadOnlyConnectorResult:
        assert ruc.startswith("20")
        assert username.startswith("auxread")
        assert password == "clave-sol-test-123"
        return SunatReadOnlyConnectorResult(
            status="CONNECTED_READ_ONLY",
            real_connector_enabled=True,
            real_sunat_session=True,
            read_only=True,
            remote_actions_enabled=False,
            reason="unit_readonly_session",
            available_permissions=[
                {
                    "permission_name": "Mi RUC y Otros Registros > Ficha RUC",
                    "permission_path": "Mi RUC y Otros Registros > Ficha RUC",
                    "permission_type": "consulta",
                    "is_available": True,
                    "can_read": True,
                    "can_execute": False,
                    "status": "available_readonly",
                },
                {
                    "permission_name": "Comprobantes de pago > Consulta Integrada de Comprobantes de Pago",
                    "permission_path": "Comprobantes de pago > Consulta Integrada de Comprobantes de Pago",
                    "permission_type": "consulta",
                    "is_available": True,
                    "can_read": True,
                    "can_execute": False,
                    "status": "available_readonly",
                },
                {
                    "permission_name": "Mis Declaraciones y pagos > Presentar Declaración y Pago",
                    "permission_path": "Mis Declaraciones y pagos > Presentar Declaración y Pago",
                    "permission_type": "sensitive_action",
                    "is_available": True,
                    "is_sensitive": True,
                    "can_read": False,
                    "can_execute": False,
                    "status": "sensitive_detected_blocked",
                },
            ],
            snapshots=[
                {
                    "source": "sunat_session",
                    "snapshot_type": "authenticated_menu",
                    "content": {"ruc": ruc, "menu_items": 3, "password_logged": False},
                    "metadata": {"credentials_submitted": True, "password_logged": False},
                }
            ],
            normalized_facts=[
                {
                    "fact_type": "identity_tax",
                    "fact_key": "ficha_ruc",
                    "fact_value": {"estado": "ACTIVO", "condicion": "HABIDO"},
                    "confidence": 90,
                    "status": "normalized",
                }
            ],
            findings=[
                {
                    "severity": "critical",
                    "category": "debt",
                    "title": "Deuda tributaria relevante",
                    "message": "SUNAT reporta una señal crítica de prueba.",
                    "source": "unit_connector",
                    "status": "open",
                }
            ],
        )

    monkeypatch.setattr("app.services.sunat_service.sunat_readonly_connector.run_readonly_session", fake_run_readonly_session)
    try:
        with TestClient(app) as client:
            headers = auth_headers(client)
            client.patch("/subscriptions/current", headers=headers, json={"plan": "premium"})
            unique = uuid.uuid4().hex[:8]
            company = client.post(
                "/identity/companies",
                headers=headers,
                json={
                    "ruc": f"20{unique}1",
                    "razon_social": f"ReadOnly SUNAT {unique}",
                    "regimen_tributario": "mype_tributario",
                },
            )
            assert company.status_code == 200
            company_id = company.json()["id"]
            workspace = client.post(
                "/identity/workspaces",
                headers=headers,
                json={"nombre": f"Workspace ReadOnly {unique}", "empresa_id": company_id, "plan_id": "PREMIUM"},
            )
            assert workspace.status_code == 200
            workspace_id = workspace.json()["id"]
            stored = client.post(
                "/sunat/auxiliary/credentials",
                headers=headers,
                json={
                    "empresa_id": company_id,
                    "workspace_id": workspace_id,
                    "ruc": company.json()["ruc"],
                    "sunat_username": f"auxread_{unique}",
                    "sunat_password": "clave-sol-test-123",
                    "consent_accepted": True,
                    "auxiliary_user_acknowledged": True,
                    "read_only_acknowledged": True,
                    "no_tax_action_acknowledged": True,
                },
            )
            assert stored.status_code == 200
            assert "clave-sol-test-123" not in stored.text

            unauthenticated = client.post("/sunat/readonly/run", json={"empresa_id": company_id, "workspace_id": workspace_id})
            assert unauthenticated.status_code in {401, 403}

            run = client.post("/sunat/readonly/run", headers=headers, json={"empresa_id": company_id, "workspace_id": workspace_id})
            assert run.status_code == 200
            body = run.json()
            assert body["connector"]["status"] == "CONNECTED_READ_ONLY"
            assert body["connector"]["real_sunat_session"] is True
            assert body["connector"]["remote_actions_enabled"] is False
            assert body["summary"]["recommended_missing"] >= 1
            assert body["summary"]["sensitive_detected"] >= 1
            assert body["findings"][0]["severity"] == "critical"
            assert "clave-sol-test-123" not in run.text
            assert f"auxread_{unique}" not in run.text

            run_id = body["run"]["id"]
            counts = asyncio.run(sunat_readonly_table_counts(run_id))
            assert counts["runs"] == 1
            assert counts["permissions"] >= 17
            assert counts["snapshots"] == 1
            assert counts["facts"] >= 1
            assert counts["findings"] >= 2

            permissions = client.get(f"/sunat/readonly/permissions?workspace_id={workspace_id}&empresa_id={company_id}", headers=headers)
            assert permissions.status_code == 200
            assert permissions.json()["missing"]
            assert permissions.json()["sensitive"][0]["can_execute"] is False

            diagnosis = client.get(f"/sunat/readonly/diagnosis?workspace_id={workspace_id}&empresa_id={company_id}", headers=headers)
            assert diagnosis.status_code == 200
            assert diagnosis.json()["prioritized_findings"][0]["severity"] == "critical"

            runtime = client.get("/runtime/status")
            assert runtime.status_code == 200
            assert runtime.json()["sunat_readonly_enabled"] is True
            assert runtime.json()["sensitive_actions_enabled"] is False
            assert runtime.json()["raw_snapshot_storage"] is True
            assert runtime.json()["external_datalake_enabled"] is False
            assert runtime.json()["storage_backend"] == "postgres"
    finally:
        asyncio.run(
            repositories.update_tenant_subscription(
                "local-demo",
                "premium",
                {"alerts": 1000, "recommendations": 500, "documents": 1000, "workflows": 500, "ai_requests": 100, "users": 25},
            )
        )
        object.__setattr__(settings, "sunat_readonly_enabled", original_readonly)


def test_sunat_readonly_new_reads_block_when_subscription_expired_and_history_remains(monkeypatch) -> None:
    original_readonly = settings.sunat_readonly_enabled
    object.__setattr__(settings, "sunat_readonly_enabled", True)

    async def blocked_fake_run(*, ruc: str, username: str, password: str) -> SunatReadOnlyConnectorResult:
        return SunatReadOnlyConnectorResult(
            status="BLOCKED_MANUAL_CHALLENGE",
            real_connector_enabled=True,
            real_sunat_session=False,
            read_only=True,
            remote_actions_enabled=False,
            reason="unit_blocked",
        )

    monkeypatch.setattr("app.services.sunat_service.sunat_readonly_connector.run_readonly_session", blocked_fake_run)
    try:
        with TestClient(app) as client:
            headers = auth_headers(client)
            client.patch("/subscriptions/current", headers=headers, json={"plan": "premium"})
            unique = uuid.uuid4().hex[:8]
            company = client.post(
                "/identity/companies",
                headers=headers,
                json={"ruc": f"20{unique}2", "razon_social": f"Retencion SUNAT {unique}", "regimen_tributario": "mype_tributario"},
            )
            company_id = company.json()["id"]
            workspace = client.post(
                "/identity/workspaces",
                headers=headers,
                json={"nombre": f"Workspace Retention {unique}", "empresa_id": company_id, "plan_id": "PREMIUM"},
            )
            workspace_id = workspace.json()["id"]
            stored = client.post(
                "/sunat/auxiliary/credentials",
                headers=headers,
                json={
                    "empresa_id": company_id,
                    "workspace_id": workspace_id,
                    "ruc": company.json()["ruc"],
                    "sunat_username": f"auxret_{unique}",
                    "sunat_password": "clave-sol-test-123",
                    "consent_accepted": True,
                    "auxiliary_user_acknowledged": True,
                    "read_only_acknowledged": True,
                    "no_tax_action_acknowledged": True,
                },
            )
            assert stored.status_code == 200
            first_run = client.post("/sunat/readonly/run", headers=headers, json={"empresa_id": company_id, "workspace_id": workspace_id})
            assert first_run.status_code == 200
            asyncio.run(expire_latest_subscription("local-demo"))

            blocked = client.post("/sunat/readonly/run", headers=headers, json={"empresa_id": company_id, "workspace_id": workspace_id})
            assert blocked.status_code == 402
            assert blocked.json()["detail"]["error"] == "subscription_not_active"

            history = client.get(f"/sunat/readonly/history?workspace_id={workspace_id}&empresa_id={company_id}", headers=headers)
            assert history.status_code == 200
            assert len(history.json()["runs"]) == 1
    finally:
        asyncio.run(
            repositories.update_tenant_subscription(
                "local-demo",
                "premium",
                {"alerts": 1000, "recommendations": 500, "documents": 1000, "workflows": 500, "ai_requests": 100, "users": 25},
            )
        )
        object.__setattr__(settings, "sunat_readonly_enabled", original_readonly)


def test_sunat_api_credentials_are_encrypted_masked_and_discovered() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        client.patch("/subscriptions/current", headers=headers, json={"plan": "premium"})
        unique = uuid.uuid4().hex[:8]
        company = client.post(
            "/identity/companies",
            headers=headers,
            json={"ruc": f"20{unique}2", "razon_social": f"API SUNAT {unique}", "regimen_tributario": "mype_tributario"},
        )
        assert company.status_code == 200
        company_id = company.json()["id"]
        workspace = client.post(
            "/identity/workspaces",
            headers=headers,
            json={"nombre": f"Workspace API {unique}", "empresa_id": company_id, "plan_id": "PREMIUM"},
        )
        assert workspace.status_code == 200
        workspace_id = workspace.json()["id"]
        payload = {
            "empresa_id": company_id,
            "workspace_id": workspace_id,
            "ruc": company.json()["ruc"],
            "client_id": f"api-client-{unique}-123456",
            "client_secret": "api-client-secret-123456",
            "api_credentials_acknowledged": True,
            "official_api_acknowledged": True,
            "no_sensitive_actions_acknowledged": True,
        }

        unauthenticated = client.post("/sunat/api/credentials", json={**payload, "consent_accepted": True})
        assert unauthenticated.status_code in {401, 403}

        no_consent = client.post("/sunat/api/credentials", headers=headers, json=payload)
        assert no_consent.status_code == 400
        assert no_consent.json()["detail"]["error"] == "explicit_sunat_api_consent_required"

        stored = client.post("/sunat/api/credentials", headers=headers, json={**payload, "consent_accepted": True})
        assert stored.status_code == 200
        body = stored.json()
        assert body["credential"]["client_id_masked"] != payload["client_id"]
        assert body["credential"]["sensitive_actions_enabled"] is False
        assert payload["client_secret"] not in stored.text
        assert payload["client_id"] not in stored.text

        row = asyncio.run(latest_sunat_api_credential("local-demo", company_id, workspace_id))
        assert row is not None
        assert row.client_id_encrypted != payload["client_id"]
        assert row.client_secret_encrypted != payload["client_secret"]
        assert row.client_id_masked == body["credential"]["client_id_masked"]

        status_response = client.get(f"/sunat/api/status?workspace_id={workspace_id}&empresa_id={company_id}", headers=headers)
        assert status_response.status_code == 200
        status_body = status_response.json()
        assert status_body["api_configured"] is True
        assert status_body["permission_guide"]["permission"] == "Credenciales de API SUNAT"
        assert payload["client_secret"] not in status_response.text

        discovery = client.get(f"/sunat/api/discovery?workspace_id={workspace_id}&empresa_id={company_id}", headers=headers)
        assert discovery.status_code == 200
        services = {service["service"]: service for service in discovery.json()["services"]}
        assert services["cpe"]["official_api_available"] is True
        assert services["sire_sales"]["requires_sol_credentials"] is True
        assert services["declarations_payments"]["status"] == "ONLY_SOL_WEB"


def test_sunat_api_token_test_updates_hash_without_exposing_token(monkeypatch) -> None:
    async def fake_cpe_auth(credentials):
        assert credentials.client_id.startswith("api-client-")
        assert credentials.client_secret == "api-client-secret-abcdef"
        return {
            "status": "TOKEN_OK",
            "service": "cpe",
            "token": {
                "token_hash": "a" * 64,
                "expires_at": "2026-06-09T05:00:00+00:00",
                "expires_in": 3600,
                "scope": "https://api.sunat.gob.pe/v1/contribuyente/contribuyentes",
                "token_type": "Bearer",
            },
        }

    monkeypatch.setattr(sunat_api_service.cpe_client, "test_auth", fake_cpe_auth)

    with TestClient(app) as client:
        headers = auth_headers(client)
        client.patch("/subscriptions/current", headers=headers, json={"plan": "premium"})
        unique = uuid.uuid4().hex[:8]
        company = client.post(
            "/identity/companies",
            headers=headers,
            json={"ruc": f"20{unique}3", "razon_social": f"Token API {unique}", "regimen_tributario": "mype_tributario"},
        )
        company_id = company.json()["id"]
        workspace = client.post(
            "/identity/workspaces",
            headers=headers,
            json={"nombre": f"Workspace Token {unique}", "empresa_id": company_id, "plan_id": "PREMIUM"},
        )
        workspace_id = workspace.json()["id"]
        stored = client.post(
            "/sunat/api/credentials",
            headers=headers,
            json={
                "empresa_id": company_id,
                "workspace_id": workspace_id,
                "ruc": company.json()["ruc"],
                "client_id": f"api-client-{unique}-abcdef",
                "client_secret": "api-client-secret-abcdef",
                "consent_accepted": True,
                "api_credentials_acknowledged": True,
                "official_api_acknowledged": True,
                "no_sensitive_actions_acknowledged": True,
            },
        )
        assert stored.status_code == 200

        tested = client.post("/sunat/api/test", headers=headers, json={"empresa_id": company_id, "workspace_id": workspace_id})
        assert tested.status_code == 200
        tested_body = tested.json()
        assert tested_body["credential"]["token_configured"] is True
        assert tested_body["credential"]["last_test_status"] == "TOKEN_OK"
        assert "api-client-secret-abcdef" not in tested.text
        assert "Bearer " not in tested.text

        row = asyncio.run(latest_sunat_api_credential("local-demo", company_id, workspace_id))
        assert row is not None
        assert row.token_hash == "a" * 64


def test_sunat_api_cpe_and_sire_sync_store_evidence_without_manual_fallback(monkeypatch) -> None:
    async def fake_validate_comprobante(credentials, payload):
        assert payload["numRuc"].startswith("20")
        return {
            "status": "CPE_OK",
            "service": "cpe",
            "raw": {"success": True, "message": "OK", "data": {"estadoCp": "1", "estadoRuc": "00", "condDomiRuc": "00", "Observaciones": []}},
            "token": {"token_hash": "b" * 64, "expires_at": "2026-06-09T05:10:00+00:00"},
        }

    async def fake_sales_sync(api_credentials, sol_credentials, period):
        assert sol_credentials.username.startswith("auxapi")
        return {
            "status": "SIRE_SALES_OK",
            "service": "sire_sales",
            "period": period,
            "content_type": "text/plain",
            "raw_text": "ventas|100.00|18.00",
            "token": {"token_hash": "c" * 64, "expires_at": "2026-06-09T05:20:00+00:00"},
        }

    async def fake_purchases_sync(api_credentials, sol_credentials, period):
        assert sol_credentials.password == "clave-sol-test-123"
        return {
            "status": "SIRE_PURCHASES_OK",
            "service": "sire_purchases",
            "period": period,
            "raw": {"resumen": {"base": 80.0, "igv": 14.4}},
            "token": {"token_hash": "d" * 64, "expires_at": "2026-06-09T05:30:00+00:00"},
        }

    monkeypatch.setattr(sunat_api_service.cpe_client, "validate_comprobante", fake_validate_comprobante)
    monkeypatch.setattr(sunat_api_service.sire_sales_client, "sync_period", fake_sales_sync)
    monkeypatch.setattr(sunat_api_service.sire_purchases_client, "sync_period", fake_purchases_sync)

    with TestClient(app) as client:
        headers = auth_headers(client)
        client.patch("/subscriptions/current", headers=headers, json={"plan": "premium"})
        unique = uuid.uuid4().hex[:8]
        company = client.post(
            "/identity/companies",
            headers=headers,
            json={"ruc": f"20{unique}4", "razon_social": f"Sync API {unique}", "regimen_tributario": "mype_tributario"},
        )
        company_id = company.json()["id"]
        workspace = client.post(
            "/identity/workspaces",
            headers=headers,
            json={"nombre": f"Workspace Sync {unique}", "empresa_id": company_id, "plan_id": "PREMIUM"},
        )
        workspace_id = workspace.json()["id"]
        api_stored = client.post(
            "/sunat/api/credentials",
            headers=headers,
            json={
                "empresa_id": company_id,
                "workspace_id": workspace_id,
                "ruc": company.json()["ruc"],
                "client_id": f"api-client-{unique}-fedcba",
                "client_secret": "api-client-secret-fedcba",
                "consent_accepted": True,
                "api_credentials_acknowledged": True,
                "official_api_acknowledged": True,
                "no_sensitive_actions_acknowledged": True,
            },
        )
        assert api_stored.status_code == 200

        no_sol = client.post("/sunat/api/sire/sales/sync", headers=headers, json={"empresa_id": company_id, "workspace_id": workspace_id, "period": "202605"})
        assert no_sol.status_code == 409
        assert no_sol.json()["detail"]["error"] == "SOL_CREDENTIALS_MISSING"

        aux = client.post(
            "/sunat/auxiliary/credentials",
            headers=headers,
            json={
                "empresa_id": company_id,
                "workspace_id": workspace_id,
                "ruc": company.json()["ruc"],
                "sunat_username": f"auxapi_{unique}",
                "sunat_password": "clave-sol-test-123",
                "consent_accepted": True,
                "auxiliary_user_acknowledged": True,
                "read_only_acknowledged": True,
                "no_tax_action_acknowledged": True,
            },
        )
        assert aux.status_code == 200

        cpe = client.post(
            "/sunat/api/cpe/test",
            headers=headers,
            json={
                "empresa_id": company_id,
                "workspace_id": workspace_id,
                "numRuc": "20123456789",
                "codComp": "01",
                "numeroSerie": "F001",
                "numero": 123,
                "fechaEmision": "01/06/2026",
                "monto": 118.0,
            },
        )
        assert cpe.status_code == 200
        assert cpe.json()["run"]["connector_status"] == "CPE_OK"
        assert "clave-sol-test-123" not in cpe.text

        sales = client.post("/sunat/api/sire/sales/sync", headers=headers, json={"empresa_id": company_id, "workspace_id": workspace_id, "period": "202605"})
        assert sales.status_code == 200
        assert sales.json()["run"]["connector_status"] == "SIRE_SALES_OK"

        purchases = client.post("/sunat/api/sire/purchases/sync", headers=headers, json={"empresa_id": company_id, "workspace_id": workspace_id, "period": "202605"})
        assert purchases.status_code == 200
        assert purchases.json()["run"]["connector_status"] == "SIRE_PURCHASES_OK"

        diagnosis = client.get(f"/sunat/api/diagnosis?workspace_id={workspace_id}&empresa_id={company_id}", headers=headers)
        assert diagnosis.status_code == 200
        assert diagnosis.json()["prioritized_findings"]
        assert "api-client-secret-fedcba" not in diagnosis.text
