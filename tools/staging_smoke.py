from __future__ import annotations

import argparse
import asyncio
import json
import random
import time
import uuid

import httpx


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


async def create_tenant(client: httpx.AsyncClient, plan: str) -> dict:
    unique = uuid.uuid4().hex[:8]
    response = await client.post(
        "/onboarding/tenants",
        json={
            "tenant_name": f"DCFT Staging {plan} {unique}",
            "admin_username": f"staging_{plan}_{unique}",
            "admin_password": "staging-user-pass-123",
            "plan": plan,
        },
    )
    require(response.status_code == 200, f"onboarding failed:{response.status_code}:{response.text}")
    return response.json()


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run controlled DCFT staging smoke, security, and latency checks.")
    parser.add_argument("--api-url", default="http://127.0.0.1:8200")
    parser.add_argument("--requests", type=int, default=120)
    parser.add_argument("--latency-ms", type=int, default=150)
    args = parser.parse_args()

    report: dict[str, object] = {"api_url": args.api_url, "checks": [], "started_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    async with httpx.AsyncClient(base_url=args.api_url, timeout=httpx.Timeout(12.0, connect=5.0)) as client:
        health = await client.get("/health")
        require(health.status_code == 200, f"health failed:{health.status_code}")
        report["checks"].append({"health": health.json().get("status"), "staging_ready": health.json().get("staging_ready")})

        runtime = await client.get("/runtime/status")
        require(runtime.status_code == 200, f"runtime failed:{runtime.status_code}")
        require(runtime.json()["busy_loop"] is False, "busy_loop must remain false")
        report["checks"].append({"runtime": runtime.json().get("status"), "busy_loop": runtime.json().get("busy_loop")})

        invalid_token = await client.get("/auth/me", headers={"Authorization": "Bearer invalid"})
        require(invalid_token.status_code in {401, 429}, f"invalid token accepted:{invalid_token.status_code}")
        invalid_login = await client.post("/auth/login", json={"username": "bad-user", "password": "bad-password"})
        require(invalid_login.status_code in {401, 429}, f"invalid login accepted:{invalid_login.status_code}")
        report["checks"].append({"auth_abuse": "rejected"})

        tenant_a = await create_tenant(client, "business_basic")
        tenant_b = await create_tenant(client, "student")
        headers_a = {"Authorization": f"Bearer {tenant_a['access_token']}"}
        headers_b = {"Authorization": f"Bearer {tenant_b['access_token']}"}
        await client.post("/alerts", headers=headers_a, json={"title": "Tenant A alert", "severity": "low", "source": "staging-smoke"})
        await client.post("/alerts", headers=headers_b, json={"title": "Tenant B alert", "severity": "low", "source": "staging-smoke"})
        summary_a = (await client.get("/dashboard/summary", headers=headers_a)).json()
        summary_b = (await client.get("/dashboard/summary", headers=headers_b)).json()
        require(summary_a["tenant_id"] != summary_b["tenant_id"], "tenant ids crossed")
        require(summary_a["counts"]["alerts"] == 1 and summary_b["counts"]["alerts"] == 1, "tenant data isolation failed")
        report["checks"].append({"tenant_isolation": "scoped"})

        feedback = await client.post("/feedback", headers=headers_a, json={"category": "onboarding", "severity": "medium", "message": "controlled staging feedback"})
        require(feedback.status_code == 200, f"feedback failed:{feedback.status_code}")
        report["checks"].append({"feedback": feedback.json().get("status")})

        async def hit(index: int) -> int:
            await asyncio.sleep(random.uniform(0, args.latency_ms / 1000))
            route = random.choice(["/health", "/runtime/status", "/onboarding/status", "/subscriptions/plans", "/dashboard/summary", "/analytics/summary"])
            headers = headers_a if route in {"/dashboard/summary", "/analytics/summary"} else {}
            response = await client.get(route, headers=headers)
            return response.status_code

        started = time.perf_counter()
        statuses = await asyncio.gather(*(hit(index) for index in range(args.requests)), return_exceptions=True)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        counts: dict[str, int] = {}
        for status in statuses:
            key = type(status).__name__ if isinstance(status, Exception) else str(status)
            counts[key] = counts.get(key, 0) + 1
        require(not any(key.endswith("Error") for key in counts), f"request errors:{counts}")
        require(all(key in {"200", "401", "429"} for key in counts), f"unexpected statuses:{counts}")
        report["checks"].append({"internet_conditions": {"requests": args.requests, "latency_ms": args.latency_ms, "elapsed_ms": elapsed_ms, "statuses": counts}})

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
