from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import func, select

from app.db.models import (
    AIRequest,
    Alert,
    ApprovalRequest,
    AuditEvent,
    Document,
    DocumentIngestion,
    MemoryRecord,
    Recommendation,
    WorkflowRun,
)
from app.db.session import async_session


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _created_at(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else utc_now()


def _flatten_operational(row: Any, **extra: Any) -> dict:
    payload = dict(row.payload or {})
    return {
        "id": row.id,
        "timestamp": _created_at(row.created_at),
        "tenant_id": row.tenant_id,
        "status": row.status,
        **extra,
        **payload,
    }


async def add_audit_event(event_type: str, actor: str, payload: dict, risk: str, tenant_id: str) -> dict:
    event = AuditEvent(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        event_type=event_type,
        actor=actor,
        risk=risk,
        payload=payload,
    )
    async with async_session() as session:
        async with session.begin():
            session.add(event)
    return {
        "id": event.id,
        "timestamp": utc_now(),
        "tenant_id": tenant_id,
        "event_type": event_type,
        "actor": actor,
        "risk": risk,
        "payload": payload,
    }


async def count_audit_events(tenant_id: str | None = None) -> int:
    async with async_session() as session:
        statement = select(func.count(AuditEvent.id))
        if tenant_id is not None:
            statement = statement.where(AuditEvent.tenant_id == tenant_id)
        result = await session.execute(statement)
        return int(result.scalar_one())


async def create_alert(payload: dict, actor: str, tenant_id: str) -> dict:
    row = Alert(id=str(uuid.uuid4()), tenant_id=tenant_id, status="open", severity=payload["severity"], payload=payload)
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return _flatten_operational(row, severity=row.severity)


async def list_alerts(tenant_id: str, limit: int = 100) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Alert).where(Alert.tenant_id == tenant_id).order_by(Alert.created_at.desc()).limit(limit)
        )
        return [_flatten_operational(row, severity=row.severity) for row in reversed(result.scalars().all())]


async def create_recommendation(payload: dict, tenant_id: str, category: str) -> dict:
    row = Recommendation(id=str(uuid.uuid4()), tenant_id=tenant_id, status="ready", category=category, payload=payload)
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return _flatten_operational(row, category=row.category)


async def list_recommendations(tenant_id: str, limit: int = 100) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Recommendation).where(Recommendation.tenant_id == tenant_id).order_by(Recommendation.created_at.desc()).limit(limit)
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


async def list_documents(tenant_id: str, limit: int = 100) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Document).where(Document.tenant_id == tenant_id).order_by(Document.created_at.desc()).limit(limit)
        )
        return [_flatten_operational(row, document_type=row.document_type) for row in reversed(result.scalars().all())]


async def list_document_ingestions(tenant_id: str, limit: int = 100) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(DocumentIngestion).where(DocumentIngestion.tenant_id == tenant_id).order_by(DocumentIngestion.created_at.desc()).limit(limit)
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
    }


async def decide_approval_request(request_id: str, decision: str, reason: str, decided_by: str, tenant_id: str) -> dict | None:
    async with async_session() as session:
        async with session.begin():
            row = await session.get(ApprovalRequest, request_id, with_for_update=True)
            if row is None or row.tenant_id != tenant_id:
                return None
            if row.status in {"approved", "rejected"}:
                return approval_to_dict(row)
            if row.status == "blocked" and decision == "approved":
                row.decision_reason = "critical risk cannot be approved automatically"
                return approval_to_dict(row)
            row.status = decision
            row.decided_by = decided_by
            row.decision_reason = reason
            return approval_to_dict(row)


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


async def list_approval_requests(tenant_id: str, limit: int = 100) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(ApprovalRequest).where(ApprovalRequest.tenant_id == tenant_id).order_by(ApprovalRequest.created_at.desc()).limit(limit)
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
        **payload,
    }


async def advance_workflow(workflow_id: str, payload: dict, tenant_id: str, approval_ok: bool) -> dict | None:
    async with async_session() as session:
        async with session.begin():
            row = await session.get(WorkflowRun, workflow_id, with_for_update=True)
            if row is None or row.tenant_id != tenant_id:
                return None
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
            row.payload = record_payload
            return workflow_to_dict(row)


async def list_workflows(tenant_id: str, limit: int = 100) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(WorkflowRun).where(WorkflowRun.tenant_id == tenant_id).order_by(WorkflowRun.created_at.desc()).limit(limit)
        )
        return [workflow_to_dict(row) for row in reversed(result.scalars().all())]


async def create_ai_request(payload: dict, tenant_id: str, provider_id: str, status: str) -> dict:
    row = AIRequest(id=str(uuid.uuid4()), tenant_id=tenant_id, status=status, provider_id=provider_id, payload=payload)
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return _flatten_operational(row, provider_id=row.provider_id)


async def list_ai_requests(tenant_id: str, limit: int = 100) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(AIRequest).where(AIRequest.tenant_id == tenant_id).order_by(AIRequest.created_at.desc()).limit(limit)
        )
        return [_flatten_operational(row, provider_id=row.provider_id) for row in reversed(result.scalars().all())]


async def create_memory_record(tenant_id: str, memory_type: str, payload: dict) -> dict:
    row = MemoryRecord(id=str(uuid.uuid4()), tenant_id=tenant_id, status="recorded", memory_type=memory_type, payload=payload)
    async with async_session() as session:
        async with session.begin():
            session.add(row)
    return _flatten_operational(row, memory_type=row.memory_type)


async def list_memory_records(tenant_id: str, limit: int = 100) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(MemoryRecord).where(MemoryRecord.tenant_id == tenant_id).order_by(MemoryRecord.created_at.desc()).limit(limit)
        )
        return [_flatten_operational(row, memory_type=row.memory_type) for row in reversed(result.scalars().all())]
