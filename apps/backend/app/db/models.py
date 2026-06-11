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
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    email_verified_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    plan: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    limits: Mapped[dict] = mapped_column(JSON, default=dict)
    billing_cycle: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(180), nullable=True, index=True)
    activated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    current_period_start: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    current_period_end: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    trial_status: Mapped[str] = mapped_column(String(32), default="none", index=True)
    trial_started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    trial_ends_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    send_count: Mapped[int] = mapped_column(Integer, default=1)
    last_sent_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class CheckoutSession(Base):
    __tablename__ = "checkout_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    plan: Mapped[str] = mapped_column(String(64), index=True)
    billing_cycle: Mapped[str] = mapped_column(String(16), index=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    provider_session_id: Mapped[str | None] = mapped_column(String(180), nullable=True, index=True)
    checkout_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="PEN")
    provider_customer_id: Mapped[str | None] = mapped_column(String(180), nullable=True, index=True)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(180), nullable=True, index=True)
    paid_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)


class StripeWebhookEvent(Base):
    __tablename__ = "stripe_webhook_events"
    id: Mapped[str] = mapped_column(String(180), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), default="stripe", index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(32), default="received", index=True)
    checkout_session_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    received_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class StudentDoctorUsage(Base):
    __tablename__ = "student_doctor_usage"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    month_key: Mapped[str] = mapped_column(String(7), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    month: Mapped[int] = mapped_column(Integer, index=True)
    questions_used: Mapped[int] = mapped_column(Integer, default=0)
    questions_limit: Mapped[int] = mapped_column(Integer, default=5)
    timestamps: Mapped[list] = mapped_column(JSON, default=list)
    last_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)
    last_asked_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


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


class SunatCredential(Base):
    __tablename__ = "sunat_credentials"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    empresa_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    ruc: Mapped[str] = mapped_column(String(20), index=True)
    sunat_username_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    sunat_password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="CREDENTIAL_RECEIVED", index=True)
    read_only: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    remote_actions_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_by: Mapped[str] = mapped_column(String(64), index=True)
    updated_by: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)
    last_validated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    disconnected_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class SunatApiCredential(Base):
    __tablename__ = "sunat_api_credentials"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    empresa_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    ruc: Mapped[str] = mapped_column(String(20), index=True)
    client_id_encrypted: Mapped[str] = mapped_column(Text)
    client_secret_encrypted: Mapped[str] = mapped_column(Text)
    client_id_masked: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(64), default="CONFIGURED", index=True)
    read_only: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    sensitive_actions_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    services_json: Mapped[dict] = mapped_column(JSON, default=dict)
    token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    token_expires_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_test_status: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    configured_by: Mapped[str] = mapped_column(String(64), index=True)
    updated_by: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)
    last_validated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class SunatConsent(Base):
    __tablename__ = "sunat_consents"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    empresa_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    connection_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    consent_version: Mapped[str] = mapped_column(String(32), default="SUNAT_SOL_V1", index=True)
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


class SunatPermissionCheck(Base):
    __tablename__ = "sunat_permission_checks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    ruc: Mapped[str] = mapped_column(String(20), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    permission_name: Mapped[str] = mapped_column(String(240), index=True)
    permission_path: Mapped[str] = mapped_column(Text, default="")
    permission_type: Mapped[str] = mapped_column(String(64), default="unknown", index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    can_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    can_execute: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    status: Mapped[str] = mapped_column(String(64), default="not_checked", index=True)
    source: Mapped[str] = mapped_column(String(120), default="sunat_readonly")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    detected_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class SunatRawSnapshot(Base):
    __tablename__ = "sunat_raw_snapshots"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    ruc: Mapped[str] = mapped_column(String(20), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(120), default="sunat_readonly", index=True)
    snapshot_type: Mapped[str] = mapped_column(String(80), default="raw", index=True)
    content_hash: Mapped[str] = mapped_column(String(128), index=True)
    content_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    captured_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class SunatNormalizedFact(Base):
    __tablename__ = "sunat_normalized_facts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    ruc: Mapped[str] = mapped_column(String(20), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    fact_type: Mapped[str] = mapped_column(String(80), index=True)
    fact_key: Mapped[str] = mapped_column(String(160), index=True)
    fact_value: Mapped[dict] = mapped_column(JSON, default=dict)
    source_snapshot_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    confidence: Mapped[int] = mapped_column(Integer, default=0, index=True)
    status: Mapped[str] = mapped_column(String(64), default="normalized", index=True)
    detected_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class SunatDiagnosticRun(Base):
    __tablename__ = "sunat_diagnostic_runs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    ruc: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(64), default="pending", index=True)
    connector_status: Mapped[str] = mapped_column(String(80), default="not_started", index=True)
    real_sunat_session: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    read_only: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    remote_actions_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class SunatFinding(Base):
    __tablename__ = "sunat_findings"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    ruc: Mapped[str] = mapped_column(String(20), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32), default="info", index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(240))
    message: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(120), default="sunat_readonly")
    status: Mapped[str] = mapped_column(String(64), default="open", index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    detected_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


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
