"""email verification and checkout sessions

Revision ID: 0009_email_verification_checkout
Revises: 0008_sunat_credentials_vault
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa


revision = "0009_email_verification_checkout"
down_revision = "0008_sunat_credentials_vault"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_email_verified", "users", ["email_verified"])
    op.create_index("ix_users_email_verified_at", "users", ["email_verified_at"])

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("send_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_email_verification_tokens_user_id", "email_verification_tokens", ["user_id"])
    op.create_index("ix_email_verification_tokens_tenant_id", "email_verification_tokens", ["tenant_id"])
    op.create_index("ix_email_verification_tokens_token_hash", "email_verification_tokens", ["token_hash"])
    op.create_index("ix_email_verification_tokens_expires_at", "email_verification_tokens", ["expires_at"])
    op.create_index("ix_email_verification_tokens_consumed_at", "email_verification_tokens", ["consumed_at"])
    op.create_index("ix_email_verification_tokens_last_sent_at", "email_verification_tokens", ["last_sent_at"])
    op.create_index("ix_email_verification_tokens_created_at", "email_verification_tokens", ["created_at"])

    op.create_table(
        "checkout_sessions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("plan", sa.String(length=64), nullable=False),
        sa.Column("billing_cycle", sa.String(length=16), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_session_id", sa.String(length=180), nullable=True),
        sa.Column("checkout_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="PEN"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_checkout_sessions_tenant_id", "checkout_sessions", ["tenant_id"])
    op.create_index("ix_checkout_sessions_user_id", "checkout_sessions", ["user_id"])
    op.create_index("ix_checkout_sessions_plan", "checkout_sessions", ["plan"])
    op.create_index("ix_checkout_sessions_billing_cycle", "checkout_sessions", ["billing_cycle"])
    op.create_index("ix_checkout_sessions_provider", "checkout_sessions", ["provider"])
    op.create_index("ix_checkout_sessions_provider_session_id", "checkout_sessions", ["provider_session_id"])
    op.create_index("ix_checkout_sessions_status", "checkout_sessions", ["status"])
    op.create_index("ix_checkout_sessions_created_at", "checkout_sessions", ["created_at"])
    op.create_index("ix_checkout_sessions_updated_at", "checkout_sessions", ["updated_at"])


def downgrade() -> None:
    op.drop_table("checkout_sessions")
    op.drop_table("email_verification_tokens")
    op.drop_index("ix_users_email_verified_at", table_name="users")
    op.drop_index("ix_users_email_verified", table_name="users")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "email_verified")
