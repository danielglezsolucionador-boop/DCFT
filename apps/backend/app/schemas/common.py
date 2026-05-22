from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


Plan = Literal["free_student", "business_basic", "business_premium"]
RiskLevel = Literal["low", "medium", "high", "critical"]


class CurrentUser(BaseModel):
    username: str
    tenant_id: str
    role: str
    plan: Plan
    scopes: list[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ApprovalRequestIn(BaseModel):
    scope: str
    action: str
    risk: RiskLevel = "medium"
    reason: str
    metadata: dict[str, str] = Field(default_factory=dict)


class ApprovalDecisionIn(BaseModel):
    decision: Literal["approved", "rejected"]
    reason: str


class WorkflowIn(BaseModel):
    name: str
    objective: str
    steps: list[str] = Field(min_length=1)
    risk: RiskLevel = "medium"


class WorkflowAdvanceIn(BaseModel):
    checkpoint_acknowledged: bool = False
    approval_request_id: str | None = None
    note: str = ""


class DocumentIn(BaseModel):
    filename: str
    source: str = "local"
    content_type: str = "application/octet-stream"
    size_bytes: int = 0
    declared_type: str | None = None


class RecommendationIn(BaseModel):
    category: str = "financial"
    objective: str
    facts: dict[str, str | int | float | bool] = Field(default_factory=dict)


class AlertIn(BaseModel):
    title: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    source: str = "manual"
    details: dict[str, str] = Field(default_factory=dict)


class AIRequestIn(BaseModel):
    objective: str
    input_summary: str
    constraints: list[str] = Field(default_factory=list)