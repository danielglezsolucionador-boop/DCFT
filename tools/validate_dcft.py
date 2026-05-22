from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[1]
API_URL = "http://127.0.0.1:8200"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    report: dict[str, object] = {
        "base_dir": str(ROOT),
        "api_url": API_URL,
        "checks": [],
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    with httpx.Client(base_url=API_URL, timeout=10.0) as client:
        health = client.get("/health")
        require(health.status_code == 200, f"/health failed:{health.status_code}")
        health_body = health.json()
        require(health_body["production_ready"] is False, "local validation must not be production ready")
        report["checks"].append({"health": health_body["status"], "production_ready": health_body["production_ready"]})

        runtime = client.get("/runtime/status")
        require(runtime.status_code == 200, f"/runtime/status failed:{runtime.status_code}")
        runtime_body = runtime.json()
        require(runtime_body["busy_loop"] is False, "busy loop flag must be false")
        require(runtime_body["ai_pipeline"] == "blocked_provider_disabled", "AI provider must remain disabled locally")
        report["checks"].append({"runtime": runtime_body["status"], "busy_loop": runtime_body["busy_loop"]})

        invalid = client.post("/auth/login", json={"username": "bad", "password": "bad"})
        require(invalid.status_code == 401, "invalid login should be rejected")

        login = client.post("/auth/login", json={"username": "dcft_admin", "password": "dcft_local_admin_change_me"})
        require(login.status_code == 200, "valid local bootstrap login failed")
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        require(client.get("/auth/me", headers=headers).status_code == 200, "auth/me failed")

        critical = client.post(
            "/governance/approval-requests",
            headers=headers,
            json={"scope": "sunat", "action": "submit official filing", "risk": "critical", "reason": "safety test"},
        )
        require(critical.status_code == 200, "critical approval request failed")
        require(critical.json()["status"] == "blocked", "critical approval must start blocked")

        ai_request = client.post(
            "/ai/requests",
            headers=headers,
            json={"objective": "test provider", "input_summary": "no provider", "constraints": ["local only"]},
        )
        require(ai_request.status_code == 200, "AI request endpoint failed")
        require(ai_request.json()["status"] == "blocked_provider_disabled", "AI request must be blocked")

        for _ in range(40):
            require(client.get("/health").status_code == 200, "health stress failed")
            require(client.get("/runtime/status").status_code == 200, "runtime stress failed")
        report["checks"].append({"stress": "80 status requests passed"})

    output_dir = ROOT / ".dcft" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "validate_dcft_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"VALIDATION_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)