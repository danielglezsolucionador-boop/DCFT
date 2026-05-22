from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


Plan = Literal["free", "student", "free_student", "business_basic", "business_premium"]
RiskLevel = Literal["low", "medium", "high", "critical"]
Role = Literal["super_admin", "tenant_admin", "operator", "auditor", "readonly"]


class CurrentUser(BaseModel):
    username: str
    tenant_id: str
    role: Role
    plan: Plan
    scopes: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OnboardingTenantIn(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=180)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
    admin_username: str = Field(min_length=3, max_length=120, pattern=r"^[A-Za-z0-9_.@-]+$")
    admin_password: str = Field(min_length=10, max_length=256)
    plan: Plan = "business_basic"


class SubscriptionUpdateIn(BaseModel):
    plan: Plan


class AnalyticsEventIn(BaseModel):
    event_type: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9_.-]+$")
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class ApprovalRequestIn(BaseModel):
    scope: str = Field(min_length=1, max_length=120)
    action: str = Field(min_length=1, max_length=2000)
    risk: RiskLevel = "medium"
    reason: str = Field(min_length=1, max_length=2000)
    metadata: dict[str, str] = Field(default_factory=dict)


class ApprovalDecisionIn(BaseModel):
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=1, max_length=2000)


class WorkflowIn(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    objective: str = Field(min_length=1, max_length=4000)
    steps: list[str] = Field(min_length=1, max_length=40)
    risk: RiskLevel = "medium"


class WorkflowAdvanceIn(BaseModel):
    checkpoint_acknowledged: bool = False
    approval_request_id: str | None = None
    note: str = Field(default="", max_length=2000)


class DocumentIn(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    source: str = Field(default="local", max_length=120)
    content_type: str = Field(default="application/octet-stream", max_length=120)
    size_bytes: int = Field(default=0, ge=0, le=100_000_000)
    declared_type: str | None = Field(default=None, max_length=120)


class RecommendationIn(BaseModel):
    category: str = Field(default="financial", max_length=80)
    objective: str = Field(min_length=1, max_length=4000)
    facts: dict[str, str | int | float | bool] = Field(default_factory=dict)


class AlertIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    source: str = Field(default="manual", max_length=120)
    details: dict[str, str] = Field(default_factory=dict)


class AIRequestIn(BaseModel):
    objective: str = Field(min_length=1, max_length=4000)
    input_summary: str = Field(min_length=1, max_length=8000)
    constraints: list[str] = Field(default_factory=list, max_length=40)
