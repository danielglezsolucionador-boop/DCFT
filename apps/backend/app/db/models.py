from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    country: Mapped[str] = mapped_column(String(80), default="PE")
    account_type: Mapped[str] = mapped_column(String(32), default="business", index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(64), index=True)
    plan: Mapped[str] = mapped_column(String(64), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    plan: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    limits: Mapped[dict] = mapped_column(JSON, default=dict)
    trial_status: Mapped[str] = mapped_column(String(32), default="none", index=True)
    trial_started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    trial_ends_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    ruc: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    razon_social: Mapped[str] = mapped_column(String(180), index=True)
    nombre_comercial: Mapped[str] = mapped_column(String(180), default="")
    regimen_tributario: Mapped[str] = mapped_column(String(80), default="general", index=True)
    estado: Mapped[str] = mapped_column(String(32), default="active", index=True)
    pais: Mapped[str] = mapped_column(String(80), default="PE", index=True)
    moneda: Mapped[str] = mapped_column(String(16), default="PEN")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)


class BusinessRole(Base):
    __tablename__ = "business_roles"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    permissions: Mapped[list] = mapped_column(JSON, default=list)
    estado: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class BusinessPlan(Base):
    __tablename__ = "business_plans"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    limits: Mapped[dict] = mapped_column(JSON, default=dict)
    features: Mapped[list] = mapped_column(JSON, default=list)
    estado: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    nombre: Mapped[str] = mapped_column(String(180), index=True)
    propietario: Mapped[str] = mapped_column(String(64), index=True)
    empresa_id: Mapped[str] = mapped_column(String(64), index=True)
    estado: Mapped[str] = mapped_column(String(32), default="active", index=True)
    plan_id: Mapped[str] = mapped_column(String(32), default="FREE", index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)


class WorkspaceMembership(Base):
    __tablename__ = "workspace_memberships"
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    role_id: Mapped[str] = mapped_column(String(32), index=True)
    estado: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class UserBusinessPlan(Base):
    __tablename__ = "user_business_plans"
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    plan_id: Mapped[str] = mapped_column(String(32), index=True)
    estado: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)


class ActiveOperationalContext(Base):
    __tablename__ = "active_operational_contexts"
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    active_company_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    active_workspace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    active_user_id: Mapped[str] = mapped_column(String(64), index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)


class OnboardingProgress(Base):
    __tablename__ = "onboarding_progress"
    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    account_created: Mapped[bool] = mapped_column(Boolean, default=True)
    company_registered: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    ruc_registered: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    videos_seen: Mapped[list] = mapped_column(JSON, default=list)
    sunat_auxiliary_prepared: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    initial_diagnosis_pending: Mapped[bool] = mapped_column(Boolean, default=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    checklist: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)


class SunatConnection(Base):
    __tablename__ = "sunat_connections"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    empresa_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    estado: Mapped[str] = mapped_column(String(32), default="NOT_CONNECTED", index=True)
    connection_type: Mapped[str] = mapped_column(String(64), default="CLAVE_SOL_AUXILIAR", index=True)
    auxiliary_user_alias: Mapped[str] = mapped_column(String(120), default="")
    credential_reference: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_by: Mapped[str] = mapped_column(String(64), index=True)
    updated_by: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)
    last_sync_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class SunatConsent(Base):
    __tablename__ = "sunat_consents"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    empresa_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    connection_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    consent_version: Mapped[str] = mapped_column(String(32), default="SUNAT_AUX_V1", index=True)
    scope: Mapped[dict] = mapped_column(JSON, default=dict)
    accepted_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class SunatConnectionEvent(Base):
    __tablename__ = "sunat_connection_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    connection_id: Mapped[str] = mapped_column(String(64), index=True)
    empresa_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    actor_user_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    actor: Mapped[str] = mapped_column(String(120), index=True)
    risk: Mapped[str] = mapped_column(String(32), index=True)
    request_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    previous_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    jti: Mapped[str] = mapped_column(String(96), primary_key=True)
    subject: Mapped[str] = mapped_column(String(120), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    reason: Mapped[str] = mapped_column(String(120), default="logout")
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AuthEvent(Base):
    __tablename__ = "auth_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(120), index=True)
    client_key: Mapped[str] = mapped_column(String(180), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    reason: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    scope: Mapped[str] = mapped_column(String(120), index=True)
    action: Mapped[str] = mapped_column(Text)
    risk: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    requested_by: Mapped[str] = mapped_column(String(120), index=True)
    decided_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class OperationalRecord(Base):
    __abstract__ = True
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Alert(OperationalRecord):
    __tablename__ = "alerts"
    severity: Mapped[str] = mapped_column(String(32), default="medium", index=True)


class Recommendation(OperationalRecord):
    __tablename__ = "recommendations"
    category: Mapped[str] = mapped_column(String(80), default="financial", index=True)


class Document(OperationalRecord):
    __tablename__ = "documents"
    document_type: Mapped[str] = mapped_column(String(80), default="unknown", index=True)


class DocumentIngestion(OperationalRecord):
    __tablename__ = "document_ingestions"
    document_id: Mapped[str] = mapped_column(String(64), index=True)


class EducationalExercise(OperationalRecord):
    __tablename__ = "educational_exercises"
    topic: Mapped[str] = mapped_column(String(80), default="accounting", index=True)


class WorkflowRun(OperationalRecord):
    __tablename__ = "workflow_runs"
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    human_checkpoint_required: Mapped[bool] = mapped_column(Boolean, default=True)


class AIRequest(OperationalRecord):
    __tablename__ = "ai_requests"
    provider_id: Mapped[str] = mapped_column(String(120), default="ai.disabled", index=True)


class KnowledgeItem(OperationalRecord):
    __tablename__ = "knowledge_items"
    domain: Mapped[str] = mapped_column(String(80), default="dcft", index=True)


class RegulatoryItem(OperationalRecord):
    __tablename__ = "regulatory_items"
    jurisdiction: Mapped[str] = mapped_column(String(80), default="PE", index=True)


class MemoryRecord(OperationalRecord):
    __tablename__ = "memory_records"
    memory_type: Mapped[str] = mapped_column(String(80), default="operational", index=True)


class RuntimeEvent(OperationalRecord):
    __tablename__ = "runtime_events"
    event_type: Mapped[str] = mapped_column(String(120), default="runtime", index=True)
