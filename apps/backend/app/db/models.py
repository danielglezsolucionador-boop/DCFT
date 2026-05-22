from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    country: Mapped[str] = mapped_column(String(80), default="PE")
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
