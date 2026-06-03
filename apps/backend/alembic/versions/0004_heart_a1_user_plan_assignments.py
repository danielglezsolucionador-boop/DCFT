"""heart a1 user plan assignments

Revision ID: 0004_heart_a1_user_plans
Revises: 0003_heart_a1_domain_identity
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa


revision = "0004_heart_a1_user_plans"
down_revision = "0003_heart_a1_domain_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_business_plans",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("plan_id", sa.String(length=32), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_business_plans_tenant_id", "user_business_plans", ["tenant_id"])
    op.create_index("ix_user_business_plans_plan_id", "user_business_plans", ["plan_id"])
    op.create_index("ix_user_business_plans_estado", "user_business_plans", ["estado"])
    op.create_index("ix_user_business_plans_created_at", "user_business_plans", ["created_at"])
    op.create_index("ix_user_business_plans_updated_at", "user_business_plans", ["updated_at"])
    op.execute(
        """
        insert into user_business_plans (user_id, tenant_id, plan_id, estado)
        select
            id,
            tenant_id,
            case
                when plan in ('business_premium') then 'PREMIUM'
                when plan in ('business_basic') then 'PROFESSIONAL'
                else 'FREE'
            end,
            'active'
        from users
        """
    )


def downgrade() -> None:
    op.drop_table("user_business_plans")
