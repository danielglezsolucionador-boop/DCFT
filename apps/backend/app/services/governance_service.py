from __future__ import annotations

import uuid

from app.core.audit import append_audit_event, utc_now
from app.core.storage import store


class GovernanceService:
    def __init__(self) -> None:
        self._store = store("approval_requests")

    def create_request(self, payload: dict, requested_by: str, tenant_id: str) -> dict:
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": utc_now(),
            "tenant_id": tenant_id,
            "status": "blocked" if payload["risk"] == "critical" else "pending",
            "requested_by": requested_by,
            "decided_by": None,
            "decision_reason": None,
            **payload,
        }
        self._store.update([], lambda rows: rows.append(record))
        append_audit_event("governance.request_created", requested_by, {"id": record["id"], "risk": record["risk"]}, risk=record["risk"], tenant_id=tenant_id)
        return record

    def decide(self, request_id: str, decision: str, reason: str, decided_by: str, tenant_id: str) -> dict | None:
        result: dict | None = None

        def mutate(rows: list[dict]) -> None:
            nonlocal result
            for row in rows:
                if row["id"] == request_id and row["tenant_id"] == tenant_id:
                    if row["status"] == "blocked" and decision == "approved":
                        result = dict(row)
                        result["decision_reason"] = "critical risk cannot be approved automatically"
                        return
                    row["status"] = decision
                    row["decided_by"] = decided_by
                    row["decision_reason"] = reason
                    result = dict(row)
                    return

        self._store.update([], mutate)
        if result is not None:
            append_audit_event("governance.request_decided", decided_by, {"id": request_id, "decision": result["status"]}, risk=result["risk"], tenant_id=tenant_id)
        return result

    def is_approved(self, request_id: str, tenant_id: str) -> bool:
        return any(row["id"] == request_id and row["tenant_id"] == tenant_id and row["status"] == "approved" for row in self._store.read([]))

    def list(self, tenant_id: str, limit: int = 100) -> list[dict]:
        rows = [row for row in self._store.read([]) if row["tenant_id"] == tenant_id]
        return rows[-limit:]


governance_service = GovernanceService()