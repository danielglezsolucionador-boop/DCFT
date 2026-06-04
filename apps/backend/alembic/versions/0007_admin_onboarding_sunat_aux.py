"""admin onboarding sunat auxiliary preparation

Revision ID: 0007_admin_onboarding_sunat_aux
Revises: 0006_auth_trial_onboarding
Create Date: 2026-06-04
"""
from alembic import op
import sqlalchemy as sa


revision = "0007_admin_onboarding_sunat_aux"
down_revision = "0006_auth_trial_onboarding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "onboarding_progress",
        sa.Column("tenant_id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("account_created", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("company_registered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("ruc_registered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("videos_seen", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("sunat_auxiliary_prepared", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("initial_diagnosis_pending", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("checklist", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_onboarding_progress_user_id", "onboarding_progress", ["user_id"])
    op.create_index("ix_onboarding_progress_company_registered", "onboarding_progress", ["company_registered"])
    op.create_index("ix_onboarding_progress_ruc_registered", "onboarding_progress", ["ruc_registered"])
    op.create_index("ix_onboarding_progress_sunat_auxiliary_prepared", "onboarding_progress", ["sunat_auxiliary_prepared"])
    op.create_index("ix_onboarding_progress_completed", "onboarding_progress", ["completed"])
    op.create_index("ix_onboarding_progress_created_at", "onboarding_progress", ["created_at"])
    op.create_index("ix_onboarding_progress_updated_at", "onboarding_progress", ["updated_at"])


def downgrade() -> None:
    op.drop_index("ix_onboarding_progress_updated_at", table_name="onboarding_progress")
    op.drop_index("ix_onboarding_progress_created_at", table_name="onboarding_progress")
    op.drop_index("ix_onboarding_progress_completed", table_name="onboarding_progress")
    op.drop_index("ix_onboarding_progress_sunat_auxiliary_prepared", table_name="onboarding_progress")
    op.drop_index("ix_onboarding_progress_ruc_registered", table_name="onboarding_progress")
    op.drop_index("ix_onboarding_progress_company_registered", table_name="onboarding_progress")
    op.drop_index("ix_onboarding_progress_user_id", table_name="onboarding_progress")
    op.drop_table("onboarding_progress")
