from __future__ import annotations

import uuid

from app.core.audit import append_audit_event, utc_now
from app.core.storage import store
from app.services.governance_service import governance_service


class WorkflowService:
    def __init__(self) -> None:
        self._store = store("workflow_runs")

    def create(self, payload: dict, actor: str, tenant_id: str) -> dict:
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": utc_now(),
            "tenant_id": tenant_id,
            "status": "created",
            "current_step": 0,
            "human_checkpoint_required": True,
            "audit_note": "workflow created; human checkpoint required before execution",
            **payload,
        }
        self._store.update([], lambda rows: rows.append(record))
        append_audit_event("workflow.created", actor, {"id": record["id"], "steps": len(record["steps"])}, risk=record["risk"], tenant_id=tenant_id)
        return record

    def advance(self, workflow_id: str, payload: dict, actor: str, tenant_id: str) -> dict | None:
        result: dict | None = None

        def mutate(rows: list[dict]) -> None:
            nonlocal result
            for row in rows:
                if row["id"] == workflow_id and row["tenant_id"] == tenant_id:
                    if row["human_checkpoint_required"] and not payload.get("checkpoint_acknowledged"):
                        row["status"] = "blocked"
                        row["audit_note"] = "human checkpoint required"
                    elif row["risk"] in {"high", "critical"} and not governance_service.is_approved(payload.get("approval_request_id") or "", tenant_id):
                        row["status"] = "blocked"
                        row["audit_note"] = "governance approval required"
                    else:
                        row["human_checkpoint_required"] = False
                        if row["current_step"] + 1 >= len(row["steps"]):
                            row["status"] = "completed"
                        else:
                            row["current_step"] += 1
                            row["status"] = "running"
                        row["audit_note"] = payload.get("note") or "workflow advanced"
                    result = dict(row)
                    return

        self._store.update([], mutate)
        if result is not None:
            append_audit_event("workflow.advanced", actor, {"id": workflow_id, "status": result["status"], "current_step": result["current_step"]}, risk=result["risk"], tenant_id=tenant_id)
        return result

    def list(self, tenant_id: str, limit: int = 100) -> list[dict]:
        return [row for row in self._store.read([]) if row["tenant_id"] == tenant_id][-limit:]


workflow_service = WorkflowService()