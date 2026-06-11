from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import asyncio
import uuid
import hashlib

from sqlalchemy import func, select, text, update
from sqlalchemy.exc import DBAPIError, OperationalError

from app.core.audit import audit_hash
from app.core.config import settings
from app.db.models import (
    ActiveOperationalContext,
    AIRequest,
    Alert,
    ApprovalRequest,
    AuthEvent,
    AuditEvent,
    BusinessPlan,
    BusinessRole,
    CheckoutSession,
    Company,
    Document,
    DocumentIngestion,
    EmailVerificationToken,
    MemoryRecord,
    OnboardingProgress,
    Recommendation,
    RevokedToken,
    RuntimeEvent,
    StripeWebhookEvent,
    Subscription,
    SunatConnection,
    SunatConnectionEvent,
    SunatConsent,
    SunatApiCredential,
    SunatCredential,
    SunatDiagnosticRun,
    SunatFinding,
    SunatNormalizedFact,
    SunatPermissionCheck,
    SunatRawSnapshot,
    StudentDoctorUsage,
    Tenant,
    User,
    UserBusinessPlan,
    Workspace,
    WorkspaceMembership,
    WorkflowRun,
)
from app.db.session import async_session, engine


_audit_chain_locks: dict[str, asyncio.Lock] = {}
_audit_chain_locks_guard = asyncio.Lock()
_onboarding_storage_checked = False
_onboarding_storage_lock = asyncio.Lock()
_sunat_credential_storage_checked = False
_sunat_credential_storage_lock = asyncio.Lock()
_email_verification_storage_checked = False
_email_verification_storage_lock = asyncio.Lock()
_checkout_storage_checked = False
_checkout_storage_lock = asyncio.Lock()
_stripe_webhook_storage_checked = False
_stripe_webhook_storage_lock = asyncio.Lock()
_student_doctor_storage_checked = False
_student_doctor_storage_lock = asyncio.Lock()
_sunat_readonly_storage_checked = False
_sunat_readonly_storage_lock = asyncio.Lock()
_sunat_api_storage_checked = False
_sunat_api_storage_lock = asyncio.Lock()


def business_plan_from_legacy(plan: str) -> str:
    normalized = {"business_basic": "mype", "business_premium": "premium", "professional": "mype"}.get(plan, plan)
    if normalized == "premium":
        return "PREMIUM"
    if normalized == "mype":
        return "PROFESSIONAL"
    return "FREE"


async def _audit_lock_for(tenant_id: str) -> asyncio.Lock:
    async with _audit_chain_locks_guard:
        lock = _audit_chain_locks.get(tenant_id)
        if lock is None:
            lock = asyncio.Lock()
            _audit_chain_locks[tenant_id] = lock
        return lock


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _created_at(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else utc_now()


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def with_db_retry(operation, *, attempts: int = 3):
    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except (OperationalError, DBAPIError):
            if attempt == attempts:
                raise
            await asyncio.sleep(0.05 * attempt)


async def ensure_onboarding_progress_storage() -> None:
    global _onboarding_storage_checked
    if _onboarding_storage_checked:
        return
    async with _onboarding_storage_lock:
        if _onboarding_storage_checked:
            return
        async with engine.begin() as connection:
            await connection.run_sync(OnboardingProgress.__table__.create, checkfirst=True)
        _onboarding_storage_checked = True


async def ensure_sunat_credential_storage() -> None:
    global _sunat_credential_storage_checked
    if _sunat_credential_storage_checked:
        return
    async with _sunat_credential_storage_lock:
        if _sunat_credential_storage_checked:
            return
        async with engine.begin() as connection:
            await connection.run_sync(SunatCredential.__table__.create, checkfirst=True)
        _sunat_credential_storage_checked = True


async def ensure_sunat_readonly_storage() -> None:
    global _sunat_readonly_storage_checked
    if _sunat_readonly_storage_checked:
        return
    async with _sunat_readonly_storage_lock:
        if _sunat_readonly_storage_checked:
            return
        async with engine.begin() as connection:
            await connection.run_sync(SunatPermissionCheck.__table__.create, checkfirst=True)
            await connection.run_sync(SunatRawSnapshot.__table__.create, checkfirst=True)
            await connection.run_sync(SunatNormalizedFact.__table__.create, checkfirst=True)
            await connection.run_sync(SunatDiagnosticRun.__table__.create, checkfirst=True)
            await connection.run_sync(SunatFinding.__table__.create, checkfirst=True)
        _sunat_readonly_storage_checked = True


async def ensure_sunat_api_storage() -> None:
    global _sunat_api_storage_checked
    if _sunat_api_storage_checked:
        return
    async with _sunat_api_storage_lock:
        if _sunat_api_storage_checked:
            return
        async with engine.begin() as connection:
            await connection.run_sync(SunatApiCredential.__table__.create, checkfirst=True)
        _sunat_api_storage_checked = True


async def ensure_email_verification_storage() -> None:
    global _email_verification_storage_checked
    if _email_verification_storage_checked:
        return
    async with _email_verification_storage_lock:
        if _email_verification_storage_checked:
            return
        async with engine.begin() as connection:
            if settings.database_backend == "sqlite":
                result = await connection.execute(text("PRAGMA table_info(users)"))
                existing_columns = {row[1] for row in result.fetchall()}
                if "email_verified" not in existing_columns:
                    await connection.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 1"))
                if "email_verified_at" not in existing_columns:
                    await connection.execute(text("ALTER TABLE users ADD COLUMN email_verified_at DATETIME"))
            elif settings.database_backend == "postgresql":
                await connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT true"))
                await connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ"))
            await connection.run_sync(EmailVerificationToken.__table__.create, checkfirst=True)
        _email_verification_storage_checked = True


async def ensure_checkout_storage() -> None:
    global _checkout_storage_checked
    if _checkout_storage_checked:
        return
    async with _checkout_storage_lock:
        if _checkout_storage_checked:
            return
        async with engine.begin() as connection:
            await connection.run_sync(CheckoutSession.__table__.create, checkfirst=True)
            await _ensure_runtime_column(connection, "checkout_sessions", "provider_customer_id", "VARCHAR(180)", "VARCHAR(180)")
            await _ensure_runtime_column(connection, "checkout_sessions", "provider_subscription_id", "VARCHAR(180)", "VARCHAR(180)")
            await _ensure_runtime_column(connection, "checkout_sessions", "paid_at", "DATETIME", "TIMESTAMPTZ")
            await _ensure_runtime_column(connection, "checkout_sessions", "completed_at", "DATETIME", "TIMESTAMPTZ")
            await _ensure_runtime_column(connection, "subscriptions", "billing_cycle", "VARCHAR(16)", "VARCHAR(16)")
            await _ensure_runtime_column(connection, "subscriptions", "provider", "VARCHAR(64)", "VARCHAR(64)")
            await _ensure_runtime_column(connection, "subscriptions", "provider_subscription_id", "VARCHAR(180)", "VARCHAR(180)")
            await _ensure_runtime_column(connection, "subscriptions", "activated_at", "DATETIME", "TIMESTAMPTZ")
            await _ensure_runtime_column(connection, "subscriptions", "current_period_start", "DATETIME", "TIMESTAMPTZ")
            await _ensure_runtime_column(connection, "subscriptions", "current_period_end", "DATETIME", "TIMESTAMPTZ")
        _checkout_storage_checked = True


async def ensure_stripe_webhook_storage() -> None:
    global _stripe_webhook_storage_checked
    if _stripe_webhook_storage_checked:
        return
    async with _stripe_webhook_storage_lock:
        if _stripe_webhook_storage_checked:
            return
        async with engine.begin() as connection:
            await connection.run_sync(StripeWebhookEvent.__table__.create, checkfirst=True)
        _stripe_webhook_storage_checked = True


async def _ensure_runtime_column(connection, table_name: str, column_name: str, sqlite_type: str, postgres_type: str) -> None:
    if settings.database_backend == "sqlite":
        result = await connection.execute(text(f"PRAGMA table_info({table_name})"))
        existing_columns = {row[1] for row in result.fetchall()}
        if column_name not in existing_columns:
            await connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sqlite_type}"))
        return
    if settings.database_backend == "postgresql":
        await connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {postgres_type}"))


async def ensure_student_doctor_storage() -> None:
    global _student_doctor_storage_checked
    if _student_doctor_storage_checked:
        return
    async with _student_doctor_storage_lock:
        if _student_doctor_storage_checked:
            return
        async with engine.begin() as connection:
            await connection.run_sync(StudentDoctorUsage.__table__.create, checkfirst=True)
        _student_doctor_storage_checked = True


def _flatten_operational(row: Any, **extra: Any) -> dict:
    payload = dict(row.payload or {})
    return {
        "id": row.id,
        "timestamp": _created_at(row.created_at),
        "tenant_id": row.tenant_id,
        "status": row.status,
        "version": row.version,
        **extra,
        **payload,
    }


def clamp_page(limit: int = 100, offset: int = 0, max_limit: int = 500) -> tuple[int, int]:
    return max(1, min(limit, max_limit)), max(0, offset)


async def add_audit_event(
    event_type: str,
    actor: str,
    payload: dict,
    risk: str,
    tenant_id: str,
    *,
    event_id: str | None = None,
    created_at: str | None = None,
    request_id: str | None = None,
) -> dict:
    tenant_lock = await _audit_lock_for(tenant_id)
    async with tenant_lock:
        async def operation() -> dict:
            timestamp = created_at or utc_now()
            async with async_session() as session:
                async with session.begin():
                    if settings.database_backend == "postgresql":
                        await session.execute(
                            text("select pg_advisory_xact_lock(hashtext(:tenant_id))"),
                            {"tenant_id": tenant_id},
                        )
                    result = await session.execute(
                        select(AuditEvent)
                        .where(AuditEvent.tenant_id == tenant_id, AuditEvent.event_hash.isnot(None))
                        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
                        .limit(1)
                    )
                    previous = result.scalar_one_or_none()
                    previous_hash = previous.event_hash if previous is not None else None
                    current_id = event_id or str(uuid.uuid4())
                    current_hash = audit_hash(
                        event_id=current_id,
                        timestamp=timestamp,
                        request_id=request_id,
                        tenant_id=tenant_id,
                        event_type=event_type,
                        actor=actor,
                        risk=risk,
                        payload=payload,
                        previous_hash=previous_hash,
                    )
                    event = AuditEvent(
                        id=current_id,
                        tenant_id=tenant_id,
                        event_type=event_type,
                        actor=actor,
                        risk=risk,
                        request_id=request_id,
                        previous_hash=previous_hash,
                        event_hash=current_hash,
                        payload=payload,
                        created_at=_parse_timestamp(timestamp),
                    )
                    session.add(event)
            return {
                "id": current_id,
                "timestamp": timestamp,
                "tenant_id": tenant_id,
                "event_type": event_type,
                "actor": actor,
                "risk": risk,
                "request_id": request_id,
                "previous_hash": previous_hash,
                "event_hash": current_hash,
                "payload": payload,
            }

        return await with_db_retry(operation)


async def audit_integrity_summary(tenant_id: str | None = None, limit: int = 5000) -> dict:
    async with async_session() as session:
        statement = select(AuditEvent).order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc()).limit(limit)
        if tenant_id is not None:
            statement = statement.where(AuditEvent.tenant_id == tenant_id)
        result = await session.execute(statement)
        rows = result.scalars().all()
    checked = 0
    legacy = 0
    hash_mismatches: list[str] = []
    broken_links: list[str] = []
    children_by_previous: dict[str, int] = {}
    heads_by_tenant: dict[str, set[str]] = {}
    hash_index = {row.event_hash for row in rows if row.event_hash}
    for row in rows:
        if not row.event_hash:
            legacy += 1
            continue
        heads_by_tenant.setdefault(row.tenant_id, set()).add(row.event_hash)
        if row.previous_hash:
            if row.previous_hash not in hash_index:
                broken_links.append(row.id)
            children_by_previous[row.previous_hash] = children_by_previous.get(row.previous_hash, 0) + 1
            for tenant_heads in heads_by_tenant.values():
                tenant_heads.discard(row.previous_hash)
        timestamp = _created_at(row.created_at)
        expected_hash = audit_hash(
            event_id=row.id,
            timestamp=timestamp,
            request_id=row.request_id,
            tenant_id=row.tenant_id,
            event_type=row.event_type,
            actor=row.actor,
            risk=row.risk,
            payload=row.payload or {},
            previous_hash=row.previous_hash,
        )
        if expected_hash != row.event_hash:
            hash_mismatches.append(row.id)
        checked += 1
    forks = [previous for previous, child_count in children_by_previous.items() if child_count > 1]
    tamper_detected = bool(hash_mismatches or broken_links)
    historical_forks = bool(forks) and not tamper_detected and legacy == 0
    if tamper_detected:
        chain_status = "tamper_detected"
    elif legacy:
        chain_status = "legacy_unhashed_events"
    elif historical_forks:
        chain_status = "historical_forks_no_tamper"
    else:
        chain_status = "ok"
    return {
        "checked_events": checked,
        "legacy_unhashed_events": legacy,
        "tamper_detected": tamper_detected,
        "hash_mismatch_event_ids": hash_mismatches[:10],
        "broken_link_event_ids": broken_links[:10],
        "chain_forks_detected": bool(forks),
        "chain_fork_count": len(forks),
        "historical_forks": historical_forks,
        "future_chain_hardened": True,
        "chain_status": chain_status,
        "head_hashes_by_tenant": {tenant: sorted(heads)[:5] for tenant, heads in heads_by_tenant.items()},
    }


async def record_auth_event(username: str, client: str, status: str, reason: str = "") -> None:
    row = AuthEvent(id=str(uuid.uuid4()), username=username, client_key=client, status=status, reason=reason)
    async with async_session() as session:
        async with session.begin():
            session.add(row)


async def count_recent_auth_failures(username: str, client: str, minutes: int = 5) -> int:
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    async with async_session() as session:
        result = await session.execute(
            select(func.count(AuthEvent.id)).where(
                AuthEvent.username == username,
                AuthEvent.client_key == client,
                AuthEvent.status == "failed",
                AuthEvent.created_at >= since,
            )
        )
        return int(result.scalar_one())


async def get_user_by_username(username: str) -> dict | None:
    await ensure_email_verification_storage()
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "username": row.username,
            "plan": row.plan,
            "active": row.active,
            "email_verified": bool(row.email_verified),
            "email_verified_at": _created_at(row.email_verified_at) if row.email_verified_at else None,
        }


async def create_email_verification_token(
    *,
    user_id: str,
    tenant_id: str,
    token_hash: str,
    expires_at: datetime,
) -> dict:
    await ensure_email_verification_storage()
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(EmailVerificationToken)
                .where(
                    EmailVerificationToken.user_id == user_id,
                    EmailVerificationToken.consumed_at.is_(None),
                )
                .values(consumed_at=now)
            )
            row = EmailVerificationToken(
                id=f"email-token-{uuid.uuid4().hex}",
                user_id=user_id,
                tenant_id=tenant_id,
                token_hash=token_hash,
                expires_at=expires_at,
                send_count=1,
                last_sent_at=now,
            )
            session.add(row)
    return {
        "id": row.id,
        "user_id": row.user_id,
        "tenant_id": row.tenant_id,
        "expires_at": expires_at.isoformat(),
        "send_count": row.send_count,
        "last_sent_at": now.isoformat(),
    }


async def verify_email_token_hash(token_hash: str) -> dict:
    await ensure_email_verification_storage()
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(EmailVerificationToken)
                .where(EmailVerificationToken.token_hash == token_hash)
                .order_by(EmailVerificationToken.created_at.desc(), EmailVerificationToken.id.desc())
                .limit(1)
            )
            token = result.scalar_one_or_none()
            if token is None or token.consumed_at is not None:
                return {"email_verified": False, "reason": "invalid_or_consumed_token"}
            expires_at = _aware_datetime(token.expires_at) or now
            if expires_at <= now:
                return {"email_verified": False, "reason": "expired_token"}
            user = await session.get(User, token.user_id)
            if user is None or user.tenant_id != token.tenant_id:
                return {"email_verified": False, "reason": "user_not_found"}
            user.email_verified = True
            user.email_verified_at = now
            user.active = True
            token.consumed_at = now
            return {
                "email_verified": True,
                "tenant_id": user.tenant_id,
                "user_id": user.id,
                "username": user.username,
                "plan": user.plan,
                "verified_at": now.isoformat(),
            }


async def mark_user_email_verified(username: str) -> dict | None:
    await ensure_email_verification_storage()
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            if user is None:
                return None
            user.email_verified = True
            user.email_verified_at = now
            user.active = True
            return {
                "user_id": user.id,
                "tenant_id": user.tenant_id,
                "username": user.username,
                "plan": user.plan,
                "verified_at": now.isoformat(),
            }


async def create_checkout_session_record(
    *,
    tenant_id: str,
    user_id: str,
    plan: str,
    billing_cycle: str,
    provider: str,
    provider_session_id: str | None,
    checkout_url: str | None,
    amount_cents: int,
    currency: str,
    status: str,
    metadata: dict,
) -> dict:
    await ensure_checkout_storage()
    row = CheckoutSession(
        id=f"checkout-{uuid.uuid4().hex}",
        tenant_id=tenant_id,
        user_id=user_id,
        plan=plan,
        billing_cycle=billing_cycle,
        provider=provider,
        provider_session_id=provider_session_id,
        checkout_url=checkout_url,
        amount_cents=amount_cents,
        currency=currency,
        status=status,
        metadata_json=metadata,
    )
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "user_id": row.user_id,
        "plan": row.plan,
        "billing_cycle": row.billing_cycle,
        "provider": row.provider,
        "provider_session_id": row.provider_session_id,
        "checkout_url": row.checkout_url,
        "amount_cents": row.amount_cents,
        "currency": row.currency,
        "status": row.status,
    }


async def update_checkout_session_provider(
    checkout_session_id: str,
    *,
    provider_session_id: str | None,
    checkout_url: str | None,
    status: str,
    metadata: dict,
) -> dict | None:
    await ensure_checkout_storage()
    async with async_session() as session:
        async with session.begin():
            row = await session.get(CheckoutSession, checkout_session_id, with_for_update=True)
            if row is None:
                return None
            row.provider_session_id = provider_session_id
            row.checkout_url = checkout_url
            row.status = status
            row.metadata_json = {**(row.metadata_json or {}), **metadata}
            await session.flush()
            await session.refresh(row)
            return {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "user_id": row.user_id,
                "plan": row.plan,
                "billing_cycle": row.billing_cycle,
                "provider": row.provider,
                "provider_session_id": row.provider_session_id,
                "checkout_url": row.checkout_url,
                "amount_cents": row.amount_cents,
                "currency": row.currency,
                "status": row.status,
            }


async def latest_checkout_session_for_tenant(tenant_id: str) -> dict | None:
    await ensure_checkout_storage()
    async with async_session() as session:
        result = await session.execute(
            select(CheckoutSession)
            .where(CheckoutSession.tenant_id == tenant_id)
            .order_by(CheckoutSession.created_at.desc(), CheckoutSession.id.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "user_id": row.user_id,
            "plan": row.plan,
            "billing_cycle": row.billing_cycle,
            "provider": row.provider,
            "provider_session_id": row.provider_session_id,
            "checkout_url": row.checkout_url,
            "status": row.status,
            "amount_cents": row.amount_cents,
            "currency": row.currency,
            "provider_customer_id": row.provider_customer_id,
            "provider_subscription_id": row.provider_subscription_id,
            "paid_at": _created_at(row.paid_at) if row.paid_at else None,
            "completed_at": _created_at(row.completed_at) if row.completed_at else None,
            "created_at": _created_at(row.created_at) if row.created_at else None,
            "updated_at": _created_at(row.updated_at) if row.updated_at else None,
        }


async def checkout_session_for_activation(
    *,
    provider: str,
    provider_session_id: str | None = None,
    checkout_session_id: str | None = None,
) -> dict | None:
    await ensure_checkout_storage()
    async with async_session() as session:
        if checkout_session_id:
            result = await session.execute(
                select(CheckoutSession)
                .where(CheckoutSession.provider == provider, CheckoutSession.id == checkout_session_id)
                .limit(1)
            )
        elif provider_session_id:
            result = await session.execute(
                select(CheckoutSession)
                .where(CheckoutSession.provider == provider, CheckoutSession.provider_session_id == provider_session_id)
                .limit(1)
            )
        else:
            return None
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "user_id": row.user_id,
            "plan": row.plan,
            "billing_cycle": row.billing_cycle,
            "provider": row.provider,
            "provider_session_id": row.provider_session_id,
            "status": row.status,
            "amount_cents": row.amount_cents,
            "currency": row.currency,
        }


async def record_payment_webhook_event(provider: str, event_id: str, event_type: str, payload: dict) -> dict:
    await ensure_stripe_webhook_storage()
    storage_event_id = f"{provider}:{event_id}" if not event_id.startswith(f"{provider}:") else event_id
    async with async_session() as session:
        async with session.begin():
            row = await session.get(StripeWebhookEvent, storage_event_id)
            if row is not None:
                return {
                    "id": row.id,
                    "event_type": row.event_type,
                    "status": row.status,
                    "already_processed": row.status in {"processed", "ignored"},
                    "checkout_session_id": row.checkout_session_id,
                }
            row = StripeWebhookEvent(
                id=storage_event_id,
                provider=provider,
                event_type=event_type,
                status="received",
                payload_json=payload,
            )
            session.add(row)
            return {
                "id": row.id,
                "event_type": row.event_type,
                "status": row.status,
                "already_processed": False,
                "checkout_session_id": None,
            }


async def record_stripe_webhook_event(event_id: str, event_type: str, payload: dict) -> dict:
    return await record_payment_webhook_event("stripe", event_id, event_type, payload)


async def mark_payment_webhook_event(
    provider: str,
    event_id: str,
    status: str,
    *,
    checkout_session_id: str | None = None,
    error: str | None = None,
) -> None:
    await ensure_stripe_webhook_storage()
    storage_event_id = f"{provider}:{event_id}" if not event_id.startswith(f"{provider}:") else event_id
    async with async_session() as session:
        async with session.begin():
            row = await session.get(StripeWebhookEvent, storage_event_id)
            if row is None:
                return
            row.status = status
            row.checkout_session_id = checkout_session_id
            row.error = error
            if status in {"processed", "ignored", "error"}:
                row.processed_at = datetime.now(timezone.utc)


async def mark_stripe_webhook_event(
    event_id: str,
    status: str,
    *,
    checkout_session_id: str | None = None,
    error: str | None = None,
) -> None:
    await mark_payment_webhook_event(
        "stripe",
        event_id,
        status,
        checkout_session_id=checkout_session_id,
        error=error,
    )


async def activate_checkout_session_from_webhook(
    *,
    provider: str = "stripe",
    provider_session_id: str | None = None,
    checkout_session_id: str | None = None,
    event_id: str,
    provider_customer_id: str | None,
    provider_subscription_id: str | None,
    amount_cents: int | None,
    currency: str | None,
    paid_at: datetime,
    current_period_start: datetime | None,
    current_period_end: datetime | None,
    limits: dict,
    metadata: dict,
) -> dict:
    await ensure_checkout_storage()
    async with async_session() as session:
        async with session.begin():
            if checkout_session_id:
                result = await session.execute(
                    select(CheckoutSession)
                    .where(CheckoutSession.provider == provider, CheckoutSession.id == checkout_session_id)
                    .limit(1)
                    .with_for_update()
                )
            elif provider_session_id:
                result = await session.execute(
                    select(CheckoutSession)
                    .where(CheckoutSession.provider == provider, CheckoutSession.provider_session_id == provider_session_id)
                    .limit(1)
                    .with_for_update()
                )
            else:
                return {"activated": False, "reason": "checkout_session_reference_missing", "provider": provider}
            checkout = result.scalar_one_or_none()
            if checkout is None:
                return {
                    "activated": False,
                    "reason": "checkout_session_not_found",
                    "provider": provider,
                    "provider_session_id": provider_session_id,
                    "checkout_session_id": checkout_session_id,
                }

            mismatches = {}
            for key, expected in {
                "tenant_id": checkout.tenant_id,
                "user_id": checkout.user_id,
                "plan": checkout.plan,
                "billing_cycle": checkout.billing_cycle,
            }.items():
                value = metadata.get(key)
                if value and str(value) != str(expected):
                    mismatches[key] = {"metadata": value, "checkout_session": expected}
            if mismatches:
                return {
                    "activated": False,
                    "reason": "checkout_session_metadata_mismatch",
                    "checkout_session_id": checkout.id,
                    "mismatches": mismatches,
                }

            if checkout.status in {"paid", "completed"}:
                return {
                    "activated": True,
                    "already_activated": True,
                    "checkout_session_id": checkout.id,
                    "tenant_id": checkout.tenant_id,
                    "user_id": checkout.user_id,
                    "plan": checkout.plan,
                    "billing_cycle": checkout.billing_cycle,
                    "status": checkout.status,
                }

            if amount_cents is not None and int(amount_cents) != int(checkout.amount_cents or 0):
                return {
                    "activated": False,
                    "reason": "checkout_amount_mismatch",
                    "checkout_session_id": checkout.id,
                    "amount_cents": amount_cents,
                    "expected_amount_cents": checkout.amount_cents,
                }
            if currency and currency.upper() != str(checkout.currency or "").upper():
                return {
                    "activated": False,
                    "reason": "checkout_currency_mismatch",
                    "checkout_session_id": checkout.id,
                    "currency": currency,
                    "expected_currency": checkout.currency,
                }

            now = datetime.now(timezone.utc)
            checkout.status = "paid"
            checkout.provider_customer_id = provider_customer_id
            checkout.provider_subscription_id = provider_subscription_id
            checkout.paid_at = paid_at
            checkout.completed_at = now
            checkout.metadata_json = {
                **(checkout.metadata_json or {}),
                "provider_event_id": event_id,
                "provider_customer_id": provider_customer_id,
                "provider_subscription_id": provider_subscription_id,
                f"{provider}_event_id": event_id,
                f"{provider}_customer_id": provider_customer_id,
                f"{provider}_subscription_id": provider_subscription_id,
                "paid_at": paid_at.isoformat(),
                "plan_activated": checkout.plan,
            }

            subscription = (
                await session.execute(select(Subscription).where(Subscription.tenant_id == checkout.tenant_id, Subscription.status == "active"))
            ).scalar_one_or_none()
            if subscription is None:
                subscription = Subscription(
                    id=f"subscription-{uuid.uuid4().hex}",
                    tenant_id=checkout.tenant_id,
                    plan=checkout.plan,
                    status="active",
                    limits=limits,
                )
                session.add(subscription)
            subscription.plan = checkout.plan
            subscription.status = "active"
            subscription.limits = limits
            subscription.billing_cycle = checkout.billing_cycle
            subscription.provider = provider
            subscription.provider_subscription_id = provider_subscription_id
            subscription.activated_at = paid_at
            subscription.current_period_start = current_period_start or paid_at
            subscription.current_period_end = current_period_end

            users = await session.execute(select(User).where(User.tenant_id == checkout.tenant_id))
            for user in users.scalars().all():
                user.plan = checkout.plan
                user_plan = await session.get(UserBusinessPlan, user.id)
                if user_plan is None:
                    session.add(
                        UserBusinessPlan(
                            user_id=user.id,
                            tenant_id=checkout.tenant_id,
                            plan_id=business_plan_from_legacy(checkout.plan),
                            estado="active",
                        )
                    )
                else:
                    user_plan.plan_id = business_plan_from_legacy(checkout.plan)
                    user_plan.estado = "active"

            await session.flush()
            return {
                "activated": True,
                "already_activated": False,
                "checkout_session_id": checkout.id,
                "tenant_id": checkout.tenant_id,
                "user_id": checkout.user_id,
                "plan": checkout.plan,
                "billing_cycle": checkout.billing_cycle,
                "status": checkout.status,
                "provider": provider,
                "provider_session_id": provider_session_id or checkout.provider_session_id,
                "provider_customer_id": provider_customer_id,
                "provider_subscription_id": provider_subscription_id,
                "stripe_session_id": provider_session_id if provider == "stripe" else None,
                "stripe_customer_id": provider_customer_id if provider == "stripe" else None,
                "stripe_subscription_id": provider_subscription_id if provider == "stripe" else None,
                "mercadopago_preapproval_id": provider_session_id if provider == "mercadopago" else None,
                "amount_cents": checkout.amount_cents,
                "currency": checkout.currency,
                "paid_at": paid_at.isoformat(),
            }


async def revoke_token(jti: str, subject: str, tenant_id: str, expires_at: datetime, reason: str = "logout") -> None:
    row = RevokedToken(jti=jti, subject=subject, tenant_id=tenant_id, expires_at=expires_at, reason=reason)
    async with async_session() as session:
        async with session.begin():
            existing = await session.get(RevokedToken, jti)
            if existing is None:
                session.add(row)


async def is_token_revoked(jti: str) -> bool:
    async with async_session() as session:
        row = await session.get(RevokedToken, jti)
        return row is not None


async def count_audit_events(tenant_id: str | None = None) -> int:
    async with async_session() as session:
        statement = select(func.count(AuditEvent.id))
        if tenant_id is not None:
            statement = statement.where(AuditEvent.tenant_id == tenant_id)
        result = await session.execute(statement)
        return int(result.scalar_one())


async def dashboard_counts(tenant_id: str) -> dict[str, int]:
    async with async_session() as session:
        values = {
            "alerts": await session.scalar(select(func.count(Alert.id)).where(Alert.tenant_id == tenant_id)),
            "open_alerts": await session.scalar(select(func.count(Alert.id)).where(Alert.tenant_id == tenant_id, Alert.status == "open")),
            "recommendations": await session.scalar(select(func.count(Recommendation.id)).where(Recommendation.tenant_id == tenant_id)),
            "documents": await session.scalar(select(func.count(Document.id)).where(Document.tenant_id == tenant_id)),
            "workflows": await session.scalar(select(func.count(WorkflowRun.id)).where(WorkflowRun.tenant_id == tenant_id)),
            "ai_requests": await session.scalar(select(func.count(AIRequest.id)).where(AIRequest.tenant_id == tenant_id)),
            "audit_events": await session.scalar(select(func.count(AuditEvent.id)).where(AuditEvent.tenant_id == tenant_id)),
        }
    return {key: int(value or 0) for key, value in values.items()}


async def tenant_usage_counts(tenant_id: str) -> dict[str, int]:
    counts = await dashboard_counts(tenant_id)
    async with async_session() as session:
        users = await session.scalar(select(func.count(User.id)).where(User.tenant_id == tenant_id, User.active.is_(True)))
    counts["users"] = int(users or 0)
    return counts


def current_student_doctor_month(now: datetime | None = None) -> tuple[int, int, str]:
    current = now or datetime.now(timezone.utc)
    return current.year, current.month, f"{current.year:04d}-{current.month:02d}"


def _student_doctor_usage_dict(row: StudentDoctorUsage | None, *, user_id: str, tenant_id: str, year: int, month: int, month_key: str, questions_limit: int = 5) -> dict:
    questions_used = int(row.questions_used if row is not None else 0)
    limit = int(row.questions_limit if row is not None else questions_limit)
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "month_key": month_key,
        "year": year,
        "month": month,
        "questions_used": questions_used,
        "questions_limit": limit,
        "questions_remaining": max(0, limit - questions_used),
        "timestamps": list(row.timestamps or []) if row is not None else [],
        "last_question": row.last_question if row is not None else None,
        "status": row.status if row is not None else "active",
        "created_at": _created_at(row.created_at) if row is not None and row.created_at else None,
        "updated_at": _created_at(row.updated_at) if row is not None and row.updated_at else None,
        "last_asked_at": _created_at(row.last_asked_at) if row is not None and row.last_asked_at else None,
    }


async def student_doctor_usage_status(user_id: str, tenant_id: str, questions_limit: int = 5) -> dict:
    await ensure_student_doctor_storage()
    year, month, month_key = current_student_doctor_month()
    async with async_session() as session:
        result = await session.execute(
            select(StudentDoctorUsage)
            .where(
                StudentDoctorUsage.user_id == user_id,
                StudentDoctorUsage.tenant_id == tenant_id,
                StudentDoctorUsage.month_key == month_key,
            )
            .order_by(StudentDoctorUsage.created_at.desc(), StudentDoctorUsage.id.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
    return _student_doctor_usage_dict(row, user_id=user_id, tenant_id=tenant_id, year=year, month=month, month_key=month_key, questions_limit=questions_limit)


async def record_student_doctor_success(user_id: str, tenant_id: str, question: str, questions_limit: int = 5) -> dict:
    await ensure_student_doctor_storage()
    year, month, month_key = current_student_doctor_month()
    asked_at = datetime.now(timezone.utc)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(StudentDoctorUsage)
                .where(
                    StudentDoctorUsage.user_id == user_id,
                    StudentDoctorUsage.tenant_id == tenant_id,
                    StudentDoctorUsage.month_key == month_key,
                )
                .order_by(StudentDoctorUsage.created_at.desc(), StudentDoctorUsage.id.desc())
                .limit(1)
                .with_for_update()
            )
            row = result.scalar_one_or_none()
            if row is None:
                row = StudentDoctorUsage(
                    id=f"student-doctor-{uuid.uuid4().hex}",
                    user_id=user_id,
                    tenant_id=tenant_id,
                    month_key=month_key,
                    year=year,
                    month=month,
                    questions_used=0,
                    questions_limit=questions_limit,
                    timestamps=[],
                    status="active",
                )
                session.add(row)
                await session.flush()
            limit = int(row.questions_limit or questions_limit)
            if int(row.questions_used or 0) >= limit:
                row.status = "limit_reached"
                return _student_doctor_usage_dict(row, user_id=user_id, tenant_id=tenant_id, year=year, month=month, month_key=month_key, questions_limit=questions_limit)
            timestamps = list(row.timestamps or [])
            timestamps.append(asked_at.isoformat())
            row.questions_used = int(row.questions_used or 0) + 1
            row.questions_limit = limit
            row.timestamps = timestamps
            row.last_question = question
            row.last_asked_at = asked_at
            row.status = "limit_reached" if row.questions_used >= limit else "active"
            await session.flush()
            await session.refresh(row)
            return _student_doctor_usage_dict(row, user_id=user_id, tenant_id=tenant_id, year=year, month=month, month_key=month_key, questions_limit=questions_limit)


async def create_tenant_with_admin(
    *,
    tenant_id: str,
    tenant_name: str,
    admin_username: str,
    password_hash: str,
    plan: str,
    limits: dict,
    account_type: str = "business",
    trial_days: int = 0,
    company_payload: dict | None = None,
    email_verified: bool = False,
    subscription_status: str = "active",
) -> dict:
    await ensure_onboarding_progress_storage()
    await ensure_email_verification_storage()
    trial_started_at = datetime.now(timezone.utc) if trial_days > 0 else None
    trial_ends_at = trial_started_at + timedelta(days=trial_days) if trial_started_at is not None else None
    verified_at = datetime.now(timezone.utc) if email_verified else None
    async with async_session() as session:
        async with session.begin():
            existing_tenant = await session.get(Tenant, tenant_id)
            existing_user = (
                await session.execute(select(User).where(User.username == admin_username))
            ).scalar_one_or_none()
            if existing_tenant is not None:
                return {"created": False, "reason": "tenant_exists"}
            if existing_user is not None:
                return {"created": False, "reason": "username_exists"}
            if company_payload is not None:
                existing_company = (
                    await session.execute(select(Company).where(Company.ruc == company_payload["ruc"]))
                ).scalar_one_or_none()
                if existing_company is not None:
                    return {"created": False, "reason": "ruc_exists"}
            tenant = Tenant(id=tenant_id, name=tenant_name, country="PE", account_type=account_type, status="active")
            user = User(
                id=f"user-{uuid.uuid4().hex}",
                tenant_id=tenant_id,
                username=admin_username,
                password_hash=password_hash,
                role="tenant_admin",
                plan=plan,
                active=email_verified,
                email_verified=email_verified,
                email_verified_at=verified_at,
            )
            subscription = Subscription(
                id=f"subscription-{uuid.uuid4().hex}",
                tenant_id=tenant_id,
                plan=plan,
                status=subscription_status,
                limits=limits,
                trial_status="active" if trial_days > 0 else "none",
                trial_started_at=trial_started_at,
                trial_ends_at=trial_ends_at,
            )
            user_plan = UserBusinessPlan(
                user_id=user.id,
                tenant_id=tenant_id,
                plan_id=business_plan_from_legacy(plan),
                estado="active",
            )
            progress = OnboardingProgress(
                tenant_id=tenant_id,
                user_id=user.id,
                account_created=True,
                company_registered=company_payload is not None,
                ruc_registered=company_payload is not None and bool(company_payload.get("ruc")),
                videos_seen=[],
                sunat_auxiliary_prepared=False,
                initial_diagnosis_pending=True,
                completed=False,
                checklist={},
            )
            rows = [tenant, user, subscription, user_plan, progress]
            company = None
            workspace = None
            context = None
            if company_payload is not None:
                company = Company(id=f"company-{uuid.uuid4().hex}", tenant_id=tenant_id, **company_payload)
                workspace = Workspace(
                    id=f"workspace-{uuid.uuid4().hex}",
                    tenant_id=tenant_id,
                    nombre=company_payload.get("razon_social") or tenant_name,
                    propietario=user.id,
                    empresa_id=company.id,
                    estado="active",
                    plan_id=business_plan_from_legacy(plan),
                )
                membership = WorkspaceMembership(
                    user_id=user.id,
                    workspace_id=workspace.id,
                    tenant_id=tenant_id,
                    role_id="ADMIN",
                    estado="active",
                )
                context = ActiveOperationalContext(
                    user_id=user.id,
                    tenant_id=tenant_id,
                    active_company_id=company.id,
                    active_workspace_id=workspace.id,
                    active_user_id=user.id,
                )
                rows.extend([company, workspace, membership, context])
            session.add_all(rows)
            await session.flush()
            result = {
                "created": True,
                "tenant_id": tenant_id,
                "admin_username": admin_username,
                "user_id": user.id,
                "plan": plan,
                "account_type": account_type,
                "trial_status": subscription.trial_status,
                "trial_started_at": _created_at(subscription.trial_started_at) if subscription.trial_started_at else None,
                "trial_ends_at": _created_at(subscription.trial_ends_at) if subscription.trial_ends_at else None,
                "company": _company_dict(company) if company is not None else None,
                "workspace": _workspace_dict(workspace) if workspace is not None else None,
                "context": _context_dict(context, user.id, tenant_id) if context is not None else None,
            }
    return result


async def update_tenant_subscription(tenant_id: str, plan: str, limits: dict) -> dict | None:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Subscription).where(Subscription.tenant_id == tenant_id, Subscription.status == "active")
            )
            subscription = result.scalar_one_or_none()
            if subscription is None:
                subscription = Subscription(
                    id=f"subscription-{uuid.uuid4().hex}",
                    tenant_id=tenant_id,
                    plan=plan,
                    status="active",
                    limits=limits,
                )
                session.add(subscription)
            else:
                subscription.plan = plan
                subscription.limits = limits
                subscription.billing_cycle = None
                subscription.provider = None
                subscription.provider_subscription_id = None
                subscription.activated_at = None
                subscription.current_period_start = None
                subscription.current_period_end = None
            users = await session.execute(select(User).where(User.tenant_id == tenant_id))
            for user in users.scalars().all():
                user.plan = plan
                user_plan = await session.get(UserBusinessPlan, user.id)
                if user_plan is None:
                    session.add(
                        UserBusinessPlan(
                            user_id=user.id,
                            tenant_id=tenant_id,
                            plan_id=business_plan_from_legacy(plan),
                            estado="active",
                        )
                    )
                else:
                    user_plan.plan_id = business_plan_from_legacy(plan)
                    user_plan.estado = "active"
    return {"tenant_id": tenant_id, "plan": plan, "limits": limits}


async def current_subscription(tenant_id: str) -> dict | None:
    async with async_session() as session:
        result = await session.execute(
            select(Subscription)
            .where(Subscription.tenant_id == tenant_id)
            .order_by(Subscription.created_at.desc(), Subscription.id.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _subscription_dict(row)


def _aware_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return None


def _subscription_dict(row: Subscription) -> dict:
    now = datetime.now(timezone.utc)
    trial_started_at = _aware_datetime(row.trial_started_at)
    trial_ends_at = _aware_datetime(row.trial_ends_at)
    current_period_end = _aware_datetime(row.current_period_end)
    period_expired = row.status == "active" and current_period_end is not None and current_period_end <= now
    normalized_status = "expired" if period_expired else row.status
    stored_trial_status = row.trial_status or "none"
    trial_active = stored_trial_status == "active" and trial_ends_at is not None and trial_ends_at > now
    trial_expired = stored_trial_status == "active" and trial_ends_at is not None and trial_ends_at <= now
    normalized_trial_status = "expired" if trial_expired else stored_trial_status
    days_remaining = 0
    if trial_active and trial_ends_at is not None:
        seconds_remaining = max(0, int((trial_ends_at - now).total_seconds()))
        days_remaining = max(1, (seconds_remaining + 86399) // 86400)
    return {
        "tenant_id": row.tenant_id,
        "plan": row.plan,
        "plan_effective": "premium" if trial_active else ("free" if period_expired else row.plan),
        "limits": row.limits or {},
        "status": normalized_status,
        "billing_cycle": row.billing_cycle,
        "interval": {"monthly": "monthly", "annual": "yearly"}.get(row.billing_cycle or "", row.billing_cycle),
        "provider": row.provider,
        "provider_subscription_id": row.provider_subscription_id,
        "activated_at": _created_at(row.activated_at) if row.activated_at else None,
        "current_period_start": _created_at(row.current_period_start) if row.current_period_start else None,
        "current_period_end": _created_at(row.current_period_end) if row.current_period_end else None,
        "started_at": _created_at(row.activated_at or row.created_at) if (row.activated_at or row.created_at) else None,
        "ends_at": _created_at(row.current_period_end) if row.current_period_end else None,
        "trial_status": normalized_trial_status,
        "trial_active": trial_active,
        "trial_expired": trial_expired,
        "trial_days_remaining": days_remaining,
        "trial_started_at": _created_at(row.trial_started_at) if row.trial_started_at else None,
        "trial_ends_at": _created_at(row.trial_ends_at) if row.trial_ends_at else None,
    }


def _onboarding_progress_dict(
    row: OnboardingProgress,
    *,
    companies: list[Company],
    workspaces: list[Workspace],
    connections: list[SunatConnection],
    subscription: Subscription | None,
) -> dict:
    videos_seen = list(row.videos_seen or [])
    company_registered = bool(row.company_registered or companies)
    ruc_registered = bool(row.ruc_registered or any(company.ruc for company in companies))
    sunat_auxiliary_prepared = bool(
        row.sunat_auxiliary_prepared
        or any(connection.auxiliary_user_alias for connection in connections if connection.estado != "DISABLED")
    )
    subscription_payload = _subscription_dict(subscription) if subscription is not None else None
    trial_active = bool((subscription_payload or {}).get("trial_active"))
    checklist = {
        **(row.checklist or {}),
        "account_created": True,
        "company_registered": company_registered,
        "ruc_registered": ruc_registered,
        "videos_seen": len(set(videos_seen)) >= 3,
        "sunat_auxiliary_prepared": sunat_auxiliary_prepared,
        "initial_diagnosis_pending": bool(row.initial_diagnosis_pending),
        "trial_active": trial_active,
    }
    ready_for_testing = bool(
        checklist["account_created"]
        and (company_registered or not companies)
        and len(set(videos_seen)) >= 3
        and (sunat_auxiliary_prepared or not companies)
    )
    return {
        "tenant_id": row.tenant_id,
        "user_id": row.user_id,
        "account_created": True,
        "company_registered": company_registered,
        "ruc_registered": ruc_registered,
        "videos_seen": videos_seen,
        "sunat_auxiliary_prepared": sunat_auxiliary_prepared,
        "initial_diagnosis_pending": bool(row.initial_diagnosis_pending),
        "completed": bool(row.completed or ready_for_testing),
        "checklist": checklist,
        "ready_for_testing": ready_for_testing,
        "plan_base": (subscription_payload or {}).get("plan"),
        "plan_effective": (subscription_payload or {}).get("plan_effective"),
        "trial": {
            "status": (subscription_payload or {}).get("trial_status", "none"),
            "active": (subscription_payload or {}).get("trial_active", False),
            "expired": (subscription_payload or {}).get("trial_expired", False),
            "days_remaining": (subscription_payload or {}).get("trial_days_remaining", 0),
            "started_at": (subscription_payload or {}).get("trial_started_at"),
            "ends_at": (subscription_payload or {}).get("trial_ends_at"),
        },
        "companies_count": len(companies),
        "workspaces_count": len(workspaces),
        "sunat_connections_count": len(connections),
        "created_at": _created_at(row.created_at),
        "updated_at": _created_at(row.updated_at),
    }


async def _ensure_progress_row(session, tenant_id: str, user_id: str) -> OnboardingProgress:
    row = await session.get(OnboardingProgress, tenant_id)
    if row is None:
        row = OnboardingProgress(
            tenant_id=tenant_id,
            user_id=user_id,
            account_created=True,
            company_registered=False,
            ruc_registered=False,
            videos_seen=[],
            sunat_auxiliary_prepared=False,
            initial_diagnosis_pending=True,
            completed=False,
            checklist={},
        )
        session.add(row)
        await session.flush()
        await session.refresh(row)
    return row


async def onboarding_progress(tenant_id: str, user_id: str) -> dict:
    await ensure_onboarding_progress_storage()
    async with async_session() as session:
        async with session.begin():
            row = await _ensure_progress_row(session, tenant_id, user_id)
            companies = list((await session.execute(select(Company).where(Company.tenant_id == tenant_id))).scalars().all())
            workspaces = list((await session.execute(select(Workspace).where(Workspace.tenant_id == tenant_id))).scalars().all())
            connections = list((await session.execute(select(SunatConnection).where(SunatConnection.tenant_id == tenant_id))).scalars().all())
            subscription = (
                await session.execute(select(Subscription).where(Subscription.tenant_id == tenant_id, Subscription.status == "active"))
            ).scalar_one_or_none()
            row.company_registered = bool(companies)
            row.ruc_registered = any(company.ruc for company in companies)
            row.sunat_auxiliary_prepared = any(
                connection.auxiliary_user_alias for connection in connections if connection.estado != "DISABLED"
            )
            await session.flush()
            await session.refresh(row)
            return _onboarding_progress_dict(row, companies=companies, workspaces=workspaces, connections=connections, subscription=subscription)


async def mark_onboarding_video_seen(tenant_id: str, user_id: str, video_id: str) -> dict:
    await ensure_onboarding_progress_storage()
    async with async_session() as session:
        async with session.begin():
            row = await _ensure_progress_row(session, tenant_id, user_id)
            videos_seen = list(row.videos_seen or [])
            if video_id not in videos_seen:
                videos_seen.append(video_id)
            row.videos_seen = videos_seen
            companies = list((await session.execute(select(Company).where(Company.tenant_id == tenant_id))).scalars().all())
            workspaces = list((await session.execute(select(Workspace).where(Workspace.tenant_id == tenant_id))).scalars().all())
            connections = list((await session.execute(select(SunatConnection).where(SunatConnection.tenant_id == tenant_id))).scalars().all())
            subscription = (
                await session.execute(select(Subscription).where(Subscription.tenant_id == tenant_id, Subscription.status == "active"))
            ).scalar_one_or_none()
            await session.flush()
            await session.refresh(row)
            return _onboarding_progress_dict(row, companies=companies, workspaces=workspaces, connections=connections, subscription=subscription)


async def set_tenant_trial(tenant_id: str, *, active: bool, days: int = 7) -> dict | None:
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        async with session.begin():
            subscription = (
                await session.execute(select(Subscription).where(Subscription.tenant_id == tenant_id, Subscription.status == "active"))
            ).scalar_one_or_none()
            if subscription is None:
                return None
            if active:
                subscription.trial_status = "active"
                subscription.trial_started_at = now
                subscription.trial_ends_at = now + timedelta(days=max(1, min(days, 30)))
            else:
                subscription.trial_status = "inactive"
                subscription.trial_ends_at = now
            await session.flush()
            await session.refresh(subscription)
            return _subscription_dict(subscription)


async def admin_change_tenant_plan(tenant_id: str, plan: str, limits: dict) -> dict | None:
    return await update_tenant_subscription(tenant_id, plan, limits)


async def admin_list_users() -> list[dict]:
    await ensure_onboarding_progress_storage()
    async with async_session() as session:
        users = list((await session.execute(select(User).order_by(User.created_at.desc(), User.username.asc()))).scalars().all())
        rows: list[dict] = []
        for user in users:
            tenant = await session.get(Tenant, user.tenant_id)
            subscription = (
                await session.execute(select(Subscription).where(Subscription.tenant_id == user.tenant_id, Subscription.status == "active"))
            ).scalar_one_or_none()
            companies = list((await session.execute(select(Company).where(Company.tenant_id == user.tenant_id))).scalars().all())
            workspaces = list((await session.execute(select(Workspace).where(Workspace.tenant_id == user.tenant_id))).scalars().all())
            connections = list((await session.execute(select(SunatConnection).where(SunatConnection.tenant_id == user.tenant_id))).scalars().all())
            progress = await session.get(OnboardingProgress, user.tenant_id)
            if progress is None:
                progress = OnboardingProgress(tenant_id=user.tenant_id, user_id=user.id)
                session.add(progress)
                await session.flush()
                await session.refresh(progress)
            subscription_payload = _subscription_dict(subscription) if subscription is not None else None
            progress_payload = _onboarding_progress_dict(
                progress,
                companies=companies,
                workspaces=workspaces,
                connections=connections,
                subscription=subscription,
            )
            rows.append(
                {
                    "user_id": user.id,
                    "tenant_id": user.tenant_id,
                    "tenant_name": tenant.name if tenant is not None else user.tenant_id,
                    "username": user.username,
                    "email": user.username if "@" in user.username else "",
                    "name": tenant.name if tenant is not None else user.username,
                    "role": user.role,
                    "plan": user.plan,
                    "plan_effective": (subscription_payload or {}).get("plan_effective", user.plan),
                    "subscription": subscription_payload,
                    "trial": progress_payload["trial"],
                    "company": _company_dict(companies[0]) if companies else None,
                    "workspace": _workspace_dict(workspaces[0]) if workspaces else None,
                    "onboarding": progress_payload,
                    "sunat_auxiliary_prepared": progress_payload["sunat_auxiliary_prepared"],
                    "active": bool(user.active),
                    "created_at": _created_at(user.created_at),
                }
            )
        await session.commit()
    return rows


async def tenant_id_for_user(user_id: str) -> str | None:
    async with async_session() as session:
        user = await session.get(User, user_id)
        return user.tenant_id if user is not None and user.active else None


def _company_dict(row: Company) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "ruc": row.ruc,
        "razon_social": row.razon_social,
        "nombre_comercial": row.nombre_comercial,
        "regimen_tributario": row.regimen_tributario,
        "estado": row.estado,
        "pais": row.pais,
        "moneda": row.moneda,
        "created_at": _created_at(row.created_at),
        "updated_at": _created_at(row.updated_at),
    }


def _workspace_dict(row: Workspace) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "nombre": row.nombre,
        "propietario": row.propietario,
        "empresa_id": row.empresa_id,
        "estado": row.estado,
        "plan_id": row.plan_id,
        "created_at": _created_at(row.created_at),
        "updated_at": _created_at(row.updated_at),
    }


def _membership_dict(row: WorkspaceMembership) -> dict:
    return {
        "user_id": row.user_id,
        "workspace_id": row.workspace_id,
        "tenant_id": row.tenant_id,
        "role_id": row.role_id,
        "estado": row.estado,
        "created_at": _created_at(row.created_at),
    }


def _context_dict(row: ActiveOperationalContext | None, user_id: str, tenant_id: str) -> dict:
    if row is None:
        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "active_company_id": None,
            "active_workspace_id": None,
            "active_user_id": user_id,
            "updated_at": None,
        }
    return {
        "user_id": row.user_id,
        "tenant_id": row.tenant_id,
        "active_company_id": row.active_company_id,
        "active_workspace_id": row.active_workspace_id,
        "active_user_id": row.active_user_id,
        "updated_at": _created_at(row.updated_at),
    }


async def get_user_by_id(tenant_id: str, user_id: str) -> dict | None:
    async with async_session() as session:
        row = await session.get(User, user_id)
        if row is None or row.tenant_id != tenant_id or not row.active:
            return None
        return {"id": row.id, "tenant_id": row.tenant_id, "username": row.username, "role": row.role, "plan": row.plan}


async def list_business_roles() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(select(BusinessRole).order_by(BusinessRole.id.asc()))
        rows = result.scalars().all()
    return [
        {"id": row.id, "nombre": row.nombre, "permissions": row.permissions or [], "estado": row.estado}
        for row in rows
    ]


async def list_business_plans() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(select(BusinessPlan).order_by(BusinessPlan.id.asc()))
        rows = result.scalars().all()
    return [
        {"id": row.id, "nombre": row.nombre, "limits": row.limits or {}, "features": row.features or [], "estado": row.estado}
        for row in rows
    ]


async def business_role_permissions(role_id: str) -> list[str]:
    async with async_session() as session:
        row = await session.get(BusinessRole, role_id)
        if row is None or row.estado != "active":
            return []
        return list(row.permissions or [])


async def business_role_exists(role_id: str) -> bool:
    async with async_session() as session:
        row = await session.get(BusinessRole, role_id)
        return bool(row and row.estado == "active")


async def business_plan_exists(plan_id: str) -> bool:
    async with async_session() as session:
        row = await session.get(BusinessPlan, plan_id)
        return bool(row and row.estado == "active")


async def create_company(tenant_id: str, payload: dict) -> dict | None:
    async with async_session() as session:
        async with session.begin():
            existing = (await session.execute(select(Company).where(Company.ruc == payload["ruc"]))).scalar_one_or_none()
            if existing is not None:
                return None
            row = Company(id=f"company-{uuid.uuid4().hex}", tenant_id=tenant_id, **payload)
            session.add(row)
            await session.flush()
            await session.refresh(row)
            return _company_dict(row)


async def list_companies(tenant_id: str) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Company).where(Company.tenant_id == tenant_id).order_by(Company.created_at.desc(), Company.id.desc())
        )
        rows = result.scalars().all()
    return [_company_dict(row) for row in rows]


async def get_company_for_tenant(tenant_id: str, company_id: str) -> dict | None:
    async with async_session() as session:
        row = await session.get(Company, company_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return _company_dict(row)


async def company_access_entry_by_ruc(ruc: str) -> dict | None:
    await ensure_sunat_credential_storage()
    await ensure_checkout_storage()
    clean_ruc = ruc.strip()
    async with async_session() as session:
        company = (
            await session.execute(
                select(Company)
                .where(Company.ruc == clean_ruc)
                .order_by(Company.created_at.desc(), Company.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if company is None:
            return None

        user = (
            await session.execute(
                select(User)
                .where(User.tenant_id == company.tenant_id, User.role == "tenant_admin", User.active == True)  # noqa: E712
                .order_by(User.created_at.asc(), User.id.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if user is None:
            user = (
                await session.execute(
                    select(User)
                    .where(User.tenant_id == company.tenant_id, User.active == True)  # noqa: E712
                    .order_by(User.created_at.asc(), User.id.asc())
                    .limit(1)
                )
            ).scalar_one_or_none()
        if user is None:
            return None

        workspace = (
            await session.execute(
                select(Workspace)
                .where(Workspace.tenant_id == company.tenant_id, Workspace.empresa_id == company.id, Workspace.estado == "active")
                .order_by(Workspace.created_at.desc(), Workspace.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if workspace is None:
            return None

        context = await session.get(ActiveOperationalContext, user.id)
        subscription = (
            await session.execute(
                select(Subscription)
                .where(Subscription.tenant_id == company.tenant_id)
                .order_by(Subscription.created_at.desc(), Subscription.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        checkout = (
            await session.execute(
                select(CheckoutSession)
                .where(CheckoutSession.tenant_id == company.tenant_id)
                .order_by(CheckoutSession.created_at.desc(), CheckoutSession.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        connection = (
            await session.execute(
                select(SunatConnection)
                .where(
                    SunatConnection.tenant_id == company.tenant_id,
                    SunatConnection.empresa_id == company.id,
                    SunatConnection.workspace_id == workspace.id,
                    SunatConnection.estado != "DISABLED",
                )
                .order_by(SunatConnection.created_at.desc(), SunatConnection.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        credential = (
            await session.execute(
                select(SunatCredential)
                .where(
                    SunatCredential.tenant_id == company.tenant_id,
                    SunatCredential.empresa_id == company.id,
                    SunatCredential.workspace_id == workspace.id,
                )
                .order_by(SunatCredential.created_at.desc(), SunatCredential.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        return {
            "company": _company_dict(company),
            "workspace": _workspace_dict(workspace),
            "context": _context_dict(context, user.id, company.tenant_id),
            "user": {
                "id": user.id,
                "tenant_id": user.tenant_id,
                "username": user.username,
                "role": user.role,
                "plan": user.plan,
                "email_verified": bool(user.email_verified),
            },
            "subscription": _subscription_dict(subscription) if subscription is not None else None,
            "checkout": {
                "id": checkout.id,
                "tenant_id": checkout.tenant_id,
                "user_id": checkout.user_id,
                "plan": checkout.plan,
                "billing_cycle": checkout.billing_cycle,
                "provider": checkout.provider,
                "provider_session_id": checkout.provider_session_id,
                "checkout_url": checkout.checkout_url,
                "status": checkout.status,
                "amount_cents": checkout.amount_cents,
                "currency": checkout.currency,
                "provider_customer_id": checkout.provider_customer_id,
                "provider_subscription_id": checkout.provider_subscription_id,
                "paid_at": _created_at(checkout.paid_at) if checkout.paid_at else None,
                "completed_at": _created_at(checkout.completed_at) if checkout.completed_at else None,
                "created_at": _created_at(checkout.created_at) if checkout.created_at else None,
                "updated_at": _created_at(checkout.updated_at) if checkout.updated_at else None,
            }
            if checkout is not None
            else None,
            "connection": _sunat_connection_dict(connection) if connection is not None else None,
            "credential": _sunat_credential_dict(
                credential,
                username_masked=(connection.auxiliary_user_alias if connection is not None else ""),
                ruc_masked=clean_ruc[:2] + ("*" * max(len(clean_ruc) - 5, 0)) + clean_ruc[-3:] if len(clean_ruc) > 5 else "*" * len(clean_ruc),
            )
            if credential is not None
            else None,
            "sunat_username_encrypted": credential.sunat_username_encrypted if credential is not None else None,
        }


async def create_workspace(tenant_id: str, owner_user_id: str, payload: dict) -> dict | None:
    async with async_session() as session:
        async with session.begin():
            company = await session.get(Company, payload["empresa_id"])
            plan = await session.get(BusinessPlan, payload["plan_id"])
            if company is None or company.tenant_id != tenant_id or plan is None or plan.estado != "active":
                return None
            workspace = Workspace(
                id=f"workspace-{uuid.uuid4().hex}",
                tenant_id=tenant_id,
                nombre=payload["nombre"],
                propietario=owner_user_id,
                empresa_id=payload["empresa_id"],
                estado=payload["estado"],
                plan_id=payload["plan_id"],
            )
            membership = WorkspaceMembership(
                user_id=owner_user_id,
                workspace_id=workspace.id,
                tenant_id=tenant_id,
                role_id="ADMIN",
                estado="active",
            )
            session.add_all([workspace, membership])
            await session.flush()
            await session.refresh(workspace)
            return _workspace_dict(workspace)


async def list_workspaces_for_user(tenant_id: str, user_id: str) -> list[dict]:
    async with async_session() as session:
        memberships = (
            await session.execute(
                select(WorkspaceMembership).where(
                    WorkspaceMembership.tenant_id == tenant_id,
                    WorkspaceMembership.user_id == user_id,
                    WorkspaceMembership.estado == "active",
                )
            )
        ).scalars().all()
        workspace_ids = [membership.workspace_id for membership in memberships]
        if not workspace_ids:
            return []
        result = await session.execute(
            select(Workspace)
            .where(Workspace.tenant_id == tenant_id, Workspace.id.in_(workspace_ids), Workspace.estado == "active")
            .order_by(Workspace.created_at.desc(), Workspace.id.desc())
        )
        rows = result.scalars().all()
    return [_workspace_dict(row) for row in rows]


async def get_workspace_for_user(tenant_id: str, user_id: str, workspace_id: str) -> dict | None:
    async with async_session() as session:
        membership = await session.get(WorkspaceMembership, (user_id, workspace_id))
        workspace = await session.get(Workspace, workspace_id)
        if (
            membership is None
            or workspace is None
            or membership.tenant_id != tenant_id
            or workspace.tenant_id != tenant_id
            or membership.estado != "active"
            or workspace.estado != "active"
        ):
            return None
        return _workspace_dict(workspace)


async def workspace_role_for_user(tenant_id: str, user_id: str, workspace_id: str) -> str | None:
    async with async_session() as session:
        row = await session.get(WorkspaceMembership, (user_id, workspace_id))
        if row is None or row.tenant_id != tenant_id or row.estado != "active":
            return None
        return row.role_id


async def assign_workspace_membership(tenant_id: str, workspace_id: str, user_id: str, role_id: str) -> dict | None:
    async with async_session() as session:
        async with session.begin():
            workspace = await session.get(Workspace, workspace_id)
            user = await session.get(User, user_id)
            role = await session.get(BusinessRole, role_id)
            if (
                workspace is None
                or user is None
                or role is None
                or workspace.tenant_id != tenant_id
                or user.tenant_id != tenant_id
                or role.estado != "active"
                or not user.active
            ):
                return None
            membership = await session.get(WorkspaceMembership, (user_id, workspace_id))
            if membership is None:
                membership = WorkspaceMembership(
                    user_id=user_id,
                    workspace_id=workspace_id,
                    tenant_id=tenant_id,
                    role_id=role_id,
                    estado="active",
                )
                session.add(membership)
            else:
                membership.role_id = role_id
                membership.estado = "active"
            await session.flush()
            await session.refresh(membership)
            return _membership_dict(membership)


async def get_active_context(tenant_id: str, user_id: str) -> dict:
    async with async_session() as session:
        row = await session.get(ActiveOperationalContext, user_id)
        if row is None or row.tenant_id != tenant_id:
            return _context_dict(None, user_id, tenant_id)
        return _context_dict(row, user_id, tenant_id)


async def set_active_company(tenant_id: str, user_id: str, company_id: str) -> dict | None:
    async with async_session() as session:
        async with session.begin():
            company = await session.get(Company, company_id)
            if company is None or company.tenant_id != tenant_id or company.estado != "active":
                return None
            context = await session.get(ActiveOperationalContext, user_id)
            if context is None:
                context = ActiveOperationalContext(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    active_company_id=company_id,
                    active_workspace_id=None,
                    active_user_id=user_id,
                )
                session.add(context)
            else:
                context.active_company_id = company_id
                context.active_user_id = user_id
            await session.flush()
            await session.refresh(context)
            return _context_dict(context, user_id, tenant_id)


async def set_active_workspace(tenant_id: str, user_id: str, workspace_id: str) -> dict | None:
    async with async_session() as session:
        async with session.begin():
            membership = await session.get(WorkspaceMembership, (user_id, workspace_id))
            workspace = await session.get(Workspace, workspace_id)
            if (
                membership is None
                or workspace is None
                or membership.tenant_id != tenant_id
                or workspace.tenant_id != tenant_id
                or membership.estado != "active"
                or workspace.estado != "active"
            ):
                return None
            context = await session.get(ActiveOperationalContext, user_id)
            if context is None:
                context = ActiveOperationalContext(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    active_company_id=workspace.empresa_id,
                    active_workspace_id=workspace_id,
                    active_user_id=user_id,
                )
                session.add(context)
            else:
                context.active_company_id = workspace.empresa_id
                context.active_workspace_id = workspace_id
                context.active_user_id = user_id
            await session.flush()
            await session.refresh(context)
            return _context_dict(context, user_id, tenant_id)


def _sunat_connection_dict(row: SunatConnection) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "empresa_id": row.empresa_id,
        "workspace_id": row.workspace_id,
        "estado": row.estado,
        "connection_type": row.connection_type,
        "auxiliary_user_alias": row.auxiliary_user_alias,
        "created_by": row.created_by,
        "updated_by": row.updated_by,
        "last_error": row.last_error,
        "created_at": _created_at(row.created_at),
        "updated_at": _created_at(row.updated_at),
        "last_sync_at": _created_at(row.last_sync_at) if row.last_sync_at is not None else None,
        "real_sunat_session": False,
        "read_only": True,
        "remote_actions_enabled": False,
    }


def _sunat_event_dict(row: SunatConnectionEvent) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "connection_id": row.connection_id,
        "empresa_id": row.empresa_id,
        "workspace_id": row.workspace_id,
        "actor_user_id": row.actor_user_id,
        "event_type": row.event_type,
        "status": row.status,
        "metadata": row.metadata_json or {},
        "created_at": _created_at(row.created_at),
    }


def _sunat_credential_dict(row: SunatCredential, *, username_masked: str | None = None, ruc_masked: str | None = None) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "empresa_id": row.empresa_id,
        "workspace_id": row.workspace_id,
        "ruc": row.ruc,
        "ruc_masked": ruc_masked or row.ruc,
        "sunat_username_masked": username_masked or "",
        "status": row.status,
        "read_only": True,
        "remote_actions_enabled": False,
        "real_sunat_session": False,
        "real_connector_enabled": False,
        "created_by": row.created_by,
        "updated_by": row.updated_by,
        "last_error": row.last_error,
        "created_at": _created_at(row.created_at),
        "updated_at": _created_at(row.updated_at),
        "last_validated_at": _created_at(row.last_validated_at) if row.last_validated_at is not None else None,
        "disconnected_at": _created_at(row.disconnected_at) if row.disconnected_at is not None else None,
    }


def _sunat_api_credential_dict(row: SunatApiCredential) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "empresa_id": row.empresa_id,
        "workspace_id": row.workspace_id,
        "ruc": row.ruc,
        "ruc_masked": row.ruc[:2] + ("*" * max(len(row.ruc) - 4, 0)) + row.ruc[-2:] if len(row.ruc) > 4 else "*" * len(row.ruc),
        "client_id_masked": row.client_id_masked,
        "status": row.status,
        "read_only": True,
        "sensitive_actions_enabled": False,
        "services": row.services_json or {},
        "token_configured": bool(row.token_hash),
        "token_expires_at": _created_at(row.token_expires_at) if row.token_expires_at is not None else None,
        "last_test_status": row.last_test_status,
        "last_error": row.last_error,
        "configured_by": row.configured_by,
        "updated_by": row.updated_by,
        "created_at": _created_at(row.created_at),
        "updated_at": _created_at(row.updated_at),
        "last_validated_at": _created_at(row.last_validated_at) if row.last_validated_at is not None else None,
    }


async def create_or_update_sunat_connection(tenant_id: str, user_id: str, payload: dict) -> dict:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(SunatConnection)
                .where(
                    SunatConnection.tenant_id == tenant_id,
                    SunatConnection.empresa_id == payload["empresa_id"],
                    SunatConnection.workspace_id == payload["workspace_id"],
                    SunatConnection.estado != "DISABLED",
                )
                .order_by(SunatConnection.created_at.desc(), SunatConnection.id.desc())
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row is None:
                row = SunatConnection(
                    id=f"sunat-connection-{uuid.uuid4().hex}",
                    tenant_id=tenant_id,
                    empresa_id=payload["empresa_id"],
                    workspace_id=payload["workspace_id"],
                    estado="CONNECTING",
                    connection_type=payload["connection_type"],
                    auxiliary_user_alias=payload.get("auxiliary_user_alias") or "",
                    credential_reference=payload.get("credential_reference"),
                    created_by=user_id,
                    updated_by=user_id,
                    last_error="real_sunat_connector_not_configured",
                )
                session.add(row)
            else:
                row.estado = "CONNECTING"
                row.connection_type = payload["connection_type"]
                row.auxiliary_user_alias = payload.get("auxiliary_user_alias") or ""
                row.credential_reference = payload.get("credential_reference")
                row.updated_by = user_id
                row.last_error = "real_sunat_connector_not_configured"
            await session.flush()
            await session.refresh(row)
            return _sunat_connection_dict(row)


async def prepare_sunat_auxiliary_connection(tenant_id: str, user_id: str, payload: dict) -> dict:
    await ensure_onboarding_progress_storage()
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(SunatConnection)
                .where(
                    SunatConnection.tenant_id == tenant_id,
                    SunatConnection.empresa_id == payload["empresa_id"],
                    SunatConnection.workspace_id == payload["workspace_id"],
                    SunatConnection.estado != "DISABLED",
                )
                .order_by(SunatConnection.created_at.desc(), SunatConnection.id.desc())
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row is None:
                row = SunatConnection(
                    id=f"sunat-connection-{uuid.uuid4().hex}",
                    tenant_id=tenant_id,
                    empresa_id=payload["empresa_id"],
                    workspace_id=payload["workspace_id"],
                    estado="NOT_CONNECTED",
                    connection_type="CLAVE_SOL_AUXILIAR",
                    auxiliary_user_alias=payload.get("auxiliary_user_alias") or "",
                    credential_reference=None,
                    created_by=user_id,
                    updated_by=user_id,
                    last_error="pending_sol_access_validation",
                )
                session.add(row)
            else:
                row.estado = "NOT_CONNECTED"
                row.connection_type = "CLAVE_SOL_AUXILIAR"
                row.auxiliary_user_alias = payload.get("auxiliary_user_alias") or ""
                row.credential_reference = None
                row.updated_by = user_id
                row.last_error = "pending_sol_access_validation"
            progress = await _ensure_progress_row(session, tenant_id, user_id)
            progress.sunat_auxiliary_prepared = bool(row.auxiliary_user_alias)
            await session.flush()
            await session.refresh(row)
            return _sunat_connection_dict(row)


async def upsert_sunat_credential(
    tenant_id: str,
    user_id: str,
    payload: dict,
    *,
    username_encrypted: str,
    password_encrypted: str,
    username_masked: str,
    ruc_masked: str,
) -> dict:
    await ensure_sunat_credential_storage()
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(SunatCredential)
                .where(
                    SunatCredential.tenant_id == tenant_id,
                    SunatCredential.empresa_id == payload["empresa_id"],
                    SunatCredential.workspace_id == payload["workspace_id"],
                )
                .order_by(SunatCredential.created_at.desc(), SunatCredential.id.desc())
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row is None:
                row = SunatCredential(
                    id=f"sunat-credential-{uuid.uuid4().hex}",
                    tenant_id=tenant_id,
                    empresa_id=payload["empresa_id"],
                    workspace_id=payload["workspace_id"],
                    ruc=payload["ruc"],
                    sunat_username_encrypted=username_encrypted,
                    sunat_password_encrypted=password_encrypted,
                    status="CREDENTIAL_RECEIVED",
                    read_only=True,
                    remote_actions_enabled=False,
                    created_by=user_id,
                    updated_by=user_id,
                    last_error="pending_read_only_connector_validation",
                )
                session.add(row)
            else:
                row.ruc = payload["ruc"]
                row.sunat_username_encrypted = username_encrypted
                row.sunat_password_encrypted = password_encrypted
                row.status = "CREDENTIAL_RECEIVED"
                row.read_only = True
                row.remote_actions_enabled = False
                row.updated_by = user_id
                row.last_error = "pending_read_only_connector_validation"
                row.disconnected_at = None
            await session.flush()
            await session.refresh(row)

            connection_result = await session.execute(
                select(SunatConnection)
                .where(
                    SunatConnection.tenant_id == tenant_id,
                    SunatConnection.empresa_id == payload["empresa_id"],
                    SunatConnection.workspace_id == payload["workspace_id"],
                    SunatConnection.estado != "DISABLED",
                )
                .order_by(SunatConnection.created_at.desc(), SunatConnection.id.desc())
                .limit(1)
            )
            connection = connection_result.scalar_one_or_none()
            if connection is None:
                connection = SunatConnection(
                    id=f"sunat-connection-{uuid.uuid4().hex}",
                    tenant_id=tenant_id,
                    empresa_id=payload["empresa_id"],
                    workspace_id=payload["workspace_id"],
                    estado="CONNECTING",
                    connection_type="CLAVE_SOL_AUXILIAR",
                    auxiliary_user_alias=username_masked,
                    credential_reference=f"vault:{row.id}",
                    created_by=user_id,
                    updated_by=user_id,
                    last_error="pending_read_only_connector_validation",
                )
                session.add(connection)
            else:
                connection.estado = "CONNECTING"
                connection.connection_type = "CLAVE_SOL_AUXILIAR"
                connection.auxiliary_user_alias = username_masked
                connection.credential_reference = f"vault:{row.id}"
                connection.updated_by = user_id
                connection.last_error = "pending_read_only_connector_validation"

            progress = await _ensure_progress_row(session, tenant_id, user_id)
            progress.sunat_auxiliary_prepared = True
            progress.updated_at = now

            await session.flush()
            await session.refresh(row)
            await session.refresh(connection)
            return {
                "credential": _sunat_credential_dict(row, username_masked=username_masked, ruc_masked=ruc_masked),
                "connection": _sunat_connection_dict(connection),
            }


async def get_sunat_credential_for_user(
    tenant_id: str,
    user_id: str,
    workspace_id: str,
    empresa_id: str,
    *,
    username_masked: str = "",
    ruc_masked: str = "",
) -> dict | None:
    await ensure_sunat_credential_storage()
    async with async_session() as session:
        membership = await session.get(WorkspaceMembership, (user_id, workspace_id))
        if membership is None or membership.tenant_id != tenant_id or membership.estado != "active":
            return None
        result = await session.execute(
            select(SunatCredential)
            .where(
                SunatCredential.tenant_id == tenant_id,
                SunatCredential.workspace_id == workspace_id,
                SunatCredential.empresa_id == empresa_id,
            )
            .order_by(SunatCredential.created_at.desc(), SunatCredential.id.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        if not username_masked:
            connection_result = await session.execute(
                select(SunatConnection.auxiliary_user_alias)
                .where(
                    SunatConnection.tenant_id == tenant_id,
                    SunatConnection.workspace_id == workspace_id,
                    SunatConnection.empresa_id == empresa_id,
                    SunatConnection.credential_reference == f"vault:{row.id}",
                )
                .order_by(SunatConnection.created_at.desc(), SunatConnection.id.desc())
                .limit(1)
            )
            username_masked = connection_result.scalar_one_or_none() or ""
        return _sunat_credential_dict(row, username_masked=username_masked, ruc_masked=ruc_masked)


async def disconnect_sunat_credential(tenant_id: str, user_id: str, workspace_id: str, empresa_id: str, reason: str) -> dict | None:
    await ensure_sunat_credential_storage()
    disconnected_at = datetime.now(timezone.utc)
    async with async_session() as session:
        async with session.begin():
            membership = await session.get(WorkspaceMembership, (user_id, workspace_id))
            if membership is None or membership.tenant_id != tenant_id or membership.estado != "active":
                return None
            result = await session.execute(
                select(SunatCredential)
                .where(
                    SunatCredential.tenant_id == tenant_id,
                    SunatCredential.workspace_id == workspace_id,
                    SunatCredential.empresa_id == empresa_id,
                )
                .order_by(SunatCredential.created_at.desc(), SunatCredential.id.desc())
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            row.sunat_username_encrypted = None
            row.sunat_password_encrypted = None
            row.status = "DISCONNECTED"
            row.read_only = True
            row.remote_actions_enabled = False
            row.updated_by = user_id
            row.last_error = reason
            row.disconnected_at = disconnected_at
            await session.flush()
            await session.refresh(row)
            return _sunat_credential_dict(row)


async def upsert_sunat_api_credential(
    tenant_id: str,
    user_id: str,
    payload: dict,
    *,
    client_id_encrypted: str,
    client_secret_encrypted: str,
    client_id_masked: str,
) -> dict:
    await ensure_sunat_api_storage()
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(SunatApiCredential)
                .where(
                    SunatApiCredential.tenant_id == tenant_id,
                    SunatApiCredential.empresa_id == payload["empresa_id"],
                    SunatApiCredential.workspace_id == payload["workspace_id"],
                )
                .order_by(SunatApiCredential.created_at.desc(), SunatApiCredential.id.desc())
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row is None:
                row = SunatApiCredential(
                    id=f"sunat-api-credential-{uuid.uuid4().hex}",
                    tenant_id=tenant_id,
                    empresa_id=payload["empresa_id"],
                    workspace_id=payload["workspace_id"],
                    ruc=payload["ruc"],
                    client_id_encrypted=client_id_encrypted,
                    client_secret_encrypted=client_secret_encrypted,
                    client_id_masked=client_id_masked,
                    status="CONFIGURED",
                    read_only=True,
                    sensitive_actions_enabled=False,
                    services_json={
                        "cpe": {"status": "pending_test"},
                        "sire_sales": {"status": "pending_test"},
                        "sire_purchases": {"status": "pending_test"},
                    },
                    configured_by=user_id,
                    updated_by=user_id,
                    last_test_status="pending",
                    last_error=None,
                )
                session.add(row)
            else:
                row.ruc = payload["ruc"]
                row.client_id_encrypted = client_id_encrypted
                row.client_secret_encrypted = client_secret_encrypted
                row.client_id_masked = client_id_masked
                row.status = "CONFIGURED"
                row.read_only = True
                row.sensitive_actions_enabled = False
                row.services_json = {
                    "cpe": {"status": "pending_test"},
                    "sire_sales": {"status": "pending_test"},
                    "sire_purchases": {"status": "pending_test"},
                }
                row.updated_by = user_id
                row.last_test_status = "pending"
                row.last_error = None
                row.updated_at = now
            await session.flush()
            await session.refresh(row)
            return _sunat_api_credential_dict(row)


async def get_sunat_api_credential_for_user(
    tenant_id: str,
    user_id: str,
    workspace_id: str,
    empresa_id: str,
) -> dict | None:
    await ensure_sunat_api_storage()
    async with async_session() as session:
        membership = await session.get(WorkspaceMembership, (user_id, workspace_id))
        if membership is None or membership.tenant_id != tenant_id or membership.estado != "active":
            return None
        result = await session.execute(
            select(SunatApiCredential)
            .where(
                SunatApiCredential.tenant_id == tenant_id,
                SunatApiCredential.workspace_id == workspace_id,
                SunatApiCredential.empresa_id == empresa_id,
            )
            .order_by(SunatApiCredential.created_at.desc(), SunatApiCredential.id.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return _sunat_api_credential_dict(row) if row is not None else None


async def get_sunat_api_credential_secret_for_user(
    tenant_id: str,
    user_id: str,
    workspace_id: str,
    empresa_id: str,
) -> dict | None:
    await ensure_sunat_api_storage()
    async with async_session() as session:
        membership = await session.get(WorkspaceMembership, (user_id, workspace_id))
        if membership is None or membership.tenant_id != tenant_id or membership.estado != "active":
            return None
        result = await session.execute(
            select(SunatApiCredential)
            .where(
                SunatApiCredential.tenant_id == tenant_id,
                SunatApiCredential.workspace_id == workspace_id,
                SunatApiCredential.empresa_id == empresa_id,
            )
            .order_by(SunatApiCredential.created_at.desc(), SunatApiCredential.id.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "empresa_id": row.empresa_id,
            "workspace_id": row.workspace_id,
            "ruc": row.ruc,
            "client_id_encrypted": row.client_id_encrypted,
            "client_secret_encrypted": row.client_secret_encrypted,
            "client_id_masked": row.client_id_masked,
            "services": row.services_json or {},
        }


async def update_sunat_api_credential_status(
    tenant_id: str,
    credential_id: str,
    *,
    status: str,
    services: dict | None = None,
    token_hash: str | None = None,
    token_expires_at: datetime | None = None,
    last_test_status: str | None = None,
    last_error: str | None = None,
    validated: bool = False,
) -> dict | None:
    await ensure_sunat_api_storage()
    async with async_session() as session:
        async with session.begin():
            row = await session.get(SunatApiCredential, credential_id, with_for_update=True)
            if row is None or row.tenant_id != tenant_id:
                return None
            row.status = status
            if services is not None:
                row.services_json = services
            row.token_hash = token_hash
            row.token_expires_at = token_expires_at
            row.last_test_status = last_test_status or status
            row.last_error = last_error
            if validated:
                row.last_validated_at = datetime.now(timezone.utc)
            await session.flush()
            await session.refresh(row)
            return _sunat_api_credential_dict(row)


async def record_sunat_consent(tenant_id: str, user_id: str, connection: dict, scope: dict) -> dict:
    accepted_at = datetime.now(timezone.utc)
    row = SunatConsent(
        id=f"sunat-consent-{uuid.uuid4().hex}",
        tenant_id=tenant_id,
        empresa_id=connection["empresa_id"],
        workspace_id=connection["workspace_id"],
        connection_id=connection["id"],
        user_id=user_id,
        accepted=True,
        consent_version="SUNAT_SOL_V1",
        scope=scope,
        accepted_at=accepted_at,
    )
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "empresa_id": row.empresa_id,
        "workspace_id": row.workspace_id,
        "connection_id": row.connection_id,
        "user_id": row.user_id,
        "accepted": row.accepted,
        "consent_version": row.consent_version,
        "scope": row.scope or {},
        "accepted_at": accepted_at.isoformat(),
    }


async def record_sunat_connection_event(
    tenant_id: str,
    user_id: str,
    connection: dict,
    event_type: str,
    status: str,
    metadata: dict,
) -> dict:
    row = SunatConnectionEvent(
        id=f"sunat-event-{uuid.uuid4().hex}",
        tenant_id=tenant_id,
        connection_id=connection["id"],
        empresa_id=connection["empresa_id"],
        workspace_id=connection["workspace_id"],
        actor_user_id=user_id,
        event_type=event_type,
        status=status,
        metadata_json=metadata,
    )
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return _sunat_event_dict(row)


def _sunat_permission_check_dict(row: SunatPermissionCheck) -> dict:
    return {
        "id": row.id,
        "company_id": row.company_id,
        "tenant_id": row.tenant_id,
        "workspace_id": row.workspace_id,
        "ruc": row.ruc,
        "run_id": row.run_id,
        "permission_name": row.permission_name,
        "permission_path": row.permission_path,
        "permission_type": row.permission_type,
        "is_available": row.is_available,
        "is_recommended": row.is_recommended,
        "is_sensitive": row.is_sensitive,
        "can_read": row.can_read,
        "can_execute": row.can_execute,
        "status": row.status,
        "source": row.source,
        "metadata": row.metadata_json or {},
        "detected_at": _created_at(row.detected_at),
    }


def _sunat_raw_snapshot_dict(row: SunatRawSnapshot) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "company_id": row.company_id,
        "workspace_id": row.workspace_id,
        "ruc": row.ruc,
        "run_id": row.run_id,
        "source": row.source,
        "snapshot_type": row.snapshot_type,
        "content_hash": row.content_hash,
        "content": row.content_json or {},
        "metadata": row.metadata_json or {},
        "captured_at": _created_at(row.captured_at),
    }


def _sunat_normalized_fact_dict(row: SunatNormalizedFact) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "company_id": row.company_id,
        "workspace_id": row.workspace_id,
        "ruc": row.ruc,
        "run_id": row.run_id,
        "fact_type": row.fact_type,
        "fact_key": row.fact_key,
        "fact_value": row.fact_value or {},
        "source_snapshot_id": row.source_snapshot_id,
        "confidence": row.confidence,
        "status": row.status,
        "detected_at": _created_at(row.detected_at),
    }


def _sunat_diagnostic_run_dict(row: SunatDiagnosticRun) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "company_id": row.company_id,
        "workspace_id": row.workspace_id,
        "ruc": row.ruc,
        "status": row.status,
        "connector_status": row.connector_status,
        "real_sunat_session": row.real_sunat_session,
        "read_only": row.read_only,
        "remote_actions_enabled": row.remote_actions_enabled,
        "summary": row.summary_json or {},
        "metadata": row.metadata_json or {},
        "started_at": _created_at(row.started_at),
        "completed_at": _created_at(row.completed_at) if row.completed_at else None,
    }


def _sunat_finding_dict(row: SunatFinding) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "company_id": row.company_id,
        "workspace_id": row.workspace_id,
        "ruc": row.ruc,
        "run_id": row.run_id,
        "severity": row.severity,
        "category": row.category,
        "title": row.title,
        "message": row.message,
        "source": row.source,
        "status": row.status,
        "metadata": row.metadata_json or {},
        "detected_at": _created_at(row.detected_at),
    }


async def get_sunat_credential_secret_for_user(
    tenant_id: str,
    user_id: str,
    workspace_id: str,
    empresa_id: str,
) -> dict | None:
    await ensure_sunat_credential_storage()
    async with async_session() as session:
        membership = await session.get(WorkspaceMembership, (user_id, workspace_id))
        if membership is None or membership.tenant_id != tenant_id or membership.estado != "active":
            return None
        result = await session.execute(
            select(SunatCredential)
            .where(
                SunatCredential.tenant_id == tenant_id,
                SunatCredential.workspace_id == workspace_id,
                SunatCredential.empresa_id == empresa_id,
            )
            .order_by(SunatCredential.created_at.desc(), SunatCredential.id.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "empresa_id": row.empresa_id,
            "workspace_id": row.workspace_id,
            "ruc": row.ruc,
            "sunat_username_encrypted": row.sunat_username_encrypted,
            "sunat_password_encrypted": row.sunat_password_encrypted,
            "status": row.status,
            "read_only": row.read_only,
            "remote_actions_enabled": row.remote_actions_enabled,
            "disconnected_at": _created_at(row.disconnected_at) if row.disconnected_at else None,
        }


async def update_sunat_readonly_status(
    tenant_id: str,
    user_id: str,
    workspace_id: str,
    empresa_id: str,
    *,
    credential_status: str,
    connection_status: str,
    last_error: str | None,
    validated: bool,
) -> None:
    await ensure_sunat_credential_storage()
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        async with session.begin():
            credential_result = await session.execute(
                select(SunatCredential)
                .where(
                    SunatCredential.tenant_id == tenant_id,
                    SunatCredential.workspace_id == workspace_id,
                    SunatCredential.empresa_id == empresa_id,
                )
                .order_by(SunatCredential.created_at.desc(), SunatCredential.id.desc())
                .limit(1)
            )
            credential = credential_result.scalar_one_or_none()
            if credential is not None:
                credential.status = credential_status
                credential.updated_by = user_id
                credential.last_error = last_error
                if validated:
                    credential.last_validated_at = now
            connection_result = await session.execute(
                select(SunatConnection)
                .where(
                    SunatConnection.tenant_id == tenant_id,
                    SunatConnection.workspace_id == workspace_id,
                    SunatConnection.empresa_id == empresa_id,
                    SunatConnection.estado != "DISABLED",
                )
                .order_by(SunatConnection.created_at.desc(), SunatConnection.id.desc())
                .limit(1)
            )
            connection = connection_result.scalar_one_or_none()
            if connection is not None:
                connection.estado = connection_status
                connection.updated_by = user_id
                connection.last_error = last_error
                if validated:
                    connection.last_sync_at = now


async def start_sunat_diagnostic_run(tenant_id: str, user_id: str, company: dict, workspace: dict, ruc: str) -> dict:
    await ensure_sunat_readonly_storage()
    row = SunatDiagnosticRun(
        id=f"sunat-run-{uuid.uuid4().hex}",
        tenant_id=tenant_id,
        company_id=company["id"],
        workspace_id=workspace["id"],
        ruc=ruc,
        status="running",
        connector_status="starting",
        real_sunat_session=False,
        read_only=True,
        remote_actions_enabled=False,
        summary_json={},
        metadata_json={"started_by": user_id, "storage_backend": settings.sunat_storage_backend},
    )
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return _sunat_diagnostic_run_dict(row)


async def complete_sunat_diagnostic_run(
    run_id: str,
    tenant_id: str,
    *,
    status: str,
    connector_status: str,
    real_sunat_session: bool,
    summary: dict,
    metadata: dict,
) -> dict | None:
    await ensure_sunat_readonly_storage()
    completed_at = datetime.now(timezone.utc)
    async with async_session() as session:
        async with session.begin():
            row = await session.get(SunatDiagnosticRun, run_id, with_for_update=True)
            if row is None or row.tenant_id != tenant_id:
                return None
            row.status = status
            row.connector_status = connector_status
            row.real_sunat_session = real_sunat_session
            row.read_only = True
            row.remote_actions_enabled = False
            row.summary_json = summary
            row.metadata_json = metadata
            row.completed_at = completed_at
            return _sunat_diagnostic_run_dict(row)
    return None


async def record_sunat_permission_checks(
    tenant_id: str,
    company_id: str,
    workspace_id: str,
    ruc: str,
    run_id: str,
    checks: list[dict],
) -> list[dict]:
    await ensure_sunat_readonly_storage()
    rows = [
        SunatPermissionCheck(
            id=f"sunat-permission-{uuid.uuid4().hex}",
            company_id=company_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            ruc=ruc,
            run_id=run_id,
            permission_name=check["permission_name"],
            permission_path=check.get("permission_path") or "",
            permission_type=check.get("permission_type") or "unknown",
            is_available=bool(check.get("is_available")),
            is_recommended=bool(check.get("is_recommended")),
            is_sensitive=bool(check.get("is_sensitive")),
            can_read=bool(check.get("can_read")),
            can_execute=bool(check.get("can_execute")),
            status=check.get("status") or "not_checked",
            source=check.get("source") or "sunat_readonly",
            metadata_json=check.get("metadata") or {},
        )
        for check in checks
    ]
    async with async_session() as session:
        async with session.begin():
            session.add_all(rows)
    return [_sunat_permission_check_dict(row) for row in rows]


async def record_sunat_raw_snapshot(
    tenant_id: str,
    company_id: str,
    workspace_id: str,
    ruc: str,
    run_id: str,
    *,
    source: str,
    snapshot_type: str,
    content: dict,
    metadata: dict,
) -> dict:
    await ensure_sunat_readonly_storage()
    encoded = repr(content).encode("utf-8", errors="replace")
    row = SunatRawSnapshot(
        id=f"sunat-snapshot-{uuid.uuid4().hex}",
        tenant_id=tenant_id,
        company_id=company_id,
        workspace_id=workspace_id,
        ruc=ruc,
        run_id=run_id,
        source=source,
        snapshot_type=snapshot_type,
        content_hash=hashlib.sha256(encoded).hexdigest(),
        content_json=content,
        metadata_json=metadata,
    )
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return _sunat_raw_snapshot_dict(row)


async def record_sunat_normalized_facts(
    tenant_id: str,
    company_id: str,
    workspace_id: str,
    ruc: str,
    run_id: str,
    facts: list[dict],
) -> list[dict]:
    await ensure_sunat_readonly_storage()
    rows = [
        SunatNormalizedFact(
            id=f"sunat-fact-{uuid.uuid4().hex}",
            tenant_id=tenant_id,
            company_id=company_id,
            workspace_id=workspace_id,
            ruc=ruc,
            run_id=run_id,
            fact_type=fact.get("fact_type") or "unknown",
            fact_key=fact.get("fact_key") or "unknown",
            fact_value=fact.get("fact_value") or {},
            source_snapshot_id=fact.get("source_snapshot_id"),
            confidence=int(fact.get("confidence") or 0),
            status=fact.get("status") or "normalized",
        )
        for fact in facts
    ]
    async with async_session() as session:
        async with session.begin():
            session.add_all(rows)
    return [_sunat_normalized_fact_dict(row) for row in rows]


async def record_sunat_findings(
    tenant_id: str,
    company_id: str,
    workspace_id: str,
    ruc: str,
    run_id: str,
    findings: list[dict],
) -> list[dict]:
    await ensure_sunat_readonly_storage()
    rows = [
        SunatFinding(
            id=f"sunat-finding-{uuid.uuid4().hex}",
            tenant_id=tenant_id,
            company_id=company_id,
            workspace_id=workspace_id,
            ruc=ruc,
            run_id=run_id,
            severity=finding.get("severity") or "info",
            category=finding.get("category") or "general",
            title=finding.get("title") or "Hallazgo SUNAT",
            message=finding.get("message") or "",
            source=finding.get("source") or "sunat_readonly",
            status=finding.get("status") or "open",
            metadata_json=finding.get("metadata") or {},
        )
        for finding in findings
    ]
    async with async_session() as session:
        async with session.begin():
            session.add_all(rows)
    return [_sunat_finding_dict(row) for row in rows]


async def latest_sunat_diagnostic_run(tenant_id: str, workspace_id: str, empresa_id: str) -> dict | None:
    await ensure_sunat_readonly_storage()
    async with async_session() as session:
        result = await session.execute(
            select(SunatDiagnosticRun)
            .where(
                SunatDiagnosticRun.tenant_id == tenant_id,
                SunatDiagnosticRun.workspace_id == workspace_id,
                SunatDiagnosticRun.company_id == empresa_id,
            )
            .order_by(SunatDiagnosticRun.started_at.desc(), SunatDiagnosticRun.id.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return _sunat_diagnostic_run_dict(row) if row is not None else None


async def list_sunat_diagnostic_runs(tenant_id: str, workspace_id: str, empresa_id: str, limit: int = 20) -> list[dict]:
    await ensure_sunat_readonly_storage()
    limit, _ = clamp_page(limit, 0, 100)
    async with async_session() as session:
        result = await session.execute(
            select(SunatDiagnosticRun)
            .where(
                SunatDiagnosticRun.tenant_id == tenant_id,
                SunatDiagnosticRun.workspace_id == workspace_id,
                SunatDiagnosticRun.company_id == empresa_id,
            )
            .order_by(SunatDiagnosticRun.started_at.desc(), SunatDiagnosticRun.id.desc())
            .limit(limit)
        )
        return [_sunat_diagnostic_run_dict(row) for row in result.scalars().all()]


async def list_sunat_permission_checks(tenant_id: str, workspace_id: str, empresa_id: str, run_id: str | None = None) -> list[dict]:
    await ensure_sunat_readonly_storage()
    if run_id is None:
        latest = await latest_sunat_diagnostic_run(tenant_id, workspace_id, empresa_id)
        run_id = (latest or {}).get("id")
    if not run_id:
        return []
    async with async_session() as session:
        result = await session.execute(
            select(SunatPermissionCheck)
            .where(
                SunatPermissionCheck.tenant_id == tenant_id,
                SunatPermissionCheck.workspace_id == workspace_id,
                SunatPermissionCheck.company_id == empresa_id,
                SunatPermissionCheck.run_id == run_id,
            )
            .order_by(SunatPermissionCheck.is_recommended.desc(), SunatPermissionCheck.permission_name.asc())
        )
        return [_sunat_permission_check_dict(row) for row in result.scalars().all()]


async def list_sunat_raw_snapshots(tenant_id: str, workspace_id: str, empresa_id: str, run_id: str | None = None) -> list[dict]:
    await ensure_sunat_readonly_storage()
    if run_id is None:
        latest = await latest_sunat_diagnostic_run(tenant_id, workspace_id, empresa_id)
        run_id = (latest or {}).get("id")
    if not run_id:
        return []
    async with async_session() as session:
        result = await session.execute(
            select(SunatRawSnapshot)
            .where(
                SunatRawSnapshot.tenant_id == tenant_id,
                SunatRawSnapshot.workspace_id == workspace_id,
                SunatRawSnapshot.company_id == empresa_id,
                SunatRawSnapshot.run_id == run_id,
            )
            .order_by(SunatRawSnapshot.captured_at.asc(), SunatRawSnapshot.id.asc())
        )
        return [_sunat_raw_snapshot_dict(row) for row in result.scalars().all()]


async def list_sunat_normalized_facts(tenant_id: str, workspace_id: str, empresa_id: str, run_id: str | None = None) -> list[dict]:
    await ensure_sunat_readonly_storage()
    if run_id is None:
        latest = await latest_sunat_diagnostic_run(tenant_id, workspace_id, empresa_id)
        run_id = (latest or {}).get("id")
    if not run_id:
        return []
    async with async_session() as session:
        result = await session.execute(
            select(SunatNormalizedFact)
            .where(
                SunatNormalizedFact.tenant_id == tenant_id,
                SunatNormalizedFact.workspace_id == workspace_id,
                SunatNormalizedFact.company_id == empresa_id,
                SunatNormalizedFact.run_id == run_id,
            )
            .order_by(SunatNormalizedFact.fact_type.asc(), SunatNormalizedFact.fact_key.asc())
        )
        return [_sunat_normalized_fact_dict(row) for row in result.scalars().all()]


SUNAT_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


async def list_sunat_findings(tenant_id: str, workspace_id: str, empresa_id: str, run_id: str | None = None) -> list[dict]:
    await ensure_sunat_readonly_storage()
    if run_id is None:
        latest = await latest_sunat_diagnostic_run(tenant_id, workspace_id, empresa_id)
        run_id = (latest or {}).get("id")
    if not run_id:
        return []
    async with async_session() as session:
        result = await session.execute(
            select(SunatFinding)
            .where(
                SunatFinding.tenant_id == tenant_id,
                SunatFinding.workspace_id == workspace_id,
                SunatFinding.company_id == empresa_id,
                SunatFinding.run_id == run_id,
            )
            .order_by(SunatFinding.detected_at.asc(), SunatFinding.id.asc())
        )
        findings = [_sunat_finding_dict(row) for row in result.scalars().all()]
    return sorted(findings, key=lambda item: (SUNAT_SEVERITY_ORDER.get(str(item.get("severity")), 9), item.get("detected_at") or ""))


async def list_sunat_connections(
    tenant_id: str,
    user_id: str,
    workspace_id: str | None = None,
    empresa_id: str | None = None,
) -> list[dict]:
    async with async_session() as session:
        membership_result = await session.execute(
            select(WorkspaceMembership.workspace_id).where(
                WorkspaceMembership.tenant_id == tenant_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.estado == "active",
            )
        )
        allowed_workspace_ids = list(membership_result.scalars().all())
        if not allowed_workspace_ids:
            return []
        statement = select(SunatConnection).where(
            SunatConnection.tenant_id == tenant_id,
            SunatConnection.workspace_id.in_(allowed_workspace_ids),
        )
        if workspace_id:
            statement = statement.where(SunatConnection.workspace_id == workspace_id)
        if empresa_id:
            statement = statement.where(SunatConnection.empresa_id == empresa_id)
        result = await session.execute(statement.order_by(SunatConnection.created_at.desc(), SunatConnection.id.desc()))
        rows = result.scalars().all()
    return [_sunat_connection_dict(row) for row in rows]


async def get_sunat_connection_for_user(tenant_id: str, user_id: str, connection_id: str) -> dict | None:
    async with async_session() as session:
        row = await session.get(SunatConnection, connection_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        membership = await session.get(WorkspaceMembership, (user_id, row.workspace_id))
        if membership is None or membership.tenant_id != tenant_id or membership.estado != "active":
            return None
        return _sunat_connection_dict(row)


async def disconnect_sunat_connection(tenant_id: str, user_id: str, connection_id: str, reason: str) -> dict | None:
    async with async_session() as session:
        async with session.begin():
            row = await session.get(SunatConnection, connection_id, with_for_update=True)
            if row is None or row.tenant_id != tenant_id:
                return None
            membership = await session.get(WorkspaceMembership, (user_id, row.workspace_id))
            if membership is None or membership.tenant_id != tenant_id or membership.estado != "active":
                return None
            row.estado = "DISABLED"
            row.updated_by = user_id
            row.last_error = reason
            await session.flush()
            await session.refresh(row)
            return _sunat_connection_dict(row)


async def list_audit_events(tenant_id: str, limit: int = 100) -> list[dict]:
    limit, _ = clamp_page(limit, 0)
    async with async_session() as session:
        result = await session.execute(
            select(AuditEvent)
            .where(AuditEvent.tenant_id == tenant_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
    return [
        {
            "id": row.id,
            "timestamp": _created_at(row.created_at),
            "request_id": row.request_id,
            "tenant_id": row.tenant_id,
            "event_type": row.event_type,
            "actor": row.actor,
            "risk": row.risk,
            "payload": row.payload or {},
            "previous_hash": row.previous_hash,
            "event_hash": row.event_hash,
        }
        for row in reversed(rows)
    ]


async def record_runtime_event(event_type: str, status: str, payload: dict, tenant_id: str = "public") -> None:
    row = RuntimeEvent(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        status=status,
        event_type=event_type,
        payload=payload,
    )
    async with async_session() as session:
        async with session.begin():
            session.add(row)


async def product_analytics_summary(tenant_id: str) -> dict:
    async with async_session() as session:
        result = await session.execute(
            select(RuntimeEvent.event_type, RuntimeEvent.status, func.count(RuntimeEvent.id))
            .where(RuntimeEvent.tenant_id == tenant_id)
            .group_by(RuntimeEvent.event_type, RuntimeEvent.status)
            .order_by(RuntimeEvent.event_type)
        )
        by_event: dict[str, dict[str, int]] = {}
        for event_type, status, count in result.all():
            by_event.setdefault(event_type, {})[status] = int(count)
        total = await session.scalar(select(func.count(RuntimeEvent.id)).where(RuntimeEvent.tenant_id == tenant_id))
        failures = await session.scalar(
            select(func.count(RuntimeEvent.id)).where(RuntimeEvent.tenant_id == tenant_id, RuntimeEvent.status == "error")
        )
    return {
        "tenant_id": tenant_id,
        "events_total": int(total or 0),
        "failures_total": int(failures or 0),
        "by_event": by_event,
        "activation": {
            "onboarding_completed": bool(by_event.get("product.onboarding_completed")),
            "first_workflow_created": bool(by_event.get("product.workflow_created")),
            "first_business_signal": bool(by_event.get("product.alert_created") or by_event.get("product.document_ingested")),
        },
    }


async def runtime_event_summary(limit: int = 5000) -> dict:
    async with async_session() as session:
        total = await session.scalar(select(func.count(RuntimeEvent.id)))
        error_total = await session.scalar(select(func.count(RuntimeEvent.id)).where(RuntimeEvent.status == "error"))
        result = await session.execute(
            select(RuntimeEvent.event_type, func.count(RuntimeEvent.id))
            .group_by(RuntimeEvent.event_type)
            .order_by(RuntimeEvent.event_type)
        )
        by_type = {event_type: int(count) for event_type, count in result.all()}
        recent = await session.execute(
            select(RuntimeEvent).order_by(RuntimeEvent.created_at.desc()).limit(limit)
        )
        rows = recent.scalars().all()
    latencies = [
        float((row.payload or {}).get("latency_ms", 0))
        for row in rows
        if isinstance(row.payload, dict) and "latency_ms" in row.payload
    ]
    return {
        "events_total": int(total or 0),
        "errors_total": int(error_total or 0),
        "by_type": by_type,
        "recent_sample": len(rows),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 3) if latencies else 0.0,
        "max_latency_ms": round(max(latencies), 3) if latencies else 0.0,
    }


async def create_alert(payload: dict, actor: str, tenant_id: str) -> dict:
    row = Alert(id=str(uuid.uuid4()), tenant_id=tenant_id, status="open", severity=payload["severity"], payload=payload)
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return _flatten_operational(row, severity=row.severity)


async def list_alerts(tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    limit, offset = clamp_page(limit, offset)
    async with async_session() as session:
        result = await session.execute(
            select(Alert).where(Alert.tenant_id == tenant_id).order_by(Alert.created_at.desc()).offset(offset).limit(limit)
        )
        return [_flatten_operational(row, severity=row.severity) for row in reversed(result.scalars().all())]


async def create_recommendation(payload: dict, tenant_id: str, category: str) -> dict:
    row = Recommendation(id=str(uuid.uuid4()), tenant_id=tenant_id, status="ready", category=category, payload=payload)
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return _flatten_operational(row, category=row.category)


async def list_recommendations(tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    limit, offset = clamp_page(limit, offset)
    async with async_session() as session:
        result = await session.execute(
            select(Recommendation).where(Recommendation.tenant_id == tenant_id).order_by(Recommendation.created_at.desc()).offset(offset).limit(limit)
        )
        return [_flatten_operational(row, category=row.category) for row in reversed(result.scalars().all())]


async def create_document(document_payload: dict, ingestion_payload: dict, tenant_id: str) -> dict:
    document = Document(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        status="registered",
        document_type=document_payload["document_type"],
        payload=document_payload,
    )
    ingestion = DocumentIngestion(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        status=ingestion_payload["status"],
        document_id=document.id,
        payload=ingestion_payload,
    )
    async with async_session() as session:
        async with session.begin():
            session.add(document)
            session.add(ingestion)
    return {
        "document": _flatten_operational(document, document_type=document.document_type),
        "ingestion": _flatten_operational(ingestion, document_id=ingestion.document_id),
    }


async def list_documents(tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    limit, offset = clamp_page(limit, offset)
    async with async_session() as session:
        result = await session.execute(
            select(Document).where(Document.tenant_id == tenant_id).order_by(Document.created_at.desc()).offset(offset).limit(limit)
        )
        return [_flatten_operational(row, document_type=row.document_type) for row in reversed(result.scalars().all())]


async def list_document_ingestions(tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    limit, offset = clamp_page(limit, offset)
    async with async_session() as session:
        result = await session.execute(
            select(DocumentIngestion).where(DocumentIngestion.tenant_id == tenant_id).order_by(DocumentIngestion.created_at.desc()).offset(offset).limit(limit)
        )
        return [_flatten_operational(row, document_id=row.document_id) for row in reversed(result.scalars().all())]


async def create_approval_request(payload: dict, requested_by: str, tenant_id: str) -> dict:
    row = ApprovalRequest(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        scope=payload["scope"],
        action=payload["action"],
        risk=payload["risk"],
        status="blocked" if payload["risk"] == "critical" else "pending",
        requested_by=requested_by,
        metadata_json=payload.get("metadata") or {},
    )
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return approval_to_dict(row)


def approval_to_dict(row: ApprovalRequest) -> dict:
    return {
        "id": row.id,
        "timestamp": _created_at(row.created_at),
        "tenant_id": row.tenant_id,
        "scope": row.scope,
        "action": row.action,
        "risk": row.risk,
        "status": row.status,
        "requested_by": row.requested_by,
        "decided_by": row.decided_by,
        "decision_reason": row.decision_reason,
        "metadata": row.metadata_json or {},
        "version": row.version,
    }


async def decide_approval_request(request_id: str, decision: str, reason: str, decided_by: str, tenant_id: str) -> dict | None:
    async def operation() -> dict | None:
        async with async_session() as session:
            async with session.begin():
                row = await session.get(ApprovalRequest, request_id, with_for_update=True)
                if row is None or row.tenant_id != tenant_id:
                    return None
                if row.status in {"approved", "rejected"}:
                    return approval_to_dict(row)
                if row.status == "blocked" and decision == "approved":
                    row.decision_reason = "critical risk cannot be approved automatically"
                    row.version += 1
                    return approval_to_dict(row)
                row.status = decision
                row.decided_by = decided_by
                row.decision_reason = reason
                row.version += 1
                return approval_to_dict(row)

    return await with_db_retry(operation)


async def is_approval_approved(request_id: str, tenant_id: str) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(ApprovalRequest.id).where(
                ApprovalRequest.id == request_id,
                ApprovalRequest.tenant_id == tenant_id,
                ApprovalRequest.status == "approved",
            )
        )
        return result.scalar_one_or_none() is not None


async def list_approval_requests(tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    limit, offset = clamp_page(limit, offset)
    async with async_session() as session:
        result = await session.execute(
            select(ApprovalRequest).where(ApprovalRequest.tenant_id == tenant_id).order_by(ApprovalRequest.created_at.desc()).offset(offset).limit(limit)
        )
        return [approval_to_dict(row) for row in reversed(result.scalars().all())]


async def create_workflow(payload: dict, tenant_id: str) -> dict:
    record_payload = {**payload, "audit_note": "workflow created; human checkpoint required before execution"}
    row = WorkflowRun(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        status="created",
        current_step=0,
        human_checkpoint_required=True,
        payload=record_payload,
    )
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return workflow_to_dict(row)


def workflow_to_dict(row: WorkflowRun) -> dict:
    payload = dict(row.payload or {})
    return {
        "id": row.id,
        "timestamp": _created_at(row.created_at),
        "tenant_id": row.tenant_id,
        "status": row.status,
        "current_step": row.current_step,
        "human_checkpoint_required": row.human_checkpoint_required,
        "version": row.version,
        **payload,
    }


async def advance_workflow(workflow_id: str, payload: dict, tenant_id: str, approval_ok: bool) -> dict | None:
    async def operation() -> dict | None:
        async with async_session() as session:
            async with session.begin():
                row = await session.get(WorkflowRun, workflow_id, with_for_update=True)
                if row is None or row.tenant_id != tenant_id:
                    return None
                if row.status == "completed":
                    return workflow_to_dict(row)
                record_payload = dict(row.payload or {})
                risk = record_payload.get("risk", "medium")
                steps = record_payload.get("steps") or []
                if row.human_checkpoint_required and not payload.get("checkpoint_acknowledged"):
                    row.status = "blocked"
                    record_payload["audit_note"] = "human checkpoint required"
                elif risk in {"high", "critical"} and not approval_ok:
                    row.status = "blocked"
                    record_payload["audit_note"] = "governance approval required"
                else:
                    row.human_checkpoint_required = False
                    if row.current_step + 1 >= len(steps):
                        row.status = "completed"
                    else:
                        row.current_step += 1
                        row.status = "running"
                    record_payload["audit_note"] = payload.get("note") or "workflow advanced"
                row.version += 1
                row.payload = record_payload
                return workflow_to_dict(row)

    return await with_db_retry(operation)


async def list_workflows(tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    limit, offset = clamp_page(limit, offset)
    async with async_session() as session:
        result = await session.execute(
            select(WorkflowRun).where(WorkflowRun.tenant_id == tenant_id).order_by(WorkflowRun.created_at.desc()).offset(offset).limit(limit)
        )
        return [workflow_to_dict(row) for row in reversed(result.scalars().all())]


async def create_ai_request(payload: dict, tenant_id: str, provider_id: str, status: str) -> dict:
    row = AIRequest(id=str(uuid.uuid4()), tenant_id=tenant_id, status=status, provider_id=provider_id, payload=payload)
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return _flatten_operational(row, provider_id=row.provider_id)


async def list_ai_requests(tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    limit, offset = clamp_page(limit, offset)
    async with async_session() as session:
        result = await session.execute(
            select(AIRequest).where(AIRequest.tenant_id == tenant_id).order_by(AIRequest.created_at.desc()).offset(offset).limit(limit)
        )
        return [_flatten_operational(row, provider_id=row.provider_id) for row in reversed(result.scalars().all())]


async def create_memory_record(tenant_id: str, memory_type: str, payload: dict) -> dict:
    row = MemoryRecord(id=str(uuid.uuid4()), tenant_id=tenant_id, status="recorded", memory_type=memory_type, payload=payload)
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return _flatten_operational(row, memory_type=row.memory_type)


async def list_memory_records(tenant_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    limit, offset = clamp_page(limit, offset)
    async with async_session() as session:
        result = await session.execute(
            select(MemoryRecord).where(MemoryRecord.tenant_id == tenant_id).order_by(MemoryRecord.created_at.desc()).offset(offset).limit(limit)
        )
        return [_flatten_operational(row, memory_type=row.memory_type) for row in reversed(result.scalars().all())]
