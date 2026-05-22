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

from datetime import datetime, timedelta, timezone
import asyncio

from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.security import hash_password
from app.db.models import User
from app.db.session import async_session
from app.main import app


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": "dcft_admin", "password": "dcft_local_admin_change_me"},
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

        runtime = client.get("/runtime/status")
        assert runtime.status_code == 200
        data = runtime.json()
        assert data["busy_loop"] is False
        assert data["zero_write_policy"] is True
        assert data["human_in_the_loop"] is True
        assert data["ai_pipeline"] == "blocked_provider_disabled"
        assert "observability" in data


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
