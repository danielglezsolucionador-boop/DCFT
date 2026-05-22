"""dcft foundation

Revision ID: 0001_dcft_foundation
Revises:
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_dcft_foundation"
down_revision = None
branch_labels = None
depends_on = None


def _operational_table(name: str, *extra_columns: sa.Column) -> None:
    op.create_table(
        name,
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *extra_columns,
    )
    op.create_index(f"ix_{name}_tenant_id", name, ["tenant_id"])
    op.create_index(f"ix_{name}_status", name, ["status"])
    op.create_index(f"ix_{name}_created_at", name, ["created_at"])


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("country", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tenants_name", "tenants", ["name"])
    op.create_index("ix_tenants_status", "tenants", ["status"])

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("plan", sa.String(length=64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_plan", "users", ["plan"])

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("plan", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("limits", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_subscriptions_tenant_id", "subscriptions", ["tenant_id"])
    op.create_index("ix_subscriptions_plan", "subscriptions", ["plan"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("risk", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_events_tenant_id", "audit_events", ["tenant_id"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_actor", "audit_events", ["actor"])
    op.create_index("ix_audit_events_risk", "audit_events", ["risk"])

    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("scope", sa.String(length=120), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("risk", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_by", sa.String(length=120), nullable=False),
        sa.Column("decided_by", sa.String(length=120), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_approval_requests_tenant_id", "approval_requests", ["tenant_id"])
    op.create_index("ix_approval_requests_scope", "approval_requests", ["scope"])
    op.create_index("ix_approval_requests_risk", "approval_requests", ["risk"])
    op.create_index("ix_approval_requests_status", "approval_requests", ["status"])
    op.create_index("ix_approval_requests_requested_by", "approval_requests", ["requested_by"])

    _operational_table("alerts", sa.Column("severity", sa.String(length=32), nullable=False))
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    _operational_table("recommendations", sa.Column("category", sa.String(length=80), nullable=False))
    op.create_index("ix_recommendations_category", "recommendations", ["category"])
    _operational_table("documents", sa.Column("document_type", sa.String(length=80), nullable=False))
    op.create_index("ix_documents_document_type", "documents", ["document_type"])
    _operational_table("document_ingestions", sa.Column("document_id", sa.String(length=64), nullable=False))
    op.create_index("ix_document_ingestions_document_id", "document_ingestions", ["document_id"])
    _operational_table("educational_exercises", sa.Column("topic", sa.String(length=80), nullable=False))
    op.create_index("ix_educational_exercises_topic", "educational_exercises", ["topic"])
    _operational_table(
        "workflow_runs",
        sa.Column("current_step", sa.Integer(), nullable=False),
        sa.Column("human_checkpoint_required", sa.Boolean(), nullable=False),
    )
    _operational_table("ai_requests", sa.Column("provider_id", sa.String(length=120), nullable=False))
    op.create_index("ix_ai_requests_provider_id", "ai_requests", ["provider_id"])
    _operational_table("knowledge_items", sa.Column("domain", sa.String(length=80), nullable=False))
    op.create_index("ix_knowledge_items_domain", "knowledge_items", ["domain"])
    _operational_table("regulatory_items", sa.Column("jurisdiction", sa.String(length=80), nullable=False))
    op.create_index("ix_regulatory_items_jurisdiction", "regulatory_items", ["jurisdiction"])
    _operational_table("memory_records", sa.Column("memory_type", sa.String(length=80), nullable=False))
    op.create_index("ix_memory_records_memory_type", "memory_records", ["memory_type"])
    _operational_table("runtime_events", sa.Column("event_type", sa.String(length=120), nullable=False))
    op.create_index("ix_runtime_events_event_type", "runtime_events", ["event_type"])


def downgrade() -> None:
    for name in [
        "runtime_events",
        "memory_records",
        "regulatory_items",
        "knowledge_items",
        "ai_requests",
        "workflow_runs",
        "educational_exercises",
        "document_ingestions",
        "documents",
        "recommendations",
        "alerts",
        "approval_requests",
        "audit_events",
        "subscriptions",
        "users",
        "tenants",
    ]:
        op.drop_table(name)