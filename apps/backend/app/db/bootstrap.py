from __future__ import annotations

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.db import repositories
from app.db.models import Subscription, Tenant, User, UserBusinessPlan
from app.db.session import async_session


INTERNAL_ADMIN_TENANT_ID = "local-demo"
INTERNAL_ADMIN_USER_ID = "user-local-admin"
INTERNAL_ADMIN_SUBSCRIPTION_ID = "subscription-local-demo"
INTERNAL_ADMIN_LIMITS = {"alerts": 100000, "recommendations": 100000, "documents": 100000, "workflows": 100000, "ai_requests": 100000, "users": 100000}


async def bootstrap_local_identity() -> None:
    if not settings.bootstrap_admin_enabled:
        return
    await repositories.ensure_email_verification_storage()
    await repositories.ensure_checkout_storage()
    await repositories.ensure_stripe_webhook_storage()
    await repositories.ensure_student_doctor_storage()

    async with async_session() as session:
        async with session.begin():
            tenant = await session.get(Tenant, INTERNAL_ADMIN_TENANT_ID)
            if tenant is None:
                session.add(
                    Tenant(
                        id=INTERNAL_ADMIN_TENANT_ID,
                        name="DCFT Internal",
                        country="PE",
                        account_type="business",
                        status="active",
                    )
                )
            else:
                tenant.name = "DCFT Internal"
                tenant.status = "active"

            result = await session.execute(select(User).where(User.username == settings.admin_username))
            user = result.scalar_one_or_none()
            canonical_user = await session.get(User, INTERNAL_ADMIN_USER_ID)
            if user is None:
                if canonical_user is None:
                    user = User(
                        id=INTERNAL_ADMIN_USER_ID,
                        tenant_id=INTERNAL_ADMIN_TENANT_ID,
                        username=settings.admin_username,
                        password_hash=hash_password(settings.admin_password),
                        role=settings.admin_role.strip().lower(),
                        plan=settings.admin_plan.strip().lower(),
                        active=True,
                        email_verified=True,
                    )
                    session.add(user)
                else:
                    user = canonical_user
                    user.username = settings.admin_username
            else:
                if canonical_user is not None and canonical_user.id != user.id:
                    canonical_user.active = False
                    canonical_user.role = "readonly"
                    canonical_user.plan = "free"

            user.tenant_id = INTERNAL_ADMIN_TENANT_ID
            if not verify_password(settings.admin_password, user.password_hash):
                user.password_hash = hash_password(settings.admin_password)
            user.role = settings.admin_role.strip().lower()
            user.plan = settings.admin_plan.strip().lower()
            user.active = True
            user.email_verified = True

            subscription = await session.get(Subscription, INTERNAL_ADMIN_SUBSCRIPTION_ID)
            if subscription is None:
                session.add(
                    Subscription(
                        id=INTERNAL_ADMIN_SUBSCRIPTION_ID,
                        tenant_id=INTERNAL_ADMIN_TENANT_ID,
                        plan=settings.admin_plan.strip().lower(),
                        status="active",
                        limits=INTERNAL_ADMIN_LIMITS,
                    )
                )
            else:
                subscription.tenant_id = INTERNAL_ADMIN_TENANT_ID
                subscription.plan = settings.admin_plan.strip().lower()
                subscription.status = "active"
                subscription.limits = INTERNAL_ADMIN_LIMITS
                subscription.billing_cycle = None
                subscription.provider = None
                subscription.provider_subscription_id = None
            user_plan = await session.get(UserBusinessPlan, user.id)
            if user_plan is None:
                session.add(
                    UserBusinessPlan(
                        user_id=user.id,
                        tenant_id=INTERNAL_ADMIN_TENANT_ID,
                        plan_id="PREMIUM",
                        estado="active",
                    )
                )
            else:
                user_plan.tenant_id = INTERNAL_ADMIN_TENANT_ID
                user_plan.plan_id = "PREMIUM"
                user_plan.estado = "active"
