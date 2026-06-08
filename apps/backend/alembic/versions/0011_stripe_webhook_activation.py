"""stripe webhook subscription activation

Revision ID: 0011_stripe_webhook_activation
Revises: 0010_student_doctor_usage
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa


revision = "0011_stripe_webhook_activation"
down_revision = "0010_student_doctor_usage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("billing_cycle", sa.String(length=16), nullable=True))
    op.add_column("subscriptions", sa.Column("provider", sa.String(length=64), nullable=True))
    op.add_column("subscriptions", sa.Column("provider_subscription_id", sa.String(length=180), nullable=True))
    op.add_column("subscriptions", sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("subscriptions", sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True))
    op.add_column("subscriptions", sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_subscriptions_billing_cycle", "subscriptions", ["billing_cycle"])
    op.create_index("ix_subscriptions_provider", "subscriptions", ["provider"])
    op.create_index("ix_subscriptions_provider_subscription_id", "subscriptions", ["provider_subscription_id"])
    op.create_index("ix_subscriptions_activated_at", "subscriptions", ["activated_at"])
    op.create_index("ix_subscriptions_current_period_start", "subscriptions", ["current_period_start"])
    op.create_index("ix_subscriptions_current_period_end", "subscriptions", ["current_period_end"])

    op.add_column("checkout_sessions", sa.Column("provider_customer_id", sa.String(length=180), nullable=True))
    op.add_column("checkout_sessions", sa.Column("provider_subscription_id", sa.String(length=180), nullable=True))
    op.add_column("checkout_sessions", sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("checkout_sessions", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_checkout_sessions_provider_customer_id", "checkout_sessions", ["provider_customer_id"])
    op.create_index("ix_checkout_sessions_provider_subscription_id", "checkout_sessions", ["provider_subscription_id"])
    op.create_index("ix_checkout_sessions_paid_at", "checkout_sessions", ["paid_at"])
    op.create_index("ix_checkout_sessions_completed_at", "checkout_sessions", ["completed_at"])

    op.create_table(
        "stripe_webhook_events",
        sa.Column("id", sa.String(length=180), primary_key=True),
        sa.Column("provider", sa.String(length=64), nullable=False, server_default="stripe"),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="received"),
        sa.Column("checkout_session_id", sa.String(length=64), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_stripe_webhook_events_provider", "stripe_webhook_events", ["provider"])
    op.create_index("ix_stripe_webhook_events_event_type", "stripe_webhook_events", ["event_type"])
    op.create_index("ix_stripe_webhook_events_status", "stripe_webhook_events", ["status"])
    op.create_index("ix_stripe_webhook_events_checkout_session_id", "stripe_webhook_events", ["checkout_session_id"])
    op.create_index("ix_stripe_webhook_events_received_at", "stripe_webhook_events", ["received_at"])
    op.create_index("ix_stripe_webhook_events_processed_at", "stripe_webhook_events", ["processed_at"])


def downgrade() -> None:
    op.drop_table("stripe_webhook_events")
    op.drop_index("ix_checkout_sessions_completed_at", table_name="checkout_sessions")
    op.drop_index("ix_checkout_sessions_paid_at", table_name="checkout_sessions")
    op.drop_index("ix_checkout_sessions_provider_subscription_id", table_name="checkout_sessions")
    op.drop_index("ix_checkout_sessions_provider_customer_id", table_name="checkout_sessions")
    op.drop_column("checkout_sessions", "completed_at")
    op.drop_column("checkout_sessions", "paid_at")
    op.drop_column("checkout_sessions", "provider_subscription_id")
    op.drop_column("checkout_sessions", "provider_customer_id")
    op.drop_index("ix_subscriptions_current_period_end", table_name="subscriptions")
    op.drop_index("ix_subscriptions_current_period_start", table_name="subscriptions")
    op.drop_index("ix_subscriptions_activated_at", table_name="subscriptions")
    op.drop_index("ix_subscriptions_provider_subscription_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_provider", table_name="subscriptions")
    op.drop_index("ix_subscriptions_billing_cycle", table_name="subscriptions")
    op.drop_column("subscriptions", "current_period_end")
    op.drop_column("subscriptions", "current_period_start")
    op.drop_column("subscriptions", "activated_at")
    op.drop_column("subscriptions", "provider_subscription_id")
    op.drop_column("subscriptions", "provider")
    op.drop_column("subscriptions", "billing_cycle")
