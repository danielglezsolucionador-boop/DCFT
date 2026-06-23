from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
from typing import Literal


Plan = Literal["free", "student", "free_student", "mype", "premium", "business_basic", "business_premium", "internal", "admin"]
AccountType = Literal["student", "business"]
BillingCycle = Literal["monthly", "annual"]
RiskLevel = Literal["low", "medium", "high", "critical"]
Role = Literal["ceo", "admin", "super_admin", "tenant_admin", "operator", "auditor", "readonly"]
BusinessRoleId = Literal["STUDENT", "PROFESSIONAL", "PREMIUM", "ADMIN"]
BusinessPlanId = Literal["FREE", "PROFESSIONAL", "PREMIUM"]
SunatConnectionState = Literal["NOT_CONNECTED", "CONNECTING", "CONNECTED", "ERROR", "DISABLED"]
SunatCredentialState = Literal["PENDING", "CREDENTIAL_RECEIVED", "VALIDATING", "CONNECTED_READ_ONLY", "ERROR", "DISCONNECTED"]
SunatConnectionType = Literal["CLAVE_SOL_AUXILIAR"]


class CurrentUser(BaseModel):
    user_id: str
    username: str
    tenant_id: str
    role: Role
    plan: Plan
    email_verified: bool = True
    scopes: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    premium: bool = False
    payment_required: bool = True
    internal: bool = False
    access_level: Literal["full", "limited"] = "limited"


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=120)
    login: str | None = Field(default=None, max_length=120)
    identifier: str | None = Field(default=None, max_length=120)
    password: str = Field(min_length=1, max_length=256)

    @model_validator(mode="after")
    def validate_login_identifier(self) -> "LoginRequest":
        identifiers = [
            value.strip()
            for value in (self.username, self.email, self.login, self.identifier)
            if value is not None and value.strip()
        ]
        if not identifiers:
            raise ValueError("username, email, login or identifier is required")
        if len({value.casefold() for value in identifiers}) > 1:
            raise ValueError("login identifiers must match")
        return self

    @property
    def login_identifier(self) -> str:
        for value in (self.username, self.email, self.login, self.identifier):
            if value is not None and value.strip():
                return value.strip()
        raise ValueError("login identifier is required")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmailVerificationResendIn(BaseModel):
    username: str = Field(min_length=3, max_length=120, pattern=r"^[A-Za-z0-9_.@-]+$")


class EmailVerificationResponse(BaseModel):
    email_verified: bool = False
    email_provider_missing: bool = False
    sent: bool = False
    message: str


class CheckoutRequestIn(BaseModel):
    plan: Plan
    billing_cycle: BillingCycle = "monthly"


class CompanySunatAccessIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ruc: str = Field(min_length=8, max_length=20, pattern=r"^[0-9A-Za-z-]+$")
    sunat_username: str = Field(min_length=3, max_length=120, pattern=r"^[A-Za-z0-9_.@-]+$")
    sunat_password: SecretStr = Field(min_length=8, max_length=256)
    consent_accepted: bool = False
    plan: Literal["mype", "premium", "business_basic", "business_premium"] = "mype"
    billing_cycle: BillingCycle = "monthly"


class CompanySunatContinueIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ruc: str = Field(min_length=8, max_length=20, pattern=r"^[0-9A-Za-z-]+$")
    sunat_username: str = Field(min_length=3, max_length=120, pattern=r"^[A-Za-z0-9_.@-]+$")
    plan: Literal["mype", "premium", "business_basic", "business_premium"] = "mype"
    billing_cycle: BillingCycle = "monthly"


class StudentDoctorAskIn(BaseModel):
    question: str = Field(min_length=3, max_length=1200)


class StudentDoctorQuotaOut(BaseModel):
    user_id: str
    tenant_id: str
    month_key: str
    year: int
    month: int
    questions_used: int
    questions_limit: int
    questions_remaining: int
    timestamps: list[str] = Field(default_factory=list)
    last_question: str | None = None
    status: str
    created_at: str | None = None
    updated_at: str | None = None
    last_asked_at: str | None = None


class StudentDoctorStatusOut(BaseModel):
    doctor_name: str
    available: bool
    ai_provider_missing: bool
    provider: str | None = None
    model: str | None = None
    quota: StudentDoctorQuotaOut
    message: str


class StudentDoctorAnswerOut(BaseModel):
    doctor_name: str
    answer: str
    provider: str
    model: str | None = None
    quota: StudentDoctorQuotaOut
    educational_disclaimer: str


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


class SunatAuxiliaryCredentialIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    empresa_id: str = Field(min_length=3, max_length=64)
    workspace_id: str = Field(min_length=3, max_length=64)
    ruc: str = Field(min_length=8, max_length=20, pattern=r"^[0-9A-Za-z-]+$")
    sunat_username: str = Field(min_length=3, max_length=120, pattern=r"^[A-Za-z0-9_.@-]+$")
    sunat_password: SecretStr = Field(min_length=8, max_length=256)
    consent_accepted: bool = False
    auxiliary_user_acknowledged: bool = False
    read_only_acknowledged: bool = False
    no_tax_action_acknowledged: bool = False


class SunatDisconnectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(default="user_revoked", min_length=3, max_length=240)


class SunatSyncIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sync_scope: list[str] = Field(default_factory=lambda: ["public_taxpayer_profile"], max_length=10)


class SunatReadonlyRunIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    empresa_id: str = Field(min_length=3, max_length=64)
    workspace_id: str = Field(min_length=3, max_length=64)


class SunatApiCredentialsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    empresa_id: str = Field(min_length=3, max_length=64)
    workspace_id: str = Field(min_length=3, max_length=64)
    ruc: str = Field(min_length=8, max_length=20, pattern=r"^[0-9A-Za-z-]+$")
    client_id: str = Field(min_length=8, max_length=180, pattern=r"^[A-Za-z0-9_.:-]+$")
    client_secret: SecretStr = Field(min_length=8, max_length=512)
    consent_accepted: bool = False
    api_credentials_acknowledged: bool = False
    official_api_acknowledged: bool = False
    no_sensitive_actions_acknowledged: bool = False


class SunatApiActionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    empresa_id: str = Field(min_length=3, max_length=64)
    workspace_id: str = Field(min_length=3, max_length=64)


class SunatCpeTestIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    empresa_id: str = Field(min_length=3, max_length=64)
    workspace_id: str = Field(min_length=3, max_length=64)
    numRuc: str = Field(min_length=11, max_length=11, pattern=r"^[0-9]{11}$")
    codComp: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z0-9]{2}$")
    numeroSerie: str = Field(min_length=1, max_length=4, pattern=r"^[A-Za-z0-9]{1,4}$")
    numero: int = Field(ge=1, le=999999999)
    fechaEmision: str = Field(min_length=10, max_length=10, pattern=r"^[0-9]{2}/[0-9]{2}/[0-9]{4}$")
    monto: float | None = Field(default=None, ge=0, le=999999999)


class SunatSireSyncIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    empresa_id: str = Field(min_length=3, max_length=64)
    workspace_id: str = Field(min_length=3, max_length=64)
    period: str = Field(min_length=6, max_length=6, pattern=r"^[0-9]{6}$")


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
    real_sunat_session: bool = False
    read_only: bool = True
    remote_actions_enabled: bool = False
    pilot_requires_auxiliary_user: bool = False
    sol_credentials_allowed: bool = True
    commercial_credential_mode: str = "SUNAT_SOL_CREDENTIALS"
    credential_capture_enabled: bool = False
    credential_storage_enabled: bool = False


class SunatAuxiliaryCredentialStatusOut(BaseModel):
    id: str | None = None
    tenant_id: str | None = None
    empresa_id: str | None = None
    workspace_id: str | None = None
    status: SunatCredentialState
    ruc_masked: str | None = None
    sunat_username_masked: str | None = None
    read_only: bool = True
    remote_actions_enabled: bool = False
    real_sunat_session: bool = False
    real_connector_enabled: bool = False
    credential_capture_enabled: bool = True
    credential_storage_enabled: bool = True
    encrypted_credential_storage: bool = True
    sol_credentials_allowed: bool = True
    commercial_credential_mode: str = "SUNAT_SOL_CREDENTIALS"
    last_validated_at: str | None = None
    disconnected_at: str | None = None


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


class TaxAIAskIn(BaseModel):
    question: str = Field(min_length=3, max_length=1200)
    context: str = Field(default="", max_length=4000)


class TaxAIAnswerOut(BaseModel):
    answer: str
    provider: str | None = None
    model: str | None = None
    ai_provider_missing: bool = False
    configured: bool = False
    educational_disclaimer: str


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
