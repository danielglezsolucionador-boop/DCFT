from __future__ import annotations

import os
import tempfile

os.environ.setdefault("DCFT_BASE_DIR", tempfile.mkdtemp(prefix="dcft-tests-"))
os.environ.setdefault("DCFT_APP_ENV", "test")
os.environ.setdefault("DCFT_DB_AUTO_MIGRATE", "false")
os.environ.setdefault("DCFT_AI_PROVIDER_ENABLED", "false")
os.environ.setdefault("DCFT_OCR_ENABLED", "false")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def auth_headers() -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": "dcft_admin", "password": "dcft_local_admin_change_me"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_health_and_runtime_are_honest() -> None:
    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["production_ready"] is False
    assert "sqlite_local_fallback_active" in body["security_warnings"]

    runtime = client.get("/runtime/status")
    assert runtime.status_code == 200
    data = runtime.json()
    assert data["busy_loop"] is False
    assert data["zero_write_policy"] is True
    assert data["human_in_the_loop"] is True
    assert data["ai_pipeline"] == "blocked_provider_disabled"


def test_auth_rejects_invalid_missing_and_bad_tokens() -> None:
    assert client.post("/auth/login", json={"username": "bad", "password": "bad"}).status_code == 401
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer bad-token"}).status_code == 401


def test_dashboard_and_operational_records_require_auth() -> None:
    headers = auth_headers()
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
    assert alert.json()["status"] == "open"

    recommendation = client.post(
        "/recommendations",
        headers=headers,
        json={"category": "tax", "objective": "revisar obligaciones", "facts": {"period": "2026-05"}},
    )
    assert recommendation.status_code == 200
    assert recommendation.json()["explainability"]["method"] == "deterministic_rules_no_external_ai"


def test_documents_and_ai_are_blocked_honestly_when_providers_disabled() -> None:
    headers = auth_headers()
    document = client.post(
        "/documents/ingest",
        headers=headers,
        json={"filename": "factura-demo.pdf", "content_type": "application/pdf", "size_bytes": 128},
    )
    assert document.status_code == 200
    assert document.json()["ingestion"]["ocr_status"] == "placeholder_disabled"

    ai_request = client.post(
        "/ai/requests",
        headers=headers,
        json={"objective": "analizar flujo de caja", "input_summary": "datos locales", "constraints": ["no external ai"]},
    )
    assert ai_request.status_code == 200
    assert ai_request.json()["status"] == "blocked_provider_disabled"


def test_governance_blocks_critical_and_allows_approved_high_workflow() -> None:
    headers = auth_headers()

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
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

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