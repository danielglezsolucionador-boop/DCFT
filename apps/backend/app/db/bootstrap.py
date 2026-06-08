from __future__ import annotations

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db import repositories
from app.db.models import Subscription, Tenant, User, UserBusinessPlan
from app.db.session import async_session


async def bootstrap_local_identity() -> None:
    if not settings.bootstrap_admin_enabled:
        return
    await repositories.ensure_email_verification_storage()
    await repositories.ensure_checkout_storage()
    await repositories.ensure_stripe_webhook_storage()
    await repositories.ensure_student_doctor_storage()

    async with async_session() as session:
        async with session.begin():
            tenant = await session.get(Tenant, "local-demo")
            if tenant is None:
                session.add(Tenant(id="local-demo", name="Local Demo Tenant", country="PE", status="active"))

            result = await session.execute(select(User).where(User.username == settings.admin_username))
            user = result.scalar_one_or_none()
            password_hash = hash_password(settings.admin_password, salt=b"dcft-local-salt")
            if user is None:
                session.add(
                    User(
                        id="user-local-admin",
                        tenant_id="local-demo",
                        username=settings.admin_username,
                        password_hash=password_hash,
                        role="tenant_admin",
                        plan="premium",
                        active=True,
                        email_verified=True,
                    )
                )
            else:
                user.tenant_id = "local-demo"
                user.password_hash = password_hash
                user.role = "tenant_admin"
                user.plan = "premium"
                user.active = True
                user.email_verified = True

            subscription = await session.get(Subscription, "subscription-local-demo")
            if subscription is None:
                session.add(
                    Subscription(
                        id="subscription-local-demo",
                        tenant_id="local-demo",
                        plan="premium",
                        status="active",
                        limits={"recommendations_per_month": 500, "workflow_runs_per_day": 500},
                    )
                )
            else:
                subscription.plan = "premium"
            user_plan = await session.get(UserBusinessPlan, "user-local-admin")
            if user_plan is None:
                session.add(UserBusinessPlan(user_id="user-local-admin", tenant_id="local-demo", plan_id="PREMIUM", estado="active"))
            else:
                user_plan.tenant_id = "local-demo"
                user_plan.plan_id = "PREMIUM"
                user_plan.estado = "active"
