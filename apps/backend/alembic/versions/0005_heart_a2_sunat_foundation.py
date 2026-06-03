"""heart a2 sunat auxiliary foundation

Revision ID: 0005_heart_a2_sunat
Revises: 0004_heart_a1_user_plans
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa


revision = "0005_heart_a2_sunat"
down_revision = "0004_heart_a1_user_plans"
branch_labels = None
depends_on = None


ROLE_PERMISSIONS = {
    "STUDENT": [
        "companies:read",
        "workspaces:read",
        "permissions:read",
        "context:read",
        "sunat:read",
    ],
    "PROFESSIONAL": [
        "companies:read",
        "companies:create",
        "workspaces:read",
        "workspaces:create",
        "permissions:read",
        "context:read",
        "context:write",
        "sunat:read",
        "sunat:connect",
        "sunat:sync",
        "sunat:disconnect",
    ],
    "PREMIUM": [
        "companies:read",
        "companies:create",
        "workspaces:read",
        "workspaces:create",
        "permissions:read",
        "context:read",
        "context:write",
        "memberships:read",
        "sunat:read",
        "sunat:connect",
        "sunat:sync",
        "sunat:disconnect",
    ],
    "ADMIN": [
        "companies:read",
        "companies:create",
        "workspaces:read",
        "workspaces:create",
        "permissions:read",
        "context:read",
        "context:write",
        "memberships:read",
        "memberships:assign",
        "roles:assign",
        "sunat:read",
        "sunat:connect",
        "sunat:sync",
        "sunat:disconnect",
    ],
}


def upgrade() -> None:
    op.create_table(
        "sunat_connections",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("empresa_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False, server_default="NOT_CONNECTED"),
        sa.Column("connection_type", sa.String(length=64), nullable=False, server_default="CLAVE_SOL_AUXILIAR"),
        sa.Column("auxiliary_user_alias", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("credential_reference", sa.String(length=160), nullable=True),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sunat_connections_tenant_id", "sunat_connections", ["tenant_id"])
    op.create_index("ix_sunat_connections_empresa_id", "sunat_connections", ["empresa_id"])
    op.create_index("ix_sunat_connections_workspace_id", "sunat_connections", ["workspace_id"])
    op.create_index("ix_sunat_connections_estado", "sunat_connections", ["estado"])
    op.create_index("ix_sunat_connections_connection_type", "sunat_connections", ["connection_type"])
    op.create_index("ix_sunat_connections_created_by", "sunat_connections", ["created_by"])
    op.create_index("ix_sunat_connections_updated_by", "sunat_connections", ["updated_by"])
    op.create_index("ix_sunat_connections_created_at", "sunat_connections", ["created_at"])
    op.create_index("ix_sunat_connections_updated_at", "sunat_connections", ["updated_at"])
    op.create_index("ix_sunat_connections_last_sync_at", "sunat_connections", ["last_sync_at"])

    op.create_table(
        "sunat_consents",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("empresa_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("connection_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("consent_version", sa.String(length=32), nullable=False, server_default="SUNAT_AUX_V1"),
        sa.Column("scope", sa.JSON(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sunat_consents_tenant_id", "sunat_consents", ["tenant_id"])
    op.create_index("ix_sunat_consents_empresa_id", "sunat_consents", ["empresa_id"])
    op.create_index("ix_sunat_consents_workspace_id", "sunat_consents", ["workspace_id"])
    op.create_index("ix_sunat_consents_connection_id", "sunat_consents", ["connection_id"])
    op.create_index("ix_sunat_consents_user_id", "sunat_consents", ["user_id"])
    op.create_index("ix_sunat_consents_accepted", "sunat_consents", ["accepted"])
    op.create_index("ix_sunat_consents_consent_version", "sunat_consents", ["consent_version"])
    op.create_index("ix_sunat_consents_accepted_at", "sunat_consents", ["accepted_at"])
    op.create_index("ix_sunat_consents_created_at", "sunat_consents", ["created_at"])

    op.create_table(
        "sunat_connection_events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("connection_id", sa.String(length=64), nullable=False),
        sa.Column("empresa_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sunat_connection_events_tenant_id", "sunat_connection_events", ["tenant_id"])
    op.create_index("ix_sunat_connection_events_connection_id", "sunat_connection_events", ["connection_id"])
    op.create_index("ix_sunat_connection_events_empresa_id", "sunat_connection_events", ["empresa_id"])
    op.create_index("ix_sunat_connection_events_workspace_id", "sunat_connection_events", ["workspace_id"])
    op.create_index("ix_sunat_connection_events_actor_user_id", "sunat_connection_events", ["actor_user_id"])
    op.create_index("ix_sunat_connection_events_event_type", "sunat_connection_events", ["event_type"])
    op.create_index("ix_sunat_connection_events_status", "sunat_connection_events", ["status"])
    op.create_index("ix_sunat_connection_events_created_at", "sunat_connection_events", ["created_at"])

    for role_id, permissions in ROLE_PERMISSIONS.items():
        op.execute(
            sa.text("update business_roles set permissions = :permissions where id = :role_id").bindparams(
                sa.bindparam("permissions", permissions, type_=sa.JSON()),
                sa.bindparam("role_id", role_id, type_=sa.String()),
            )
        )


def downgrade() -> None:
    op.drop_table("sunat_connection_events")
    op.drop_table("sunat_consents")
    op.drop_table("sunat_connections")
