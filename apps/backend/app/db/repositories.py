from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import asyncio
import uuid

from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, OperationalError

from app.core.audit import audit_hash
from app.core.config import settings
from app.db.models import (
    AIRequest,
    Alert,
    ApprovalRequest,
    AuthEvent,
    AuditEvent,
    Document,
    DocumentIngestion,
    MemoryRecord,
    Recommendation,
    RevokedToken,
    RuntimeEvent,
    Subscription,
    Tenant,
    User,
    WorkflowRun,
)
from app.db.session import async_session


_audit_chain_locks: dict[str, asyncio.Lock] = {}
_audit_chain_locks_guard = asyncio.Lock()


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
    return {
        "checked_events": checked,
        "legacy_unhashed_events": legacy,
        "tamper_detected": bool(hash_mismatches or broken_links),
        "hash_mismatch_event_ids": hash_mismatches[:10],
        "broken_link_event_ids": broken_links[:10],
        "chain_forks_detected": bool(forks),
        "chain_fork_count": len(forks),
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


async def create_tenant_with_admin(
    *,
    tenant_id: str,
    tenant_name: str,
    admin_username: str,
    password_hash: str,
    plan: str,
    limits: dict,
) -> dict:
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
            tenant = Tenant(id=tenant_id, name=tenant_name, country="PE", status="active")
            user = User(
                id=f"user-{uuid.uuid4().hex}",
                tenant_id=tenant_id,
                username=admin_username,
                password_hash=password_hash,
                role="tenant_admin",
                plan=plan,
                active=True,
            )
            subscription = Subscription(
                id=f"subscription-{uuid.uuid4().hex}",
                tenant_id=tenant_id,
                plan=plan,
                status="active",
                limits=limits,
            )
            session.add_all([tenant, user, subscription])
    return {"created": True, "tenant_id": tenant_id, "admin_username": admin_username, "plan": plan}


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
            users = await session.execute(select(User).where(User.tenant_id == tenant_id))
            for user in users.scalars().all():
                user.plan = plan
    return {"tenant_id": tenant_id, "plan": plan, "limits": limits}


async def current_subscription(tenant_id: str) -> dict | None:
    async with async_session() as session:
        result = await session.execute(
            select(Subscription).where(Subscription.tenant_id == tenant_id, Subscription.status == "active")
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return {"tenant_id": row.tenant_id, "plan": row.plan, "limits": row.limits or {}, "status": row.status}


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
