"""sunat auxiliary credentials vault

Revision ID: 0008_sunat_credentials_vault
Revises: 0007_admin_onboarding_sunat_aux
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa


revision = "0008_sunat_credentials_vault"
down_revision = "0007_admin_onboarding_sunat_aux"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sunat_credentials",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("empresa_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("ruc", sa.String(length=20), nullable=False),
        sa.Column("sunat_username_encrypted", sa.Text(), nullable=True),
        sa.Column("sunat_password_encrypted", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="CREDENTIAL_RECEIVED"),
        sa.Column("read_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("remote_actions_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sunat_credentials_tenant_id", "sunat_credentials", ["tenant_id"])
    op.create_index("ix_sunat_credentials_empresa_id", "sunat_credentials", ["empresa_id"])
    op.create_index("ix_sunat_credentials_workspace_id", "sunat_credentials", ["workspace_id"])
    op.create_index("ix_sunat_credentials_ruc", "sunat_credentials", ["ruc"])
    op.create_index("ix_sunat_credentials_status", "sunat_credentials", ["status"])
    op.create_index("ix_sunat_credentials_read_only", "sunat_credentials", ["read_only"])
    op.create_index("ix_sunat_credentials_remote_actions_enabled", "sunat_credentials", ["remote_actions_enabled"])
    op.create_index("ix_sunat_credentials_created_by", "sunat_credentials", ["created_by"])
    op.create_index("ix_sunat_credentials_updated_by", "sunat_credentials", ["updated_by"])
    op.create_index("ix_sunat_credentials_created_at", "sunat_credentials", ["created_at"])
    op.create_index("ix_sunat_credentials_updated_at", "sunat_credentials", ["updated_at"])
    op.create_index("ix_sunat_credentials_last_validated_at", "sunat_credentials", ["last_validated_at"])
    op.create_index("ix_sunat_credentials_disconnected_at", "sunat_credentials", ["disconnected_at"])


def downgrade() -> None:
    op.drop_table("sunat_credentials")
