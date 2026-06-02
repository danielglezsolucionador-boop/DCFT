from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import time
import uuid

from fastapi import Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import ai, alerts, analytics, audit, auth, dashboard, documents, education, feedback, governance, health, knowledge, memory, onboarding, recommendations, runtime, subscriptions, tax_workflows, users, workflows
from app.core.audit import append_audit_event_async, set_audit_request_id
from app.core.config import settings
from app.core.observability import metrics_registry
from app.db.bootstrap import bootstrap_local_identity
from app.db.migrations import run_migrations_if_enabled
from app.db.session import dispose_engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_runtime_safety()
    settings.state_dir.mkdir(parents=True, exist_ok=True)
    settings.audit_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    await run_migrations_if_enabled()
    await bootstrap_local_identity()
    await append_audit_event_async("runtime.startup", "system", {"service": settings.app_name, "version": settings.app_version})
    yield
    await append_audit_event_async("runtime.shutdown", "system", {"service": settings.app_name})
    await dispose_engine()


app = FastAPI(title="DCFT Backend", version=settings.app_version, lifespan=lifespan)
trace_persist_semaphore = asyncio.Semaphore(settings.observability_persist_concurrency)


async def persist_request_trace(request: Request, request_id: str, status_code: int, latency_ms: float) -> None:
    try:
        from app.db.repositories import record_runtime_event

        async with trace_persist_semaphore:
            await record_runtime_event(
                "request",
                "error" if status_code >= 500 else "ok",
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "latency_ms": round(latency_ms, 3),
                },
            )
    except Exception:
        metrics_registry.record_error()


@app.middleware("http")
async def request_observability(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    set_audit_request_id(request_id)
    content_length = request.headers.get("content-length")
    try:
        request_size = int(content_length) if content_length else 0
    except ValueError:
        request_size = 0
    if request_size > 524_288:
        metrics_registry.record_request(request.url.path, 413, 0.0)
        asyncio.create_task(persist_request_trace(request, request_id, 413, 0.0))
        return JSONResponse(
            status_code=413,
            content={"detail": {"error": "request_too_large", "max_bytes": 524_288}},
            headers={"X-Request-ID": request_id},
        )
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        metrics_registry.record_error()
        raise
    latency_ms = (time.perf_counter() - started) * 1000
    metrics_registry.record_request(request.url.path, response.status_code, latency_ms)
    asyncio.create_task(persist_request_trace(request, request_id, response.status_code, latency_ms))
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-ms"] = f"{latency_ms:.3f}"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(runtime.router)
app.include_router(onboarding.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subscriptions.router)
app.include_router(dashboard.router)
app.include_router(alerts.router)
app.include_router(recommendations.router)
app.include_router(documents.router)
app.include_router(education.router)
app.include_router(workflows.router)
app.include_router(tax_workflows.router)
app.include_router(governance.router)
app.include_router(audit.router)
app.include_router(analytics.router)
app.include_router(feedback.router)
app.include_router(ai.router)
app.include_router(knowledge.router)
app.include_router(memory.router)
