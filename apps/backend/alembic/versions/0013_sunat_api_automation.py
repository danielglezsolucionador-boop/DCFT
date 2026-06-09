"""sunat api automation credentials

Revision ID: 0013_sunat_api_automation
Revises: 0012_sunat_readonly_intelligence
Create Date: 2026-06-09 00:08:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0013_sunat_api_automation"
down_revision = "0012_sunat_readonly_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sunat_api_credentials",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("empresa_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("ruc", sa.String(length=20), nullable=False, index=True),
        sa.Column("client_id_encrypted", sa.Text(), nullable=False),
        sa.Column("client_secret_encrypted", sa.Text(), nullable=False),
        sa.Column("client_id_masked", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="CONFIGURED", index=True),
        sa.Column("read_only", sa.Boolean(), nullable=False, server_default=sa.true(), index=True),
        sa.Column("sensitive_actions_enabled", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("services_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("token_hash", sa.String(length=128), nullable=True, index=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("last_test_status", sa.String(length=64), nullable=True, index=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("configured_by", sa.String(length=64), nullable=False, index=True),
        sa.Column("updated_by", sa.String(length=64), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True, index=True),
    )


def downgrade() -> None:
    op.drop_table("sunat_api_credentials")
