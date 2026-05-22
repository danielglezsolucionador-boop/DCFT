from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
import time


@dataclass
class Metrics:
    started_at: float = field(default_factory=time.time)
    requests_total: int = 0
    errors_total: int = 0
    auth_failures: int = 0
    governance_events: int = 0
    audit_events: int = 0
    workflow_events: int = 0
    latency_total_ms: float = 0.0
    by_path: dict[str, int] = field(default_factory=dict)
    by_tenant: dict[str, int] = field(default_factory=dict)


class MetricsRegistry:
    def __init__(self) -> None:
        self._metrics = Metrics()
        self._lock = RLock()

    def record_request(self, path: str, status_code: int, latency_ms: float) -> None:
        with self._lock:
            self._metrics.requests_total += 1
            self._metrics.latency_total_ms += latency_ms
            self._metrics.by_path[path] = self._metrics.by_path.get(path, 0) + 1
            if status_code >= 500:
                self._metrics.errors_total += 1

    def record_error(self) -> None:
        with self._lock:
            self._metrics.errors_total += 1

    def record_auth_failure(self) -> None:
        with self._lock:
            self._metrics.auth_failures += 1

    def record_governance_event(self) -> None:
        with self._lock:
            self._metrics.governance_events += 1

    def record_audit_event(self) -> None:
        with self._lock:
            self._metrics.audit_events += 1

    def record_workflow_event(self) -> None:
        with self._lock:
            self._metrics.workflow_events += 1

    def record_tenant_access(self, tenant_id: str) -> None:
        with self._lock:
            self._metrics.by_tenant[tenant_id] = self._metrics.by_tenant.get(tenant_id, 0) + 1

    def snapshot(self) -> dict:
        with self._lock:
            avg_latency = (
                self._metrics.latency_total_ms / self._metrics.requests_total
                if self._metrics.requests_total
                else 0.0
            )
            return {
                "uptime_seconds": round(time.time() - self._metrics.started_at, 3),
                "requests_total": self._metrics.requests_total,
                "errors_total": self._metrics.errors_total,
                "auth_failures": self._metrics.auth_failures,
                "governance_events": self._metrics.governance_events,
                "audit_events": self._metrics.audit_events,
                "workflow_events": self._metrics.workflow_events,
                "avg_latency_ms": round(avg_latency, 3),
                "by_path": dict(sorted(self._metrics.by_path.items())),
                "by_tenant": dict(sorted(self._metrics.by_tenant.items())),
            }


metrics_registry = MetricsRegistry()
