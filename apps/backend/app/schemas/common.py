from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


Plan = Literal["free", "student", "free_student", "mype", "premium", "business_basic", "business_premium"]
AccountType = Literal["student", "business"]
RiskLevel = Literal["low", "medium", "high", "critical"]
Role = Literal["super_admin", "tenant_admin", "operator", "auditor", "readonly"]
BusinessRoleId = Literal["STUDENT", "PROFESSIONAL", "PREMIUM", "ADMIN"]
BusinessPlanId = Literal["FREE", "PROFESSIONAL", "PREMIUM"]
SunatConnectionState = Literal["NOT_CONNECTED", "CONNECTING", "CONNECTED", "ERROR", "DISABLED"]
SunatConnectionType = Literal["CLAVE_SOL_AUXILIAR"]


class CurrentUser(BaseModel):
    user_id: str
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
    plan: Plan = "mype"
    account_type: AccountType = "business"
    ruc: str | None = Field(default=None, min_length=8, max_length=20, pattern=r"^[0-9A-Za-z-]+$")
    razon_social: str | None = Field(default=None, min_length=2, max_length=180)
    nombre_comercial: str = Field(default="", max_length=180)
    regimen_tributario: str = Field(default="mype_tributario", min_length=2, max_length=80)
    trial_requested: bool = True


class SubscriptionUpdateIn(BaseModel):
    plan: Plan


class AdminTrialUpdateIn(BaseModel):
    active: bool = True
    days: int = Field(default=7, ge=1, le=30)


class AdminPlanUpdateIn(BaseModel):
    plan: Plan


class CompanyIn(BaseModel):
    ruc: str = Field(min_length=8, max_length=20, pattern=r"^[0-9A-Za-z-]+$")
    razon_social: str = Field(min_length=2, max_length=180)
    nombre_comercial: str = Field(default="", max_length=180)
    regimen_tributario: str = Field(default="general", min_length=2, max_length=80)
    estado: str = Field(default="active", min_length=2, max_length=32)
    pais: str = Field(default="PE", min_length=2, max_length=80)
    moneda: str = Field(default="PEN", min_length=2, max_length=16)


class CompanyOut(BaseModel):
    id: str
    tenant_id: str
    ruc: str
    razon_social: str
    nombre_comercial: str
    regimen_tributario: str
    estado: str
    pais: str
    moneda: str
    created_at: str
    updated_at: str


class WorkspaceIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=180)
    empresa_id: str = Field(min_length=3, max_length=64)
    estado: str = Field(default="active", min_length=2, max_length=32)
    plan_id: BusinessPlanId = "FREE"


class WorkspaceOut(BaseModel):
    id: str
    tenant_id: str
    nombre: str
    propietario: str
    empresa_id: str
    estado: str
    plan_id: BusinessPlanId
    created_at: str
    updated_at: str


class WorkspaceMembershipIn(BaseModel):
    user_id: str = Field(min_length=3, max_length=64)
    role_id: BusinessRoleId


class WorkspaceMembershipOut(BaseModel):
    user_id: str
    workspace_id: str
    tenant_id: str
    role_id: BusinessRoleId
    estado: str
    created_at: str


class ActiveCompanyIn(BaseModel):
    company_id: str = Field(min_length=3, max_length=64)


class ActiveWorkspaceIn(BaseModel):
    workspace_id: str = Field(min_length=3, max_length=64)


class ActiveOperationalContextOut(BaseModel):
    user_id: str
    tenant_id: str
    active_company_id: str | None
    active_workspace_id: str | None
    active_user_id: str
    updated_at: str | None = None


class PermissionMatrixOut(BaseModel):
    roles: dict[str, list[str]]
    plans: dict[str, dict]
    enforced_by_backend: bool = True


class SunatConnectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    empresa_id: str = Field(min_length=3, max_length=64)
    workspace_id: str = Field(min_length=3, max_length=64)
    connection_type: SunatConnectionType = "CLAVE_SOL_AUXILIAR"
    auxiliary_user_alias: str = Field(default="", max_length=120)
    credential_reference: str | None = Field(default=None, min_length=3, max_length=160, pattern=r"^[A-Za-z0-9_.:/-]+$")
    consent_accepted: bool = False
    auxiliary_user_acknowledged: bool = False
    read_only_acknowledged: bool = False
    no_tax_action_acknowledged: bool = False


class SunatAuxiliaryPreparationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    empresa_id: str = Field(min_length=3, max_length=64)
    workspace_id: str = Field(min_length=3, max_length=64)
    ruc: str = Field(min_length=8, max_length=20, pattern=r"^[0-9A-Za-z-]+$")
    auxiliary_user_alias: str = Field(min_length=3, max_length=120)


class SunatDisconnectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(default="user_revoked", min_length=3, max_length=240)


class SunatSyncIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sync_scope: list[str] = Field(default_factory=lambda: ["public_taxpayer_profile"], max_length=10)


class SunatConnectionOut(BaseModel):
    id: str
    tenant_id: str
    empresa_id: str
    workspace_id: str
    estado: SunatConnectionState
    connection_type: SunatConnectionType
    auxiliary_user_alias: str
    created_by: str
    updated_by: str | None
    last_error: str | None
    created_at: str
    updated_at: str
    last_sync_at: str | None
    real_sunat_session: bool = False
    read_only: bool = True
    remote_actions_enabled: bool = False


class SunatConnectionEventOut(BaseModel):
    id: str
    tenant_id: str
    connection_id: str
    empresa_id: str
    workspace_id: str
    actor_user_id: str
    event_type: str
    status: str
    metadata: dict
    created_at: str


class SunatConnectionStatusOut(BaseModel):
    connection: SunatConnectionOut | None
    status: SunatConnectionState
    foundation_only: bool = True
    real_connector_enabled: bool = False


class AnalyticsEventIn(BaseModel):
    event_type: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9_.-]+$")
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class FeedbackIn(BaseModel):
    category: Literal["onboarding", "workflow", "confusion", "bug", "performance", "other"] = "other"
    message: str = Field(min_length=3, max_length=2000)
    severity: Literal["low", "medium", "high"] = "medium"


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


class MemoryRecordIn(BaseModel):
    memory_type: str = Field(default="operational", min_length=2, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    title: str = Field(min_length=1, max_length=240)
    content: str = Field(min_length=1, max_length=8000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    source: str = Field(default="manual", max_length=120)


class TaxWorkflowIn(BaseModel):
    workflow_type: Literal["sunat_notice_review", "monthly_obligation_review"] = "sunat_notice_review"
    objective: str = Field(min_length=1, max_length=4000)
    facts: dict[str, str | int | float | bool] = Field(default_factory=dict)
