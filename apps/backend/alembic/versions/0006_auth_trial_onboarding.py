"""auth roles trial onboarding foundation

Revision ID: 0006_auth_trial_onboarding
Revises: 0005_heart_a2_sunat
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa


revision = "0006_auth_trial_onboarding"
down_revision = "0005_heart_a2_sunat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    plans_table = sa.table(
        "business_plans",
        sa.column("id", sa.String),
        sa.column("nombre", sa.String),
        sa.column("limits", sa.JSON),
        sa.column("features", sa.JSON),
    )
    op.execute(
        plans_table.update()
        .where(plans_table.c.id == "FREE")
        .values(
            nombre="Estudiante",
            features=["education", "practice_workflows", "premium_modules_visible_locked"],
            limits={"users": 1, "companies": 0, "workspaces": 1},
        )
    )
    op.execute(
        plans_table.update()
        .where(plans_table.c.id == "PROFESSIONAL")
        .values(
            nombre="MYPE",
            features=["basic_monitoring", "alerts", "reports", "safe_sunat_sol_credentials"],
            limits={"users": 5, "companies": 1, "workspaces": 3},
        )
    )
    op.execute(
        plans_table.update()
        .where(plans_table.c.id == "PREMIUM")
        .values(
            nombre="Premium",
            features=["executive_reports", "advanced_audit", "doctor_empresarial", "priority_controls"],
            limits={"users": 25, "companies": 3, "workspaces": 10},
        )
    )

    op.add_column("tenants", sa.Column("account_type", sa.String(length=32), nullable=False, server_default="business"))
    op.create_index("ix_tenants_account_type", "tenants", ["account_type"])

    op.add_column("subscriptions", sa.Column("trial_status", sa.String(length=32), nullable=False, server_default="none"))
    op.add_column("subscriptions", sa.Column("trial_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("subscriptions", sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_subscriptions_trial_status", "subscriptions", ["trial_status"])
    op.create_index("ix_subscriptions_trial_started_at", "subscriptions", ["trial_started_at"])
    op.create_index("ix_subscriptions_trial_ends_at", "subscriptions", ["trial_ends_at"])


def downgrade() -> None:
    op.drop_index("ix_subscriptions_trial_ends_at", table_name="subscriptions")
    op.drop_index("ix_subscriptions_trial_started_at", table_name="subscriptions")
    op.drop_index("ix_subscriptions_trial_status", table_name="subscriptions")
    op.drop_column("subscriptions", "trial_ends_at")
    op.drop_column("subscriptions", "trial_started_at")
    op.drop_column("subscriptions", "trial_status")

    op.drop_index("ix_tenants_account_type", table_name="tenants")
    op.drop_column("tenants", "account_type")
