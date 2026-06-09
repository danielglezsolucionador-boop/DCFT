"""sunat readonly intelligence layer

Revision ID: 0012_sunat_readonly_intelligence
Revises: 0011_stripe_webhook_activation
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa


revision = "0012_sunat_readonly_intelligence"
down_revision = "0011_stripe_webhook_activation"
branch_labels = None
depends_on = None


def _json_default() -> sa.TextClause:
    return sa.text("'{}'")


def upgrade() -> None:
    op.create_table(
        "sunat_permission_checks",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("ruc", sa.String(length=20), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("permission_name", sa.String(length=240), nullable=False),
        sa.Column("permission_path", sa.Text(), nullable=False, server_default=""),
        sa.Column("permission_type", sa.String(length=64), nullable=False, server_default="unknown"),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_recommended", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_execute", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="not_checked"),
        sa.Column("source", sa.String(length=120), nullable=False, server_default="sunat_readonly"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=_json_default()),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in [
        "company_id",
        "tenant_id",
        "workspace_id",
        "ruc",
        "run_id",
        "permission_name",
        "permission_type",
        "is_available",
        "is_recommended",
        "is_sensitive",
        "can_read",
        "can_execute",
        "status",
        "detected_at",
    ]:
        op.create_index(f"ix_sunat_permission_checks_{column}", "sunat_permission_checks", [column])

    op.create_table(
        "sunat_raw_snapshots",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("ruc", sa.String(length=20), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False, server_default="sunat_readonly"),
        sa.Column("snapshot_type", sa.String(length=80), nullable=False, server_default="raw"),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("content_json", sa.JSON(), nullable=False, server_default=_json_default()),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=_json_default()),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ["tenant_id", "company_id", "workspace_id", "ruc", "run_id", "source", "snapshot_type", "content_hash", "captured_at"]:
        op.create_index(f"ix_sunat_raw_snapshots_{column}", "sunat_raw_snapshots", [column])

    op.create_table(
        "sunat_normalized_facts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("ruc", sa.String(length=20), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("fact_type", sa.String(length=80), nullable=False),
        sa.Column("fact_key", sa.String(length=160), nullable=False),
        sa.Column("fact_value", sa.JSON(), nullable=False, server_default=_json_default()),
        sa.Column("source_snapshot_id", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="normalized"),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ["tenant_id", "company_id", "workspace_id", "ruc", "run_id", "fact_type", "fact_key", "source_snapshot_id", "confidence", "status", "detected_at"]:
        op.create_index(f"ix_sunat_normalized_facts_{column}", "sunat_normalized_facts", [column])

    op.create_table(
        "sunat_diagnostic_runs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("ruc", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="pending"),
        sa.Column("connector_status", sa.String(length=80), nullable=False, server_default="not_started"),
        sa.Column("real_sunat_session", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("remote_actions_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("summary_json", sa.JSON(), nullable=False, server_default=_json_default()),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=_json_default()),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ["tenant_id", "company_id", "workspace_id", "ruc", "status", "connector_status", "real_sunat_session", "read_only", "remote_actions_enabled", "started_at", "completed_at"]:
        op.create_index(f"ix_sunat_diagnostic_runs_{column}", "sunat_diagnostic_runs", [column])

    op.create_table(
        "sunat_findings",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("ruc", sa.String(length=20), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="info"),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False, server_default="sunat_readonly"),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="open"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=_json_default()),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ["tenant_id", "company_id", "workspace_id", "ruc", "run_id", "severity", "category", "status", "detected_at"]:
        op.create_index(f"ix_sunat_findings_{column}", "sunat_findings", [column])


def downgrade() -> None:
    op.drop_table("sunat_findings")
    op.drop_table("sunat_diagnostic_runs")
    op.drop_table("sunat_normalized_facts")
    op.drop_table("sunat_raw_snapshots")
    op.drop_table("sunat_permission_checks")
