"""heart a1 domain identity

Revision ID: 0003_heart_a1_domain_identity
Revises: 0002_enterprise_hardening
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_heart_a1_domain_identity"
down_revision = "0002_enterprise_hardening"
branch_labels = None
depends_on = None


BUSINESS_ROLES = [
    {
        "id": "STUDENT",
        "nombre": "Student",
        "permissions": [
            "companies:read",
            "workspaces:read",
            "permissions:read",
            "context:read",
        ],
        "estado": "active",
    },
    {
        "id": "PROFESSIONAL",
        "nombre": "Professional",
        "permissions": [
            "companies:read",
            "companies:create",
            "workspaces:read",
            "workspaces:create",
            "permissions:read",
            "context:read",
            "context:write",
        ],
        "estado": "active",
    },
    {
        "id": "PREMIUM",
        "nombre": "Premium",
        "permissions": [
            "companies:read",
            "companies:create",
            "workspaces:read",
            "workspaces:create",
            "permissions:read",
            "context:read",
            "context:write",
            "memberships:read",
        ],
        "estado": "active",
    },
    {
        "id": "ADMIN",
        "nombre": "Admin",
        "permissions": [
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
        ],
        "estado": "active",
    },
]


BUSINESS_PLANS = [
    {
        "id": "FREE",
        "nombre": "Free",
        "limits": {"users": 1, "companies": 1, "workspaces": 1},
        "features": ["basic_dashboard", "single_company", "single_workspace"],
        "estado": "active",
    },
    {
        "id": "PROFESSIONAL",
        "nombre": "Professional",
        "limits": {"users": 5, "companies": 3, "workspaces": 5},
        "features": ["multi_company", "workflows", "reports"],
        "estado": "active",
    },
    {
        "id": "PREMIUM",
        "nombre": "Premium",
        "limits": {"users": 25, "companies": 20, "workspaces": 50},
        "features": ["multi_company", "advanced_workflows", "executive_reports", "priority_controls"],
        "estado": "active",
    },
]


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("ruc", sa.String(length=20), nullable=False),
        sa.Column("razon_social", sa.String(length=180), nullable=False),
        sa.Column("nombre_comercial", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("regimen_tributario", sa.String(length=80), nullable=False, server_default="general"),
        sa.Column("estado", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("pais", sa.String(length=80), nullable=False, server_default="PE"),
        sa.Column("moneda", sa.String(length=16), nullable=False, server_default="PEN"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_companies_tenant_id", "companies", ["tenant_id"])
    op.create_index("ix_companies_ruc", "companies", ["ruc"], unique=True)
    op.create_index("ix_companies_razon_social", "companies", ["razon_social"])
    op.create_index("ix_companies_regimen_tributario", "companies", ["regimen_tributario"])
    op.create_index("ix_companies_estado", "companies", ["estado"])
    op.create_index("ix_companies_pais", "companies", ["pais"])
    op.create_index("ix_companies_created_at", "companies", ["created_at"])
    op.create_index("ix_companies_updated_at", "companies", ["updated_at"])

    op.create_table(
        "business_roles",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("nombre", sa.String(length=80), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_business_roles_nombre", "business_roles", ["nombre"], unique=True)
    op.create_index("ix_business_roles_estado", "business_roles", ["estado"])
    op.create_index("ix_business_roles_created_at", "business_roles", ["created_at"])

    op.create_table(
        "business_plans",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("nombre", sa.String(length=80), nullable=False),
        sa.Column("limits", sa.JSON(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_business_plans_nombre", "business_plans", ["nombre"], unique=True)
    op.create_index("ix_business_plans_estado", "business_plans", ["estado"])
    op.create_index("ix_business_plans_created_at", "business_plans", ["created_at"])

    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("nombre", sa.String(length=180), nullable=False),
        sa.Column("propietario", sa.String(length=64), nullable=False),
        sa.Column("empresa_id", sa.String(length=64), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("plan_id", sa.String(length=32), nullable=False, server_default="FREE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workspaces_tenant_id", "workspaces", ["tenant_id"])
    op.create_index("ix_workspaces_nombre", "workspaces", ["nombre"])
    op.create_index("ix_workspaces_propietario", "workspaces", ["propietario"])
    op.create_index("ix_workspaces_empresa_id", "workspaces", ["empresa_id"])
    op.create_index("ix_workspaces_estado", "workspaces", ["estado"])
    op.create_index("ix_workspaces_plan_id", "workspaces", ["plan_id"])
    op.create_index("ix_workspaces_created_at", "workspaces", ["created_at"])
    op.create_index("ix_workspaces_updated_at", "workspaces", ["updated_at"])

    op.create_table(
        "workspace_memberships",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("workspace_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("role_id", sa.String(length=32), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workspace_memberships_tenant_id", "workspace_memberships", ["tenant_id"])
    op.create_index("ix_workspace_memberships_role_id", "workspace_memberships", ["role_id"])
    op.create_index("ix_workspace_memberships_estado", "workspace_memberships", ["estado"])
    op.create_index("ix_workspace_memberships_created_at", "workspace_memberships", ["created_at"])

    op.create_table(
        "active_operational_contexts",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("active_company_id", sa.String(length=64), nullable=True),
        sa.Column("active_workspace_id", sa.String(length=64), nullable=True),
        sa.Column("active_user_id", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_active_operational_contexts_tenant_id", "active_operational_contexts", ["tenant_id"])
    op.create_index("ix_active_operational_contexts_active_company_id", "active_operational_contexts", ["active_company_id"])
    op.create_index("ix_active_operational_contexts_active_workspace_id", "active_operational_contexts", ["active_workspace_id"])
    op.create_index("ix_active_operational_contexts_active_user_id", "active_operational_contexts", ["active_user_id"])
    op.create_index("ix_active_operational_contexts_updated_at", "active_operational_contexts", ["updated_at"])

    business_roles_table = sa.table(
        "business_roles",
        sa.column("id", sa.String),
        sa.column("nombre", sa.String),
        sa.column("permissions", sa.JSON),
        sa.column("estado", sa.String),
    )
    business_plans_table = sa.table(
        "business_plans",
        sa.column("id", sa.String),
        sa.column("nombre", sa.String),
        sa.column("limits", sa.JSON),
        sa.column("features", sa.JSON),
        sa.column("estado", sa.String),
    )
    op.bulk_insert(business_roles_table, BUSINESS_ROLES)
    op.bulk_insert(business_plans_table, BUSINESS_PLANS)


def downgrade() -> None:
    for table_name in [
        "active_operational_contexts",
        "workspace_memberships",
        "workspaces",
        "business_plans",
        "business_roles",
        "companies",
    ]:
        op.drop_table(table_name)
