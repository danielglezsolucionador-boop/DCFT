"""enterprise hardening controls

Revision ID: 0002_enterprise_hardening
Revises: 0001_dcft_foundation
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_enterprise_hardening"
down_revision = "0001_dcft_foundation"
branch_labels = None
depends_on = None


OPERATIONAL_TABLES = [
    "alerts",
    "recommendations",
    "documents",
    "document_ingestions",
    "educational_exercises",
    "workflow_runs",
    "ai_requests",
    "knowledge_items",
    "regulatory_items",
    "memory_records",
    "runtime_events",
]


def upgrade() -> None:
    op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="1"))

    op.add_column("audit_events", sa.Column("request_id", sa.String(length=80), nullable=True))
    op.add_column("audit_events", sa.Column("previous_hash", sa.String(length=128), nullable=True))
    op.add_column("audit_events", sa.Column("event_hash", sa.String(length=128), nullable=True))
    op.create_index("ix_audit_events_request_id", "audit_events", ["request_id"])
    op.create_index("ix_audit_events_event_hash", "audit_events", ["event_hash"], unique=True)

    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(length=96), primary_key=True),
        sa.Column("subject", sa.String(length=120), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_revoked_tokens_subject", "revoked_tokens", ["subject"])
    op.create_index("ix_revoked_tokens_tenant_id", "revoked_tokens", ["tenant_id"])
    op.create_index("ix_revoked_tokens_expires_at", "revoked_tokens", ["expires_at"])

    op.create_table(
        "auth_events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("client_key", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auth_events_username", "auth_events", ["username"])
    op.create_index("ix_auth_events_client_key", "auth_events", ["client_key"])
    op.create_index("ix_auth_events_status", "auth_events", ["status"])
    op.create_index("ix_auth_events_created_at", "auth_events", ["created_at"])

    op.add_column("approval_requests", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    for table_name in OPERATIONAL_TABLES:
        op.add_column(table_name, sa.Column("version", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    for table_name in reversed(OPERATIONAL_TABLES):
        op.drop_column(table_name, "version")
    op.drop_column("approval_requests", "version")
    op.drop_table("auth_events")
    op.drop_table("revoked_tokens")
    op.drop_index("ix_audit_events_event_hash", table_name="audit_events")
    op.drop_index("ix_audit_events_request_id", table_name="audit_events")
    op.drop_column("audit_events", "event_hash")
    op.drop_column("audit_events", "previous_hash")
    op.drop_column("audit_events", "request_id")
    op.drop_column("users", "token_version")
