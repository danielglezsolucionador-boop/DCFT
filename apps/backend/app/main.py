from __future__ import annotations

from contextlib import asynccontextmanager
import time
import uuid

from fastapi import Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import ai, alerts, auth, dashboard, documents, education, governance, health, knowledge, recommendations, runtime, subscriptions, users, workflows
from app.core.audit import append_audit_event_async
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


@app.middleware("http")
async def request_observability(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    content_length = request.headers.get("content-length")
    try:
        request_size = int(content_length) if content_length else 0
    except ValueError:
        request_size = 0
    if request_size > 524_288:
        metrics_registry.record_request(request.url.path, 413, 0.0)
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
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subscriptions.router)
app.include_router(dashboard.router)
app.include_router(alerts.router)
app.include_router(recommendations.router)
app.include_router(documents.router)
app.include_router(education.router)
app.include_router(workflows.router)
app.include_router(governance.router)
app.include_router(ai.router)
app.include_router(knowledge.router)
