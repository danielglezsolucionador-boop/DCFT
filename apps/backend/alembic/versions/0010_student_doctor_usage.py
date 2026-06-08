"""student doctor monthly usage

Revision ID: 0010_student_doctor_usage
Revises: 0009_email_verification_checkout
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa


revision = "0010_student_doctor_usage"
down_revision = "0009_email_verification_checkout"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_doctor_usage",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("month_key", sa.String(length=7), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("questions_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("questions_limit", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("timestamps", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("last_question", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_asked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_student_doctor_usage_user_id", "student_doctor_usage", ["user_id"])
    op.create_index("ix_student_doctor_usage_tenant_id", "student_doctor_usage", ["tenant_id"])
    op.create_index("ix_student_doctor_usage_month_key", "student_doctor_usage", ["month_key"])
    op.create_index("ix_student_doctor_usage_year", "student_doctor_usage", ["year"])
    op.create_index("ix_student_doctor_usage_month", "student_doctor_usage", ["month"])
    op.create_index("ix_student_doctor_usage_status", "student_doctor_usage", ["status"])
    op.create_index("ix_student_doctor_usage_created_at", "student_doctor_usage", ["created_at"])
    op.create_index("ix_student_doctor_usage_updated_at", "student_doctor_usage", ["updated_at"])
    op.create_index("ix_student_doctor_usage_last_asked_at", "student_doctor_usage", ["last_asked_at"])
    op.create_index(
        "ux_student_doctor_usage_user_month",
        "student_doctor_usage",
        ["user_id", "tenant_id", "month_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("student_doctor_usage")
