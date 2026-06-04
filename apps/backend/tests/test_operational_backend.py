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

from datetime import datetime, timedelta, timezone
import asyncio
import uuid

from fastapi.testclient import TestClient
from jose import jwt
import pytest

from app.core.config import Settings, settings
from app.core.security import hash_password
from app.db.models import User
from app.db.session import async_session
from app.main import app


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
                )
            )


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


def test_login_lockout_is_persistent_security_control() -> None:
    with TestClient(app) as client:
        for _ in range(10):
            response = client.post("/auth/login", json={"username": "locked-user", "password": "bad"})
            assert response.status_code == 401
        locked = client.post("/auth/login", json={"username": "locked-user", "password": "bad"})
        assert locked.status_code == 429


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
        token = onboarding.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["role"] == "tenant_admin"
        assert me.json()["plan"] == "student"
        assert onboarding.json()["trial"]["status"] == "active"
        assert onboarding.json()["company"] is None

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

        headers = {"Authorization": f"Bearer {body['access_token']}"}
        assert client.get("/identity/companies", headers=headers).json()[0]["id"] == body["company"]["id"]
        assert client.get("/identity/workspaces", headers=headers).json()[0]["id"] == body["workspace"]["id"]


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
        headers = {"Authorization": f"Bearer {onboarding.json()['access_token']}"}

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

        upgraded = client.patch("/subscriptions/current", headers=headers, json={"plan": "business_basic"})
        assert upgraded.status_code == 200
        assert upgraded.json()["plan"] == "mype"

        allowed = client.post(
            "/alerts",
            headers=headers,
            json={"title": "Allowed after upgrade", "severity": "low", "source": "limit-test"},
        )
        assert allowed.status_code == 200

        downgraded = client.patch("/subscriptions/current", headers=headers, json={"plan": "free"})
        assert downgraded.status_code == 200
        assert downgraded.json()["over_limit"]["alerts"]["current"] == 6


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
        other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
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

        classification = client.get("/sunat/data-classification")
        assert classification.status_code == 200
        assert "RUC" in classification.json()["CONSULTABLE"]
        assert "presentacion_de_formularios" in classification.json()["NO_CONSULTABLE"]
        assert classification.json()["remote_actions_enabled"] is False

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
                "auxiliary_user_alias": "auxiliar-consulta",
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
