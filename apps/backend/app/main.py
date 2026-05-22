from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, alerts, auth, dashboard, documents, education, governance, health, knowledge, recommendations, runtime, subscriptions, users, workflows
from app.core.audit import append_audit_event
from app.core.config import settings
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
    append_audit_event("runtime.startup", "system", {"service": settings.app_name, "version": settings.app_version})
    yield
    append_audit_event("runtime.shutdown", "system", {"service": settings.app_name})
    await dispose_engine()


app = FastAPI(title="DCFT Backend", version=settings.app_version, lifespan=lifespan)

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