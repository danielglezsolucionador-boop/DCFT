import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  BarChart3,
  BellRing,
  Building2,
  CheckCircle2,
  ClipboardList,
  Clock3,
  FileCheck2,
  FileText,
  Gauge,
  HeartPulse,
  Home,
  Landmark,
  Layers3,
  Lock,
  LogOut,
  MessageCircle,
  RefreshCcw,
  Scale,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  UserCircle,
  UserPlus,
  WalletCards,
  X
} from "lucide-react";
import { type CSSProperties, type FormEvent, type ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import { API_URL, ApiError, patch, post, request, type Session } from "./lib/api";

type SignalTone = "green" | "yellow" | "red" | "neutral";
type PanelKey = "diagnostico" | "reportes" | "doctor" | "perfil" | "premium" | "onboarding" | "sunat" | "empresa" | "admin";

type RuntimeStatus = {
  status: string;
  runtime_loop?: string;
  busy_loop: boolean;
  environment?: string;
  staging_ready?: boolean;
  production_ready?: boolean;
  zero_write_policy?: boolean;
  human_in_the_loop?: boolean;
  privacy_first?: boolean;
  ai_pipeline: string;
  ocr_pipeline: string;
  database?: { status: string; backend: string };
  audit_events?: number;
  persistent_observability?: {
    events_total: number;
    errors_total: number;
    avg_latency_ms: number;
    max_latency_ms: number;
    recent_sample: number;
    by_type: Record<string, number>;
  };
  audit_integrity?: {
    checked_events: number;
    legacy_unhashed_events: number;
    tamper_detected: boolean;
    chain_forks_detected: boolean;
  };
};

type Summary = {
  product: string;
  tagline: string;
  tenant_id: string;
  counts: Record<string, number>;
  plan: {
    id: string;
    name: string;
    limits: Record<string, number | string>;
  };
  trial?: {
    status: string;
    active?: boolean;
    expired?: boolean;
    days_remaining?: number;
    plan_base?: string;
    plan_effective?: string;
    started_at?: string | null;
    ends_at?: string | null;
  };
  usage?: {
    current: Record<string, number>;
    limits: Record<string, number>;
    over_limit: Record<string, { current: number; limit: number }>;
  };
  runtime: RuntimeStatus;
  activation?: Record<string, boolean>;
  boundaries: string[];
};

type PlanDefinition = {
  id: string;
  name: string;
  features: string[];
  limits: Record<string, number>;
  commercial_tier?: string;
  trial_days?: number;
  requires_ruc?: boolean;
};

type OnboardingStatus = {
  signup_enabled: boolean;
  plans: PlanDefinition[];
  steps: string[];
  boundaries: string[];
};

type AnalyticsSummary = {
  events_total: number;
  failures_total: number;
  by_event: Record<string, Record<string, number>>;
  activation: {
    onboarding_completed: boolean;
    first_workflow_created: boolean;
    first_business_signal: boolean;
  };
};

type OnboardingResult = {
  tenant_id: string;
  admin_username: string;
  access_token: string;
  token_type: string;
  plan: PlanDefinition;
  trial?: {
    status: string;
    started_at?: string | null;
    ends_at?: string | null;
    days?: number;
  };
  company?: Company | null;
  workspace?: Workspace | null;
  context?: ActiveContext | null;
  next_steps: string[];
};

type Health = {
  status: string;
  production_ready: boolean;
  staging_ready: boolean;
  environment?: string;
  database?: { status: string; backend: string };
  modules: Record<string, string>;
  security_warnings: string[];
};

type CurrentUser = {
  user_id?: string;
  username: string;
  tenant_id: string;
  role: string;
  plan: string;
  permissions: string[];
};

type Company = {
  id: string;
  tenant_id: string;
  ruc: string;
  razon_social: string;
  nombre_comercial: string;
  regimen_tributario: string;
  estado: string;
  pais: string;
  moneda: string;
  created_at: string;
  updated_at: string;
};

type Workspace = {
  id: string;
  tenant_id: string;
  nombre: string;
  propietario: string;
  empresa_id: string;
  estado: string;
  plan_id: string;
  created_at: string;
  updated_at: string;
};

type ActiveContext = {
  user_id: string;
  tenant_id: string;
  active_company_id: string | null;
  active_workspace_id: string | null;
  active_user_id: string;
  updated_at?: string | null;
};

type PermissionMatrix = {
  roles: Record<string, string[]>;
  plans: Record<string, { limits: Record<string, number>; features: string[] }>;
  enforced_by_backend: boolean;
};

type SunatConnection = {
  id: string;
  tenant_id: string;
  empresa_id: string;
  workspace_id: string;
  estado: string;
  connection_type: string;
  auxiliary_user_alias: string;
  created_by: string;
  updated_by?: string | null;
  last_error?: string | null;
  created_at: string;
  updated_at: string;
  last_sync_at?: string | null;
  real_sunat_session: boolean;
  read_only: boolean;
  remote_actions_enabled: boolean;
};

type SunatStatus = {
  connection: SunatConnection | null;
  status: string;
  foundation_only: boolean;
  real_connector_enabled: boolean;
};

type OnboardingVideo = {
  id: string;
  title: string;
  description: string;
  placeholder: boolean;
  duration_hint: string;
  seen: boolean;
  button_label: string;
};

type OnboardingProgress = {
  tenant_id: string;
  user_id: string;
  account_created: boolean;
  company_registered: boolean;
  ruc_registered: boolean;
  videos_seen: string[];
  sunat_auxiliary_prepared: boolean;
  initial_diagnosis_pending: boolean;
  completed: boolean;
  checklist: Record<string, boolean>;
  ready_for_testing: boolean;
  plan_base?: string;
  plan_effective?: string;
  trial?: {
    status: string;
    active: boolean;
    expired: boolean;
    days_remaining: number;
    started_at?: string | null;
    ends_at?: string | null;
  };
  videos: OnboardingVideo[];
};

type AdminUser = {
  user_id: string;
  tenant_id: string;
  tenant_name: string;
  username: string;
  email: string;
  name: string;
  role: string;
  plan: string;
  plan_effective: string;
  trial: OnboardingProgress["trial"];
  company: Company | null;
  workspace: Workspace | null;
  onboarding: OnboardingProgress;
  sunat_auxiliary_prepared: boolean;
  active: boolean;
  created_at: string;
};

type AdminUsersResponse = {
  users: AdminUser[];
  protected: boolean;
  admin: string;
};

type OperationalRecord = {
  id: string;
  timestamp: string;
  tenant_id: string;
  status: string;
  version?: number;
  title?: string;
  severity?: "low" | "medium" | "high" | "critical";
  source?: string;
  details?: Record<string, string>;
  category?: string;
  objective?: string;
  recommendation?: string;
  explainability?: {
    method?: string;
    inputs_used?: string[];
    limitations?: string[];
    recommendation?: string;
  };
};

type DocumentRecord = OperationalRecord & {
  document_type?: string;
  document_id?: string;
  ocr_status?: string;
  explanation?: string;
  metadata?: {
    filename?: string;
    source?: string;
    content_type?: string;
    size_bytes?: number;
    declared_type?: string | null;
  };
};

type GovernanceRequest = {
  id: string;
  timestamp: string;
  tenant_id: string;
  scope: string;
  action: string;
  risk: "low" | "medium" | "high" | "critical";
  status: "pending" | "blocked" | "approved" | "rejected";
  requested_by: string;
  decided_by?: string | null;
  decision_reason?: string | null;
  version: number;
};

type AuditResponse = {
  tenant_id: string;
  events: Array<{
    id: string;
    timestamp: string;
    event_type: string;
    actor: string;
    risk: string;
  }>;
  integrity: RuntimeStatus["audit_integrity"];
};

const PRODUCT_NAME = "DCFT";
const PRODUCT_FULL_NAME = "Doctor Contable Financiero Tributario";
const PRODUCT_TAGLINE = "Centro Premium de Salud Empresarial";
const PRODUCT_PROMISE = "Prevencion hoy, tranquilidad siempre, futuro asegurado.";

const NAV_ITEMS = [
  { href: "#dashboard", label: "Inicio", icon: Home },
  { href: "#diagnostic", label: "Diagnostico", icon: Search },
  { href: "#reports", label: "Reportes", icon: FileText },
  { href: "#doctor", label: "Doctor", icon: Stethoscope },
  { href: "#profile", label: "Perfil", icon: UserCircle }
];

const DESKTOP_NAV_ITEMS: Array<{ label: string; icon: typeof Home; href?: string; panel?: PanelKey }> = [
  { href: "#dashboard", label: "Inicio", icon: Home },
  { panel: "diagnostico", label: "Diagnostico", icon: Search },
  { panel: "diagnostico", label: "Alertas", icon: BellRing },
  { panel: "reportes", label: "Reportes", icon: FileText },
  { panel: "doctor", label: "Doctor", icon: Stethoscope },
  { panel: "empresa", label: "Empresas", icon: Building2 },
  { panel: "admin", label: "Admin CEO", icon: Settings2 },
  { panel: "perfil", label: "Perfil", icon: UserCircle }
];

function toneLabel(tone: SignalTone) {
  if (tone === "green") return "Operativo";
  if (tone === "yellow") return "Atencion";
  if (tone === "red") return "Critico";
  return "Pendiente";
}

function businessStatusLabel(tone: SignalTone) {
  if (tone === "green") return "En orden";
  if (tone === "yellow") return "Atencion";
  if (tone === "red") return "Riesgo";
  return "Sin sesion";
}

function severityTone(severity?: string): SignalTone {
  if (severity === "critical" || severity === "high") return "red";
  if (severity === "medium") return "yellow";
  if (severity === "low") return "green";
  return "neutral";
}

function pipelineTone(value?: string): SignalTone {
  if (!value) return "neutral";
  if (value.includes("enabled") || value.includes("configured") || value === "active") return "green";
  if (value.includes("blocked") || value.includes("disabled") || value.includes("placeholder")) return "yellow";
  return "neutral";
}

function sunatTone(status?: string): SignalTone {
  if (status === "CONNECTED") return "green";
  if (status === "ERROR") return "red";
  if (status === "CONNECTING" || status === "NOT_CONNECTED") return "yellow";
  return "neutral";
}

function compactStatus(value?: string | boolean | null) {
  if (typeof value === "boolean") return value ? "Activo" : "Inactivo";
  if (!value) return "Pendiente";
  return value.replace(/_/g, " ");
}

function formatNumber(value: number | undefined) {
  return new Intl.NumberFormat("es-PE").format(value ?? 0);
}

function recordDate(value?: string) {
  if (!value) return "Sin fecha";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-PE", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }).format(date);
}

function featureLabel(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter: string) => letter.toUpperCase());
}

function realCount(value: number | undefined, authorized: boolean) {
  return authorized ? formatNumber(value ?? 0) : "Bloqueado";
}

function isTaxSignal(record: OperationalRecord | DocumentRecord) {
  const metadata = "metadata" in record ? record.metadata : undefined;
  const documentType = "document_type" in record ? record.document_type : undefined;
  const haystack = [
    record.category,
    record.title,
    record.source,
    documentType,
    metadata?.filename,
    record.details ? Object.values(record.details).join(" ") : ""
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return ["tax", "sunat", "tribut", "impuesto", "factura", "invoice", "esquela"].some((term) => haystack.includes(term));
}

function isFinancialSignal(record: OperationalRecord | DocumentRecord) {
  const metadata = "metadata" in record ? record.metadata : undefined;
  const documentType = "document_type" in record ? record.document_type : undefined;
  const haystack = [
    record.category,
    record.title,
    record.source,
    documentType,
    metadata?.filename,
    record.details ? Object.values(record.details).join(" ") : ""
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return ["financial", "financ", "balance", "estado", "liquidez", "cash", "banco"].some((term) => haystack.includes(term));
}

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <img src="/dcft-icon.svg" alt="" />
    </span>
  );
}

function StatusPill({ tone, children }: { tone: SignalTone; children: ReactNode }) {
  return <span className={`status-pill ${tone}`}>{children}</span>;
}

function SectionHeader({
  eyebrow,
  title,
  action,
  children
}: {
  eyebrow: string;
  title: string;
  action?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className="section-header">
      <div>
        <span className="overline">{eyebrow}</span>
        <h2>{title}</h2>
        {children ? <p>{children}</p> : null}
      </div>
      {action ? <div className="section-action">{action}</div> : null}
    </div>
  );
}

function MetricTile({
  label,
  value,
  tone,
  icon,
  detail
}: {
  label: string;
  value: string;
  tone: SignalTone;
  icon: ReactNode;
  detail?: string;
}) {
  return (
    <article className={`metric-tile ${tone}`}>
      <span className="metric-icon">{icon}</span>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        {detail ? <small>{detail}</small> : null}
      </div>
    </article>
  );
}

function InfoCard({
  icon,
  eyebrow,
  title,
  detail,
  tone,
  meta
}: {
  icon: ReactNode;
  eyebrow: string;
  title: string;
  detail: string;
  tone: SignalTone;
  meta?: string;
}) {
  return (
    <article className={`info-card ${tone}`}>
      <div className="info-card__top">
        <span className="card-icon">{icon}</span>
        <StatusPill tone={tone}>{toneLabel(tone)}</StatusPill>
      </div>
      <span className="overline">{eyebrow}</span>
      <h3>{title}</h3>
      <p>{detail}</p>
      {meta ? <small>{meta}</small> : null}
    </article>
  );
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty-state">
      <CheckCircle2 size={18} />
      <div>
        <strong>{title}</strong>
        <span>{text}</span>
      </div>
    </div>
  );
}

function DocumentEvidenceList({
  documents,
  ingestions,
  authorized
}: {
  documents: DocumentRecord[];
  ingestions: DocumentRecord[];
  authorized: boolean;
}) {
  if (!authorized) {
    return <EmptyState title="Workspace protegido" text="Inicia sesion para ver evidencia documental del tenant." />;
  }
  if (!documents.length) {
    return <EmptyState title="Sin documentos cargados" text="No existen documentos reales registrados para este workspace." />;
  }
  const ingestionByDocument = new Map(ingestions.map((ingestion) => [ingestion.document_id, ingestion]));
  return (
    <div className="document-list">
      {documents.slice(0, 4).map((document) => {
        const ingestion = ingestionByDocument.get(document.id);
        const filename = document.metadata?.filename || document.title || "Documento registrado";
        return (
          <article className="document-row" key={document.id}>
            <span className="document-row__icon"><FileText size={18} /></span>
            <div>
              <h3>{filename}</h3>
              <p>{compactStatus(document.document_type)} / OCR {compactStatus(ingestion?.ocr_status || ingestion?.status)}</p>
            </div>
            <span>{recordDate(document.timestamp)}</span>
          </article>
        );
      })}
    </div>
  );
}

function RecordList({
  records,
  kind,
  emptyText
}: {
  records: OperationalRecord[];
  kind: "alert" | "recommendation";
  emptyText: string;
}) {
  if (!records.length) {
    return <EmptyState title="Sin registros activos" text={emptyText} />;
  }
  return (
    <div className="record-list">
      {records.slice(0, 5).map((record) => {
        const tone = kind === "alert" ? severityTone(record.severity) : "green";
        const title = kind === "alert" ? record.title || "Alerta registrada" : record.objective || "Recomendacion registrada";
        const body = kind === "alert"
          ? record.source || record.status
          : record.recommendation || record.explainability?.recommendation || "Revision lista para validar.";
        return (
          <article className="record-row" key={record.id}>
            <div>
              <StatusPill tone={tone}>{kind === "alert" ? record.severity || record.status : record.category || record.status}</StatusPill>
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
            <span>{recordDate(record.timestamp)}</span>
          </article>
        );
      })}
    </div>
  );
}

function GovernanceList({ records }: { records: GovernanceRequest[] }) {
  if (!records.length) {
    return <EmptyState title="Sin aprobaciones pendientes" text="No hay acciones sensibles bloqueadas en este tenant." />;
  }
  return (
    <div className="governance-list">
      {records.slice(0, 5).map((record) => (
        <article className="governance-row" key={record.id}>
          <div>
            <StatusPill tone={severityTone(record.risk)}>{record.status}</StatusPill>
            <h3>{record.scope}</h3>
            <p>{record.action}</p>
          </div>
          <span>{recordDate(record.timestamp)}</span>
        </article>
      ))}
    </div>
  );
}

function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem("dcft_token") || "");
  const [health, setHealth] = useState<Health | null>(null);
  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatus | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeContext, setActiveContext] = useState<ActiveContext | null>(null);
  const [permissions, setPermissions] = useState<PermissionMatrix | null>(null);
  const [sunatStatus, setSunatStatus] = useState<SunatStatus | null>(null);
  const [onboardingProgress, setOnboardingProgress] = useState<OnboardingProgress | null>(null);
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [plans, setPlans] = useState<PlanDefinition[]>([]);
  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [alerts, setAlerts] = useState<OperationalRecord[]>([]);
  const [recommendations, setRecommendations] = useState<OperationalRecord[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [documentIngestions, setDocumentIngestions] = useState<DocumentRecord[]>([]);
  const [governance, setGovernance] = useState<GovernanceRequest[]>([]);
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [onboardingForm, setOnboardingForm] = useState({
    tenant_name: "",
    tenant_id: "",
    admin_username: "",
    admin_password: "",
    plan: "mype",
    account_type: "business",
    ruc: "",
    razon_social: "",
    nombre_comercial: "",
    regimen_tributario: "mype_tributario",
    trial_requested: true
  });
  const [sunatAuxForm, setSunatAuxForm] = useState({
    ruc: "",
    auxiliary_user_alias: ""
  });
  const [activePanel, setActivePanel] = useState<PanelKey | null>(null);

  const authorized = token.length > 0;

  const logout = useCallback((reason = "session closed") => {
    const activeToken = localStorage.getItem("dcft_token");
    if (activeToken) {
      post("/auth/logout", {}, activeToken).catch(() => undefined);
    }
    localStorage.removeItem("dcft_token");
    setToken("");
    setCurrentUser(null);
    setSummary(null);
    setAnalytics(null);
    setAlerts([]);
    setRecommendations([]);
    setDocuments([]);
    setDocumentIngestions([]);
    setGovernance([]);
    setAudit(null);
    setCompanies([]);
    setWorkspaces([]);
    setActiveContext(null);
    setPermissions(null);
    setSunatStatus(null);
    setOnboardingProgress(null);
    setAdminUsers([]);
    setError(reason === "session closed" ? "" : reason);
  }, []);

  const handleError = useCallback((err: unknown, fallback: string) => {
    if (err instanceof ApiError) {
      if (err.status === 401) {
        logout("Sesion expirada. Ingresa nuevamente.");
        return "Sesion expirada. Ingresa nuevamente.";
      }
      if (err.status === 403) return "Permiso denegado por seguridad operacional.";
      if (err.status === 429) return "Limite de uso activo. Intenta nuevamente en unos minutos.";
      if (err.status === 0) return `${err.message}. Runtime degradado.`;
      return `${err.status}: ${err.message}`;
    }
    return err instanceof Error ? err.message : fallback;
  }, [logout]);

  const optionalSecureRequest = useCallback(async <T,>(path: string, fallback: T, activeToken: string): Promise<T> => {
    try {
      return await request<T>(path, {}, activeToken);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) throw err;
      return fallback;
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [healthBody, onboardingBody, planBody, runtimeBody] = await Promise.all([
        request<Health>("/health"),
        request<OnboardingStatus>("/onboarding/status"),
        request<PlanDefinition[]>("/subscriptions/plans"),
        request<RuntimeStatus>("/runtime/status")
      ]);
      setHealth(healthBody);
      setOnboardingStatus(onboardingBody);
      setPlans(planBody);
      setRuntimeStatus(runtimeBody);

      if (token) {
        const [
          me,
          dashboard,
          analyticsBody,
          alertsBody,
          recommendationsBody,
          documentsBody,
          ingestionsBody,
          governanceBody,
          auditBody,
          companyBody,
          workspaceBody,
          contextBody,
          permissionBody,
          sunatBody,
          onboardingProgressBody,
          adminBody
        ] = await Promise.all([
          request<CurrentUser>("/auth/me", {}, token),
          request<Summary>("/dashboard/summary", {}, token),
          optionalSecureRequest<AnalyticsSummary | null>("/analytics/summary", null, token),
          optionalSecureRequest<OperationalRecord[]>("/alerts?limit=6", [], token),
          optionalSecureRequest<OperationalRecord[]>("/recommendations?limit=6", [], token),
          optionalSecureRequest<DocumentRecord[]>("/documents?limit=6", [], token),
          optionalSecureRequest<DocumentRecord[]>("/documents/ingestions?limit=6", [], token),
          optionalSecureRequest<GovernanceRequest[]>("/governance/approval-requests?limit=6", [], token),
          optionalSecureRequest<AuditResponse | null>("/audit/events?limit=6", null, token),
          optionalSecureRequest<Company[]>("/identity/companies", [], token),
          optionalSecureRequest<Workspace[]>("/identity/workspaces", [], token),
          optionalSecureRequest<ActiveContext | null>("/identity/context", null, token),
          optionalSecureRequest<PermissionMatrix | null>("/identity/permissions", null, token),
          optionalSecureRequest<SunatStatus | null>("/sunat/status", null, token),
          optionalSecureRequest<OnboardingProgress | null>("/onboarding/progress", null, token),
          optionalSecureRequest<AdminUsersResponse | null>("/admin/ceo/users", null, token)
        ]);
        setCurrentUser(me);
        setSummary(dashboard);
        setAnalytics(analyticsBody);
        setAlerts(alertsBody);
        setRecommendations(recommendationsBody);
        setDocuments(documentsBody);
        setDocumentIngestions(ingestionsBody);
        setGovernance(governanceBody);
        setAudit(auditBody);
        setCompanies(companyBody);
        setWorkspaces(workspaceBody);
        setActiveContext(contextBody);
        setPermissions(permissionBody);
        setSunatStatus(sunatBody);
        setOnboardingProgress(onboardingProgressBody);
        setAdminUsers(adminBody?.users || []);
      } else {
        setCurrentUser(null);
        setSummary(null);
        setAnalytics(null);
        setAlerts([]);
        setRecommendations([]);
        setDocuments([]);
        setDocumentIngestions([]);
        setGovernance([]);
        setAudit(null);
        setCompanies([]);
        setWorkspaces([]);
        setActiveContext(null);
        setPermissions(null);
        setSunatStatus(null);
        setOnboardingProgress(null);
        setAdminUsers([]);
      }
    } catch (err) {
      setError(handleError(err, "No se pudo actualizar DCFT."));
    } finally {
      setLoading(false);
    }
  }, [handleError, optionalSecureRequest, token]);

  const login = async (event?: FormEvent) => {
    event?.preventDefault();
    setLoading(true);
    setError("");
    try {
      const session = await post<Session>("/auth/login", { username, password });
      setToken(session.access_token);
      localStorage.setItem("dcft_token", session.access_token);
      setPassword("");
    } catch (err) {
      setError(handleError(err, "No se pudo iniciar sesion."));
    } finally {
      setLoading(false);
    }
  };

  const createTenant = async (event?: FormEvent) => {
    event?.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = {
        ...onboardingForm,
        tenant_id: onboardingForm.tenant_id.trim() || undefined,
        ruc: onboardingForm.ruc.trim() || undefined,
        razon_social: onboardingForm.razon_social.trim() || onboardingForm.tenant_name.trim(),
        nombre_comercial: onboardingForm.nombre_comercial.trim(),
        admin_username: onboardingForm.admin_username.trim(),
        tenant_name: onboardingForm.tenant_name.trim()
      };
      const result = await post<OnboardingResult>("/onboarding/tenants", payload);
      setToken(result.access_token);
      setUsername(result.admin_username);
      setPassword("");
      localStorage.setItem("dcft_token", result.access_token);
    } catch (err) {
      setError(handleError(err, "No se pudo crear el workspace."));
    } finally {
      setLoading(false);
    }
  };

  const selectCompany = async (companyId: string) => {
    if (!companyId || !token) return;
    setLoading(true);
    setError("");
    try {
      const context = await post<ActiveContext>("/identity/context/company", { company_id: companyId }, token);
      setActiveContext(context);
      await refresh();
    } catch (err) {
      setError(handleError(err, "No se pudo seleccionar la empresa."));
    } finally {
      setLoading(false);
    }
  };

  const selectWorkspace = async (workspaceId: string) => {
    if (!workspaceId || !token) return;
    setLoading(true);
    setError("");
    try {
      const context = await post<ActiveContext>("/identity/context/workspace", { workspace_id: workspaceId }, token);
      setActiveContext(context);
      await refresh();
    } catch (err) {
      setError(handleError(err, "No se pudo seleccionar el workspace."));
    } finally {
      setLoading(false);
    }
  };

  const markVideoSeen = async (videoId: string) => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const progress = await post<OnboardingProgress>(`/onboarding/videos/${videoId}/seen`, {}, token);
      setOnboardingProgress(progress);
      await refresh();
    } catch (err) {
      setError(handleError(err, "No se pudo marcar el video."));
    } finally {
      setLoading(false);
    }
  };

  const prepareSunatAuxiliary = async (event?: FormEvent) => {
    event?.preventDefault();
    if (!token || !activeCompany || !activeWorkspace) return;
    setLoading(true);
    setError("");
    try {
      await post(
        "/sunat/auxiliary-access/prepare",
        {
          empresa_id: activeCompany.id,
          workspace_id: activeWorkspace.id,
          ruc: sunatAuxForm.ruc.trim() || activeCompany.ruc,
          auxiliary_user_alias: sunatAuxForm.auxiliary_user_alias.trim()
        },
        token
      );
      setSunatAuxForm({ ruc: activeCompany.ruc, auxiliary_user_alias: sunatAuxForm.auxiliary_user_alias.trim() });
      await refresh();
    } catch (err) {
      setError(handleError(err, "No se pudo preparar el usuario SUNAT auxiliar."));
    } finally {
      setLoading(false);
    }
  };

  const setAdminTrial = async (userId: string, active: boolean) => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      await post(`/admin/ceo/users/${userId}/trial`, { active, days: 7 }, token);
      await refresh();
    } catch (err) {
      setError(handleError(err, "No se pudo actualizar el trial."));
    } finally {
      setLoading(false);
    }
  };

  const setAdminPlan = async (userId: string, plan: string) => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      await patch(`/admin/ceo/users/${userId}/plan`, { plan }, token);
      await refresh();
    } catch (err) {
      setError(handleError(err, "No se pudo cambiar el plan."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [refresh]);

  const runtime = runtimeStatus || summary?.runtime || null;
  const backendOk = health?.status === "ok" && runtime?.busy_loop === false;
  const planName = summary?.plan.name || currentUser?.plan || "Sin sesion";
  const plansToRender = plans.length ? plans : onboardingStatus?.plans || [];
  const activePlanId = summary?.plan.id || currentUser?.plan || onboardingForm.plan;
  const trialActive = Boolean(summary?.trial?.active || onboardingProgress?.trial?.active);
  const trialExpired = Boolean(summary?.trial?.expired || onboardingProgress?.trial?.expired);
  const trialDaysRemaining = summary?.trial?.days_remaining ?? onboardingProgress?.trial?.days_remaining ?? 0;
  const effectivePlanId = summary?.trial?.plan_effective || onboardingProgress?.plan_effective || activePlanId;
  const basePlanId = summary?.trial?.plan_base || onboardingProgress?.plan_base || activePlanId;

  const openAlerts = summary?.counts.open_alerts ?? alerts.filter((alert) => alert.status === "open").length;
  const overLimitCount = Object.keys(summary?.usage?.over_limit || {}).length;
  const documentCount = summary?.counts.documents ?? documents.length;
  const recommendationCount = summary?.counts.recommendations ?? recommendations.length;
  const auditCount = summary?.counts.audit_events ?? runtime?.audit_events;
  const taxEvidenceCount = alerts.filter(isTaxSignal).length + recommendations.filter(isTaxSignal).length + documents.filter(isTaxSignal).length;
  const financialEvidenceCount = recommendations.filter(isFinancialSignal).length + documents.filter(isFinancialSignal).length;

  const signal = useMemo(() => {
    const failures = analytics?.failures_total ?? 0;
    if (!authorized || !summary) return "neutral" as SignalTone;
    if (openAlerts > 2 || overLimitCount > 0 || failures > 0 || runtime?.busy_loop) return "red" as SignalTone;
    if (openAlerts > 0 || documentCount === 0) return "yellow" as SignalTone;
    return "green" as SignalTone;
  }, [analytics, authorized, documentCount, openAlerts, overLimitCount, runtime, summary]);

  const taxTone: SignalTone = !authorized ? "neutral" : openAlerts > 2 ? "red" : openAlerts > 0 ? "yellow" : taxEvidenceCount > 0 ? "green" : "yellow";
  const financeTone: SignalTone = !authorized ? "neutral" : overLimitCount > 0 ? "red" : financialEvidenceCount > 0 ? "green" : "yellow";
  const accountingTone: SignalTone = !authorized ? "neutral" : documentCount > 0 ? "green" : "yellow";
  const recommendationTone: SignalTone = !authorized ? "neutral" : recommendationCount > 0 ? "green" : "neutral";
  const auditTone: SignalTone = !authorized ? "neutral" : (auditCount ?? 0) > 0 ? "green" : "yellow";
  const databaseTone: SignalTone = runtime?.database?.status === "ok" ? "green" : "yellow";
  const aiTone = pipelineTone(runtime?.ai_pipeline);
  const ocrTone = pipelineTone(runtime?.ocr_pipeline);
  const currentSunatTone = sunatTone(sunatStatus?.status);

  const activeCompany = companies.find((company) => company.id === activeContext?.active_company_id) || companies[0] || null;
  const activeWorkspace = workspaces.find((workspace) => workspace.id === activeContext?.active_workspace_id) || workspaces[0] || null;
  const canPrepareSunatAux = Boolean(authorized && activeCompany && activeWorkspace && (sunatAuxForm.auxiliary_user_alias.trim().length >= 3));
  const rolePermissions = currentUser?.role && permissions?.roles[currentUser.role] ? permissions.roles[currentUser.role] : currentUser?.permissions || [];
  const onboardingPlan = plansToRender.find((plan) => plan.id === onboardingForm.plan);
  const onboardingRequiresRuc = Boolean(onboardingPlan?.requires_ruc || ["mype", "premium", "business_basic", "business_premium"].includes(onboardingForm.plan));
  const canCreateTenant = Boolean(
    onboardingStatus?.signup_enabled
    && onboardingForm.tenant_name.trim().length >= 2
    && onboardingForm.admin_username.trim()
    && onboardingForm.admin_password.length >= 10
    && (!onboardingRequiresRuc || onboardingForm.ruc.trim().length >= 8)
  );

  const operationalCards = [
    {
      icon: <Scale size={22} />,
      eyebrow: "Tributario",
      title: openAlerts > 0 ? "Revision requerida" : "Sin alerta critica",
      detail: authorized ? `${formatNumber(openAlerts)} alertas abiertas y ${formatNumber(taxEvidenceCount)} senales tributarias.` : "Lectura privada pendiente de sesion.",
      tone: taxTone,
      meta: "Alertas, documentos y recomendaciones"
    },
    {
      icon: <WalletCards size={22} />,
      eyebrow: "Financiero",
      title: overLimitCount > 0 ? "Limites excedidos" : "Uso bajo control",
      detail: authorized ? `${formatNumber(overLimitCount)} limites excedidos y ${formatNumber(financialEvidenceCount)} senales financieras.` : "Uso de plan protegido.",
      tone: financeTone,
      meta: "Plan, usage y documentos"
    },
    {
      icon: <FileCheck2 size={22} />,
      eyebrow: "Contable",
      title: documentCount > 0 ? "Evidencia documental" : "Sin documentos",
      detail: authorized ? `${formatNumber(documentCount)} documentos registrados. OCR ${compactStatus(runtime?.ocr_pipeline)}.` : "Documentos visibles al autenticar.",
      tone: accountingTone,
      meta: "Metadata y OCR"
    },
    {
      icon: <Landmark size={22} />,
      eyebrow: "SUNAT",
      title: compactStatus(sunatStatus?.status || "NOT_CONNECTED"),
      detail: authorized ? `Foundation ${sunatStatus?.foundation_only ? "activa" : "pendiente"}; conector real ${sunatStatus?.real_connector_enabled ? "activo" : "off"}.` : "Estado SUNAT protegido.",
      tone: currentSunatTone,
      meta: "Clave SOL auxiliar"
    }
  ];

  const businessScore = authorized
    ? Math.max(48, Math.min(96, 82 - openAlerts * 5 - overLimitCount * 8 + Math.min(documentCount, 4) * 2 + Math.min(recommendationCount, 3)))
    : 82;
  const businessScoreTone: SignalTone = businessScore >= 78 ? "green" : businessScore >= 62 ? "yellow" : "red";
  const scoreTrend = [60, 68, 75, businessScore];
  const primaryAlertTitle = financeTone === "red" || financeTone === "yellow" ? "Atencion Financiera" : openAlerts > 0 ? "Atencion Tributaria" : "Vigilancia Preventiva";
  const primaryAlertText = authorized && alerts[0]?.title
    ? `${alerts[0].title}. ${alerts[0].source || "Revisa la recomendacion para prevenir riesgos futuros."}`
    : "Hemos detectado senales que merecen revision para prevenir riesgos futuros.";
  const businessSignals = [
    {
      label: "Tributaria",
      tone: taxTone,
      icon: <ShieldCheck size={26} />,
      detail: authorized ? `${formatNumber(taxEvidenceCount)} senales revisadas` : "Proteccion preventiva"
    },
    {
      label: "Financiera",
      tone: financeTone,
      icon: <WalletCards size={26} />,
      detail: authorized ? `${formatNumber(overLimitCount)} limites en vigilancia` : "Liquidez y uso"
    },
    {
      label: "Contable",
      tone: accountingTone,
      icon: <FileCheck2 size={26} />,
      detail: authorized ? `${formatNumber(documentCount)} documentos` : "Evidencia y orden"
    }
  ];
  const lockedModules = [
    {
      title: "Medico de Cabecera Empresarial",
      text: "Recibe cada manana un diagnostico automatico de tu empresa sin necesidad de preguntar.",
      plan: "Premium"
    },
    {
      title: "Auditoria Integral",
      text: "Detecta riesgos contables, financieros y tributarios antes de que se conviertan en problemas.",
      plan: "Premium"
    }
  ];
  const accessPlans = plansToRender.length
    ? plansToRender
    : [
      {
        id: "student",
        name: "Estudiante",
        features: ["consultas limitadas", "biblioteca", "casos practicos", "premium visible bloqueado"],
        limits: { consultas: 10, reportes: 0 },
        trial_days: 7,
        requires_ruc: false
      },
      {
        id: "mype",
        name: "MYPE",
        features: ["vigilancia basica", "semaforos", "alertas basicas", "chat limitado"],
        limits: { precio_soles: 89, empresas: 1 },
        trial_days: 7,
        requires_ruc: true
      },
      {
        id: "premium",
        name: "Premium",
        features: ["vigilancia completa", "medico de cabecera", "auditoria inteligente", "chat avanzado"],
        limits: { precio_soles: 199, empresas: 3 },
        trial_days: 7,
        requires_ruc: true
      }
    ];

  const panelTitles: Record<PanelKey, string> = {
    diagnostico: "Diagnostico empresarial",
    reportes: "Reportes y evidencia",
    doctor: "Medico de Cabecera",
    perfil: "Perfil y acceso",
    premium: "Premium trial",
    onboarding: "Onboarding",
    sunat: "SUNAT auxiliar",
    empresa: "Empresa y workspace",
    admin: "Admin CEO"
  };

  const quickActions: Array<{ panel: PanelKey; label: string; detail: string; icon: ReactNode }> = [
    { panel: "doctor", label: "Doctor", detail: "Consulta ejecutiva", icon: <Stethoscope size={19} /> },
    { panel: "premium", label: "Premium", detail: "Trial y modulos", icon: <Lock size={19} /> },
    { panel: "empresa", label: "Empresa", detail: "Workspace activo", icon: <Building2 size={19} /> },
    { panel: "sunat", label: "SUNAT", detail: "Acceso auxiliar", icon: <Landmark size={19} /> },
    { panel: "onboarding", label: "Onboarding", detail: "Videos y alta", icon: <CheckCircle2 size={19} /> }
  ];

  const onboardingVideos = onboardingProgress?.videos || [
    { id: "sunat_auxiliary_user", title: "Como crear usuario secundario / auxiliar SUNAT", description: "Antes de conectar tu empresa, mira este video de 2 minutos para crear un acceso seguro de consulta.", placeholder: true, duration_hint: "2 minutos", seen: false, button_label: "Marcar como visto" },
    { id: "connect_company", title: "Como conectar tu empresa a DCFT", description: "Prepara RUC, razon social y workspace.", placeholder: true, duration_hint: "2 minutos", seen: false, button_label: "Marcar como visto" },
    { id: "interpret_diagnosis", title: "Como interpretar tu diagnostico empresarial", description: "Lee alertas, semaforo empresarial y prioridades.", placeholder: true, duration_hint: "2 minutos", seen: false, button_label: "Marcar como visto" }
  ];

  const openPanel = (panel: PanelKey) => setActivePanel(panel);
  const closePanel = () => setActivePanel(null);
  const publicError = error && (error.toLowerCase().includes("backend") || error.toLowerCase().includes("runtime") || error.toLowerCase().includes("api"))
    ? "No pudimos actualizar los datos ahora. Tu cabina sigue disponible; vuelve a intentarlo en unos segundos."
    : error;

  const renderAccessForm = () => (
    <form className="mini-login" onSubmit={login}>
      <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label="Usuario" placeholder="Usuario" autoComplete="username" />
      <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" aria-label="Clave" placeholder="Clave" autoComplete="current-password" />
      <button className="primary-button" type="submit" disabled={loading || !username || !password}>
        <Lock size={16} />
        Entrar
      </button>
    </form>
  );

  const renderOnboardingForm = () => (
    <form className="onboarding-form" onSubmit={createTenant}>
      <input value={onboardingForm.tenant_name} onChange={(event) => setOnboardingForm({ ...onboardingForm, tenant_name: event.target.value })} aria-label="Empresa" placeholder="Nombre de empresa" disabled={loading || authorized} autoComplete="organization" />
      <input value={onboardingForm.tenant_id} onChange={(event) => setOnboardingForm({ ...onboardingForm, tenant_id: event.target.value })} aria-label="Identificador opcional" placeholder="ID opcional" disabled={loading || authorized} autoComplete="off" />
      <input value={onboardingForm.admin_username} onChange={(event) => setOnboardingForm({ ...onboardingForm, admin_username: event.target.value })} aria-label="Administrador" placeholder="Administrador" disabled={loading || authorized} autoComplete="username" />
      <input value={onboardingForm.admin_password} onChange={(event) => setOnboardingForm({ ...onboardingForm, admin_password: event.target.value })} type="password" aria-label="Clave inicial" placeholder="Clave inicial" disabled={loading || authorized} autoComplete="new-password" />
      <select value={onboardingForm.account_type} onChange={(event) => setOnboardingForm({ ...onboardingForm, account_type: event.target.value, plan: event.target.value === "student" ? "student" : onboardingForm.plan === "student" ? "mype" : onboardingForm.plan })} aria-label="Tipo de cuenta" disabled={loading || authorized}>
        <option value="student">Estudiante / sin RUC</option>
        <option value="business">Empresa / con RUC</option>
      </select>
      <select value={onboardingForm.plan} onChange={(event) => setOnboardingForm({ ...onboardingForm, plan: event.target.value, account_type: event.target.value === "student" ? "student" : "business" })} aria-label="Plan" disabled={loading || authorized}>
        {accessPlans.map((plan) => (
          <option key={plan.id} value={plan.id}>{plan.name}</option>
        ))}
      </select>
      {onboardingForm.account_type === "business" || onboardingRequiresRuc ? (
        <>
          <input value={onboardingForm.ruc} onChange={(event) => setOnboardingForm({ ...onboardingForm, ruc: event.target.value })} aria-label="RUC" placeholder="RUC de la empresa" disabled={loading || authorized} inputMode="numeric" />
          <input value={onboardingForm.razon_social} onChange={(event) => setOnboardingForm({ ...onboardingForm, razon_social: event.target.value })} aria-label="Razon social" placeholder="Razon social" disabled={loading || authorized} autoComplete="organization" />
          <input value={onboardingForm.nombre_comercial} onChange={(event) => setOnboardingForm({ ...onboardingForm, nombre_comercial: event.target.value })} aria-label="Nombre comercial" placeholder="Nombre comercial opcional" disabled={loading || authorized} autoComplete="organization-title" />
        </>
      ) : null}
      <label className="checkbox-line">
        <input type="checkbox" checked={onboardingForm.trial_requested} onChange={(event) => setOnboardingForm({ ...onboardingForm, trial_requested: event.target.checked })} disabled={loading || authorized} />
        Activar trial inicial de 7 dias
      </label>
      <button className="primary-button" type="submit" disabled={loading || authorized || !canCreateTenant}>
        <UserPlus size={17} />
        Crear workspace
        <ArrowRight size={17} />
      </button>
    </form>
  );

  const renderPanelContent = () => {
    if (activePanel === "diagnostico") {
      return (
        <div className="drawer-stack">
          <div className="drawer-grid">
            {operationalCards.map((card) => (
              <InfoCard key={card.eyebrow} {...card} />
            ))}
          </div>
          <RecordList records={alerts} kind="alert" emptyText="No existen alertas abiertas en este workspace." />
          <RecordList records={recommendations} kind="recommendation" emptyText="No existen recomendaciones registradas para este tenant." />
        </div>
      );
    }

    if (activePanel === "reportes") {
      return (
        <div className="drawer-stack">
          <DocumentEvidenceList documents={documents} ingestions={documentIngestions} authorized={authorized} />
          <GovernanceList records={governance} />
          <div className="audit-strip">
            <span>Integridad</span>
            <strong>{audit?.integrity?.tamper_detected ? "Revisar" : "Visible"}</strong>
            <small>{formatNumber(audit?.integrity?.checked_events)} eventos verificados</small>
          </div>
        </div>
      );
    }

    if (activePanel === "doctor") {
      return (
        <div className="drawer-stack">
          <section className="doctor-card compact-panel-card">
            <div className="doctor-portrait" aria-hidden="true">
              <span>Dr.</span>
            </div>
            <div>
              <span>Medico de Cabecera Empresarial</span>
              <h2>Dr. DCFT</h2>
              <p>Vigilancia preventiva para cuidar la salud financiera, contable y tributaria de tu empresa.</p>
              <div className="daily-diagnosis">
                <strong>Diagnostico diario preparado</strong>
                <small>Tributaria: {businessStatusLabel(taxTone)} / financiera: {businessStatusLabel(financeTone)} / contable: {businessStatusLabel(accountingTone)}</small>
              </div>
            </div>
          </section>
          <RecordList records={recommendations} kind="recommendation" emptyText="El Doctor no tiene recomendaciones pendientes para este workspace." />
        </div>
      );
    }

    if (activePanel === "premium") {
      return (
        <div className="drawer-stack">
          {authorized ? (
            <section className={`trial-banner ${trialExpired ? "expired" : trialActive ? "active" : ""}`}>
              <span>{trialActive ? "Premium de prueba" : trialExpired ? "Trial vencido" : "Trial inactivo"}</span>
              <strong>{trialActive ? `${trialDaysRemaining} dias restantes` : `Plan base ${featureLabel(basePlanId)}`}</strong>
              <small>Plan efectivo: {featureLabel(effectivePlanId)}. Los datos se conservan aunque el trial venza.</small>
            </section>
          ) : null}
          <div className="locked-grid">
            {lockedModules.map((module) => (
              <article className="locked-card" key={module.title}>
                <Lock size={18} />
                <strong>{module.title}</strong>
                <p>{module.text}</p>
                <span>Disponible en {module.plan}</span>
                <button className="alert-button" type="button" onClick={() => openPanel(authorized ? "admin" : "perfil")}>
                  Ver activacion
                  <ArrowRight size={16} />
                </button>
              </article>
            ))}
          </div>
          <div className="plans-preview">
            {accessPlans.map((plan) => (
              <article className={`plan-preview-card ${plan.id === effectivePlanId ? "active" : ""}`} key={plan.id}>
                <span>{plan.id === effectivePlanId ? "Plan efectivo" : "Plan disponible"}</span>
                <strong>{plan.name}</strong>
                <small>{plan.features.slice(0, 2).map(featureLabel).join(" / ")}</small>
                {plan.trial_days ? <small>Trial Premium {plan.trial_days} dias</small> : null}
              </article>
            ))}
          </div>
        </div>
      );
    }

    if (activePanel === "onboarding") {
      return (
        <div className="drawer-stack">
          <div className="human-copy-card">
            <strong>Alta guiada</strong>
            <p>Estudiante puede empezar sin RUC. MYPE y Premium requieren RUC para crear empresa y workspace.</p>
          </div>
          {renderOnboardingForm()}
          {onboardingProgress ? (
            <div className="checklist-grid" aria-label="Checklist de onboarding">
              {Object.entries(onboardingProgress.checklist).map(([key, value]) => (
                <span className={value ? "done" : "pending"} key={key}>
                  <CheckCircle2 size={15} />
                  {featureLabel(key)}
                </span>
              ))}
            </div>
          ) : null}
          <div className="video-slot-list" aria-label="Guias de onboarding">
            {onboardingVideos.map((video) => (
              <article className={`video-card ${video.seen ? "seen" : ""}`} key={video.id}>
                <span>{video.duration_hint}</span>
                <strong>{video.title}</strong>
                <p>{video.description}</p>
                <button className="secondary-link" type="button" disabled={!authorized || loading || video.seen} onClick={() => markVideoSeen(video.id)}>
                  {video.button_label}
                </button>
              </article>
            ))}
          </div>
        </div>
      );
    }

    if (activePanel === "sunat") {
      return (
        <div className="drawer-stack">
          <div className="human-copy-card">
            <strong>Acceso seguro de consulta</strong>
            <p>DCFT necesita acceso de consulta para realizar el diagnostico inicial. No realizara declaraciones, pagos ni modificaciones.</p>
          </div>
          <form className="sunat-prep-form" onSubmit={prepareSunatAuxiliary}>
            <input
              value={sunatAuxForm.ruc || activeCompany?.ruc || ""}
              onChange={(event) => setSunatAuxForm({ ...sunatAuxForm, ruc: event.target.value })}
              aria-label="RUC SUNAT auxiliar"
              placeholder="RUC"
              disabled={!authorized || !activeCompany || loading}
              inputMode="numeric"
            />
            <input
              value={sunatAuxForm.auxiliary_user_alias}
              onChange={(event) => setSunatAuxForm({ ...sunatAuxForm, auxiliary_user_alias: event.target.value })}
              aria-label="Usuario secundario SUNAT"
              placeholder="Usuario secundario SUNAT"
              disabled={!authorized || !activeCompany || loading}
              autoComplete="off"
            />
            <button className="secondary-link" type="button" disabled>
              Validar conexion pendiente
            </button>
            <button className="primary-button" type="submit" disabled={!canPrepareSunatAux || loading}>
              <ShieldCheck size={17} />
              Preparar usuario auxiliar
            </button>
            <small>Usa un usuario secundario o auxiliar con permisos controlados. No uses tu Clave SOL principal como flujo recomendado.</small>
          </form>
        </div>
      );
    }

    if (activePanel === "empresa") {
      return (
        <div className="drawer-stack">
          <div className="context-card">
            <span className="overline">Empresa activa</span>
            <select
              value={activeContext?.active_company_id || activeCompany?.id || ""}
              onChange={(event) => selectCompany(event.currentTarget.value)}
              disabled={!authorized || !companies.length || loading}
              aria-label="Empresa activa"
            >
              <option value="">{companies.length ? "Seleccionar empresa" : "Sin empresas"}</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>{company.razon_social}</option>
              ))}
            </select>
            <strong>{activeCompany?.razon_social || "Pendiente"}</strong>
            <small>{activeCompany ? `RUC ${activeCompany.ruc} / ${activeCompany.regimen_tributario}` : "Crea tu empresa desde Onboarding."}</small>
          </div>
          <div className="context-card">
            <span className="overline">Workspace activo</span>
            <select
              value={activeContext?.active_workspace_id || activeWorkspace?.id || ""}
              onChange={(event) => selectWorkspace(event.currentTarget.value)}
              disabled={!authorized || !workspaces.length || loading}
              aria-label="Workspace activo"
            >
              <option value="">{workspaces.length ? "Seleccionar workspace" : "Sin workspaces"}</option>
              {workspaces.map((workspace) => (
                <option key={workspace.id} value={workspace.id}>{workspace.nombre}</option>
              ))}
            </select>
            <strong>{activeWorkspace?.nombre || "Pendiente"}</strong>
            <small>{activeWorkspace ? `${activeWorkspace.estado} / plan ${activeWorkspace.plan_id}` : "Crea un workspace ligado a empresa."}</small>
          </div>
          <button className="primary-button" type="button" onClick={() => openPanel("onboarding")}>
            Crear empresa o workspace
            <ArrowRight size={16} />
          </button>
        </div>
      );
    }

    if (activePanel === "admin") {
      return (
        <div className="drawer-stack">
          <div className="human-copy-card">
            <strong>Panel protegido</strong>
            <p>Admin CEO permite activar trials, revisar usuarios y consultar el estado tecnico sin mostrarlo en la Home.</p>
          </div>
          {adminUsers.length ? (
            <div className="admin-user-grid">
              {adminUsers.slice(0, 8).map((user) => (
                <article className="admin-user-card" key={user.user_id}>
                  <div>
                    <span>{user.role}</span>
                    <h3>{user.username}</h3>
                    <p>{user.company?.razon_social || user.tenant_name} / {user.workspace?.nombre || "Sin workspace"}</p>
                  </div>
                  <div className="admin-user-meta">
                    <StatusPill tone={user.trial?.active ? "yellow" : "neutral"}>
                      {user.trial?.active ? "Premium de prueba" : "Trial inactivo"}
                    </StatusPill>
                    <small>Base {featureLabel(user.plan)} / efectivo {featureLabel(user.plan_effective)}</small>
                    <small>Onboarding {user.onboarding.ready_for_testing ? "listo" : "pendiente"}</small>
                  </div>
                  <div className="admin-actions">
                    <button className="primary-button" type="button" onClick={() => setAdminTrial(user.user_id, true)} disabled={loading}>
                      Activar 7 dias
                    </button>
                    <button className="secondary-link" type="button" onClick={() => setAdminTrial(user.user_id, false)} disabled={loading}>
                      Desactivar
                    </button>
                    <select value={user.plan} onChange={(event) => setAdminPlan(user.user_id, event.target.value)} disabled={loading} aria-label={`Plan de ${user.username}`}>
                      {accessPlans.map((plan) => (
                        <option value={plan.id} key={plan.id}>{plan.name}</option>
                      ))}
                    </select>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <Lock size={18} />
              <div>
                <strong>Acceso protegido</strong>
                <span>Inicia sesion con un usuario autorizado para operar Admin CEO.</span>
              </div>
            </div>
          )}
          <details className="technical-details">
            <summary>Estado tecnico</summary>
            <div className="runtime-grid">
              <InfoCard icon={<Activity size={22} />} eyebrow="Backend" title={health?.status || "checking"} detail={`DB ${compactStatus(runtime?.database?.backend)} / ${compactStatus(runtime?.database?.status)}`} tone={backendOk ? "green" : "yellow"} />
              <InfoCard icon={<Lock size={22} />} eyebrow="IA" title={compactStatus(runtime?.ai_pipeline)} detail="Estado gobernado por runtime." tone={aiTone} />
              <InfoCard icon={<ClipboardList size={22} />} eyebrow="OCR" title={compactStatus(runtime?.ocr_pipeline)} detail="Documentos con metadata verificable." tone={ocrTone} />
              <InfoCard icon={<Clock3 size={22} />} eyebrow="Observabilidad" title={`${formatNumber(runtime?.persistent_observability?.events_total)} eventos`} detail={`${runtime?.persistent_observability?.avg_latency_ms ?? 0} ms promedio.`} tone={databaseTone} />
            </div>
          </details>
        </div>
      );
    }

    return (
      <div className="drawer-stack">
        {authorized ? (
          <div className="session-summary">
            <strong>{currentUser?.username}</strong>
            <small>{currentUser?.role} / {planName}</small>
            <button className="secondary-link" onClick={() => logout()} disabled={loading} type="button">
              Cerrar sesion
            </button>
          </div>
        ) : (
          <>
            <div className="human-copy-card">
              <strong>Acceso seguro</strong>
              <p>Inicia sesion para ver tu empresa, workspace, plan y diagnostico real.</p>
            </div>
            {renderAccessForm()}
            <button className="secondary-link" type="button" onClick={() => openPanel("onboarding")}>
              Crear cuenta nueva
            </button>
          </>
        )}
      </div>
    );
  };

  return (
    <main className={`dcft-shell ${authorized ? "is-authorized" : "is-guest"}`}>
      <aside className="app-sidebar" aria-label="Navegacion principal">
        <a className="brand-lockup" href="#dashboard" aria-label="DCFT inicio">
          <BrandMark />
          <span className="brand-copy">
            <strong>{PRODUCT_NAME}</strong>
            <span>{PRODUCT_FULL_NAME}</span>
          </span>
        </a>

        <nav className="side-nav">
          {DESKTOP_NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return item.href ? (
              <a href={item.href} key={item.href}>
                <Icon size={18} />
                <span>{item.label}</span>
              </a>
            ) : (
              <button type="button" onClick={() => item.panel && openPanel(item.panel)} key={item.label}>
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-status">
          <span className="overline">Estado</span>
          <StatusPill tone={authorized ? "green" : "yellow"}>{authorized ? featureLabel(effectivePlanId) : "Acceso seguro"}</StatusPill>
          <small>{authorized ? currentUser?.username || "Sesion activa" : "Inicia sesion para datos reales"}</small>
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar" id="top">
          <div className="topbar-title">
            <BrandMark />
            <div>
              <span className="overline">{PRODUCT_TAGLINE}</span>
              <h1>{PRODUCT_NAME}</h1>
            </div>
          </div>

          <div className="topbar-actions" data-screen="login-mobile">
            <StatusPill tone={authorized ? "green" : "yellow"}>{authorized ? featureLabel(effectivePlanId) : "Entrar"}</StatusPill>
            <button className="icon-button" onClick={refresh} disabled={loading} title="Actualizar">
              <RefreshCcw size={18} />
            </button>
            <button className="icon-button notification-button" type="button" title="Notificaciones">
              <BellRing size={18} />
            </button>
            <button className="icon-button" type="button" onClick={() => openPanel("perfil")} title="Perfil">
              <UserCircle size={18} />
            </button>
            {authorized ? (
              <button className="icon-button" onClick={() => logout()} disabled={loading} title="Cerrar sesion">
                <LogOut size={18} />
              </button>
            ) : null}
          </div>
        </header>

        {loading ? (
          <div className="loading-strip" role="status">
            <span />
            Actualizando datos del backend...
          </div>
        ) : null}

        <section className="official-home" id="dashboard" data-screen="dashboard">
          <section className="brand-hero" aria-label="Identidad DCFT">
            <div className="brand-hero__seal">
              <BrandMark />
            </div>
            <span className="overline">{PRODUCT_FULL_NAME}</span>
            <h2>{PRODUCT_NAME}</h2>
            <p>{PRODUCT_TAGLINE}</p>
            <small>{PRODUCT_PROMISE}</small>
            <div className="trust-strip" aria-label="Promesa de DCFT">
              <span><ShieldCheck size={17} /> Proteccion</span>
              <span><Activity size={17} /> Vigilancia</span>
              <span><Stethoscope size={17} /> Diagnostico</span>
              <span><BadgeCheck size={17} /> Confianza</span>
            </div>
          </section>

          <section className="business-traffic" aria-label="Semaforo Empresarial">
            <div className="official-section-title">
              <span>Inicio</span>
              <h2>Semaforo Empresarial</h2>
            </div>
            <div className="traffic-card-grid">
              {businessSignals.map((signalItem) => (
                <article className={`traffic-card ${signalItem.tone}`} key={signalItem.label}>
                  <span className="traffic-icon">{signalItem.icon}</span>
                  <div>
                    <strong>{signalItem.label}</strong>
                    <StatusPill tone={signalItem.tone}>{businessStatusLabel(signalItem.tone)}</StatusPill>
                    <small>{signalItem.detail}</small>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className={`doctor-alert ${financeTone === "red" ? "red" : "yellow"}`} aria-label="Alerta del Doctor">
            <div className="alert-symbol">
              <AlertTriangle size={22} />
            </div>
            <div>
              <span>Alerta del Doctor</span>
              <h2>{primaryAlertTitle}</h2>
              <p>{primaryAlertText}</p>
              <button className="alert-button" type="button" onClick={() => openPanel("diagnostico")}>
                Ver recomendacion
                <ArrowRight size={17} />
              </button>
            </div>
          </section>

          <section className="health-card" id="diagnostic" data-screen="diagnostic" aria-label="Salud Empresarial">
            <div className="official-section-title">
              <span>Diagnostico</span>
              <h2>Salud Empresarial</h2>
            </div>
            <div className="health-card__body">
              <div className={`score-ring ${businessScoreTone}`} style={{ "--score": `${businessScore}%` } as CSSProperties}>
                <strong>{businessScore}</strong>
                <span>de 100</span>
              </div>
              <div className="health-summary">
                <strong>{businessScore >= 80 ? "Buena salud" : businessScore >= 62 ? "Salud en vigilancia" : "Requiere atencion"}</strong>
                <p>{businessScore >= 80 ? "Vas por buen camino." : "Hay senales que conviene revisar antes de que escalen."}</p>
                <div className="score-trend" aria-label="Evolucion de salud empresarial">
                  {scoreTrend.map((scoreValue, index) => (
                    <span key={`${scoreValue}-${index}`}>
                      <i style={{ height: `${Math.max(16, scoreValue / 1.6)}px` }} />
                      <small>{scoreValue}</small>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="quick-actions-panel" aria-label="Acciones rapidas">
            <div className="official-section-title">
              <span>Accesos</span>
              <h2>Acciones rapidas</h2>
            </div>
            <div className="quick-action-grid">
              {quickActions.map((action) => (
                <button className="quick-action-card" type="button" key={action.panel} onClick={() => openPanel(action.panel)}>
                  <span>{action.icon}</span>
                  <strong>{action.label}</strong>
                  <small>{action.detail}</small>
                </button>
              ))}
            </div>
          </section>

          <section className="doctor-card" id="doctor" data-screen="doctor" aria-label="Medico de Cabecera Empresarial">
            <div className="doctor-portrait" aria-hidden="true">
              <span>Dr.</span>
            </div>
            <div>
              <span>Medico de Cabecera Empresarial</span>
              <h2>Dr. DCFT</h2>
              <p>Estamos para cuidar la salud de tu empresa y acompanarte en cada decision importante.</p>
              <div className="daily-diagnosis">
                <strong>Diagnostico diario preparado</strong>
                <small>Estado tributario: {businessStatusLabel(taxTone)} / financiero: {businessStatusLabel(financeTone)} / contable: {businessStatusLabel(accountingTone)}</small>
              </div>
              <button className="primary-button" type="button" onClick={() => openPanel("doctor")}>
                Agendar consulta
                <ArrowRight size={17} />
              </button>
            </div>
          </section>

          <section className="premium-showcase" id="reports" data-screen="reports" aria-label="Modulos premium">
            <div className="official-section-title">
              <span>Valor premium</span>
              <h2>Modulos visibles</h2>
            </div>
            <div className="locked-grid">
              {lockedModules.map((module) => (
                <article className="locked-card" key={module.title}>
                  <Lock size={18} />
                  <strong>{module.title}</strong>
                  <p>{module.text}</p>
                  <span>Disponible en {module.plan}</span>
                </article>
              ))}
            </div>
          </section>

          <section className="access-card" id="profile" data-screen="profile" aria-label="Perfil y acceso">
            <div>
              <span>Perfil</span>
              <h2>{authorized ? currentUser?.username || "Usuario activo" : "Acceso seguro"}</h2>
              <p>{authorized ? `${currentUser?.role || "Rol"} / ${planName}` : "Inicia sesion para activar datos reales de empresa, workspace y permisos."}</p>
            </div>
            {!authorized ? (
              <form className="mini-login" onSubmit={login}>
                <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label="Usuario mobile" placeholder="Usuario" autoComplete="username" />
                <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" aria-label="Clave mobile" placeholder="Clave" autoComplete="current-password" />
                <button className="primary-button" type="submit" disabled={loading || !username || !password}>
                  <Lock size={16} />
                  Entrar
                </button>
                <a className="secondary-link" href="#onboarding">Crear cuenta</a>
              </form>
            ) : (
              <StatusPill tone="green">Sesion activa</StatusPill>
            )}
          </section>

          {authorized ? (
            <section className={`trial-banner ${trialExpired ? "expired" : trialActive ? "active" : ""}`} aria-label="Estado del trial">
              <span>{trialActive ? "Premium de prueba" : trialExpired ? "Trial vencido" : "Trial inactivo"}</span>
              <strong>{trialActive ? `${trialDaysRemaining} dias restantes` : `Plan base ${featureLabel(basePlanId)}`}</strong>
              <small>Plan efectivo: {featureLabel(effectivePlanId)}. Los datos se conservan aunque el trial venza.</small>
            </section>
          ) : null}

          <section className="plans-preview" aria-label="Niveles de acceso">
            {accessPlans.map((plan) => (
              <article className={`plan-preview-card ${plan.id === effectivePlanId ? "active" : ""}`} key={plan.id}>
                <span>{plan.id === effectivePlanId ? "Plan efectivo" : "Plan disponible"}</span>
                <strong>{plan.name}</strong>
                <small>{plan.features.slice(0, 2).map(featureLabel).join(" / ")}</small>
                {plan.trial_days ? <small>Trial Premium {plan.trial_days} dias</small> : null}
              </article>
            ))}
          </section>
        </section>

        <section className="executive-hero technical-zone" id="legacy-dashboard" data-screen="dashboard-legacy">
          <div className="hero-primary">
            <div className="hero-copy">
              <span className="overline">Dashboard ejecutivo</span>
              <h2>{summary?.tenant_id || currentUser?.tenant_id || "Workspace empresarial"}</h2>
              <p>{authorized ? "Lectura operativa del tenant activo." : "Acceso seguro para operar empresas, workspaces y gobierno tributario."}</p>
            </div>
            <div className="signal-panel">
              <span>Semaforo empresarial</span>
              <strong>{toneLabel(signal)}</strong>
              <StatusPill tone={signal}>{authorized ? "Datos reales" : "Sin sesion"}</StatusPill>
            </div>
          </div>

          <div className="context-rail">
            <article className="context-card">
              <span className="overline">Empresa activa</span>
              <select
                value={activeContext?.active_company_id || activeCompany?.id || ""}
                onChange={(event) => selectCompany(event.currentTarget.value)}
                disabled={!authorized || !companies.length || loading}
                aria-label="Empresa activa"
              >
                <option value="">{companies.length ? "Seleccionar empresa" : "Sin empresas"}</option>
                {companies.map((company) => (
                  <option key={company.id} value={company.id}>{company.razon_social}</option>
                ))}
              </select>
              <strong>{activeCompany?.razon_social || "Pendiente"}</strong>
              <small>{activeCompany ? `RUC ${activeCompany.ruc} / ${activeCompany.regimen_tributario}` : "Registra una empresa desde la API de identidad."}</small>
            </article>

            <article className="context-card">
              <span className="overline">Workspace activo</span>
              <select
                value={activeContext?.active_workspace_id || activeWorkspace?.id || ""}
                onChange={(event) => selectWorkspace(event.currentTarget.value)}
                disabled={!authorized || !workspaces.length || loading}
                aria-label="Workspace activo"
              >
                <option value="">{workspaces.length ? "Seleccionar workspace" : "Sin workspaces"}</option>
                {workspaces.map((workspace) => (
                  <option key={workspace.id} value={workspace.id}>{workspace.nombre}</option>
                ))}
              </select>
              <strong>{activeWorkspace?.nombre || "Pendiente"}</strong>
              <small>{activeWorkspace ? `${activeWorkspace.estado} / plan ${activeWorkspace.plan_id}` : "Crea un workspace ligado a empresa."}</small>
            </article>

            <article className="context-card">
              <span className="overline">Sesion</span>
              {!authorized ? (
                <form className="compact-login" onSubmit={login}>
                  <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label="Usuario" placeholder="Usuario" autoComplete="username" />
                  <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" aria-label="Clave" placeholder="Clave" autoComplete="current-password" />
                  <button className="primary-button" type="submit" disabled={loading || !username || !password}>
                    <Lock size={16} />
                    Entrar
                  </button>
                </form>
              ) : (
                <div className="session-summary">
                  <strong>{currentUser?.username}</strong>
                  <small>{currentUser?.role} / {planName}</small>
                </div>
              )}
            </article>
          </div>
        </section>

        <section className="metric-grid" aria-label="Indicadores principales">
          <MetricTile label="Alertas abiertas" value={realCount(openAlerts, authorized)} tone={taxTone} icon={<BellRing size={21} />} detail="Riesgo tributario" />
          <MetricTile label="Recomendaciones" value={realCount(recommendationCount, authorized)} tone={recommendationTone} icon={<Sparkles size={21} />} detail="Revision activa" />
          <MetricTile label="Documentos" value={realCount(documentCount, authorized)} tone={accountingTone} icon={<FileCheck2 size={21} />} detail="Evidencia" />
          <MetricTile label="Audit trail" value={realCount(auditCount, authorized)} tone={auditTone} icon={<Layers3 size={21} />} detail="Trazabilidad" />
        </section>

        <section className="workspace-grid" id="identity" data-screen="identity">
          <article className="command-panel wide">
            <SectionHeader eyebrow="Centro de navegacion" title="Identidad operacional">
              Roles, planes, empresa y workspace quedan gobernados por backend.
            </SectionHeader>
            <div className="identity-grid">
              <InfoCard icon={<Building2 size={22} />} eyebrow="Empresas" title={formatNumber(companies.length)} detail={activeCompany?.razon_social || "Sin empresa activa"} tone={companies.length ? "green" : "yellow"} meta="RUC unico y tenant scoped" />
              <InfoCard icon={<Gauge size={22} />} eyebrow="Workspaces" title={formatNumber(workspaces.length)} detail={activeWorkspace?.nombre || "Sin workspace activo"} tone={workspaces.length ? "green" : "yellow"} meta="Membership requerido" />
              <InfoCard icon={<ShieldCheck size={22} />} eyebrow="Permisos" title={permissions?.enforced_by_backend ? "Backend" : "Pendiente"} detail={`${formatNumber(rolePermissions.length)} permisos visibles para el usuario.`} tone={permissions?.enforced_by_backend ? "green" : "yellow"} meta={currentUser?.role || "Sin rol"} />
            </div>
          </article>

          <article className="command-panel" id="sunat" data-screen="sunat">
            <SectionHeader eyebrow="SUNAT Foundation" title="Clave SOL auxiliar" action={<StatusPill tone={currentSunatTone}>{compactStatus(sunatStatus?.status || "NOT_CONNECTED")}</StatusPill>}>
              Solo lectura, consentimiento explicito y sin acciones tributarias.
            </SectionHeader>
            <div className="sunat-state">
              <span className="sunat-icon"><Landmark size={26} /></span>
              <strong>{sunatStatus?.connection?.connection_type || "CLAVE_SOL_AUXILIAR"}</strong>
              <p>Conector real: {sunatStatus?.real_connector_enabled ? "activo" : "off"} / Foundation: {sunatStatus?.foundation_only ? "activa" : "pendiente"}</p>
              <small>Acciones remotas: {sunatStatus?.connection?.remote_actions_enabled ? "activas" : "deshabilitadas"}</small>
            </div>
            <form className="sunat-prep-form" onSubmit={prepareSunatAuxiliary}>
              <p>DCFT necesita acceso de consulta para el diagnostico inicial. No declarara, no pagara y no modificara informacion.</p>
              <input
                value={sunatAuxForm.ruc || activeCompany?.ruc || ""}
                onChange={(event) => setSunatAuxForm({ ...sunatAuxForm, ruc: event.target.value })}
                aria-label="RUC SUNAT auxiliar"
                placeholder="RUC"
                disabled={!authorized || !activeCompany || loading}
                inputMode="numeric"
              />
              <input
                value={sunatAuxForm.auxiliary_user_alias}
                onChange={(event) => setSunatAuxForm({ ...sunatAuxForm, auxiliary_user_alias: event.target.value })}
                aria-label="Usuario secundario SUNAT"
                placeholder="Usuario secundario SUNAT"
                disabled={!authorized || !activeCompany || loading}
                autoComplete="off"
              />
              <button className="secondary-link" type="button" disabled>
                Validar conexion pendiente
              </button>
              <button className="primary-button" type="submit" disabled={!canPrepareSunatAux || loading}>
                <ShieldCheck size={17} />
                Preparar usuario auxiliar
              </button>
              <small>Permisos pendientes: consulta / solo lectura / sin Clave SOL principal.</small>
            </form>
          </article>
        </section>

        <section className="card-grid">
          {operationalCards.map((card) => (
            <InfoCard key={card.eyebrow} {...card} />
          ))}
        </section>

        <section className="workspace-grid">
          <article className="command-panel" id="alerts" data-screen="alerts">
            <SectionHeader eyebrow="Riesgos" title="Alertas activas" />
            <RecordList records={alerts} kind="alert" emptyText="No existen alertas abiertas en este workspace." />
          </article>

          <article className="command-panel" id="recommendations" data-screen="recommendations">
            <SectionHeader eyebrow="Recomendaciones" title="Revision profesional" />
            <RecordList records={recommendations} kind="recommendation" emptyText="No existen recomendaciones registradas para este tenant." />
          </article>
        </section>

        <section className="workspace-grid">
          <article className="command-panel wide">
            <SectionHeader eyebrow="Estado documental" title="Evidencia reciente">
              Metadata, OCR y documentos se leen desde backend.
            </SectionHeader>
            <DocumentEvidenceList documents={documents} ingestions={documentIngestions} authorized={authorized} />
          </article>

          <article className="command-panel" id="governance" data-screen="governance">
            <SectionHeader eyebrow="Aprobaciones" title="Gobierno humano" />
            <GovernanceList records={governance} />
            <div className="audit-strip">
              <span>Integridad</span>
              <strong>{audit?.integrity?.tamper_detected ? "Revisar" : "Visible"}</strong>
              <small>{formatNumber(audit?.integrity?.checked_events)} eventos verificados</small>
            </div>
          </article>
        </section>

        <section className="command-panel" id="plans" data-screen="plans">
          <SectionHeader eyebrow="Estado del plan" title="Planes y limites">
            Plan comercial activo y limites leidos desde backend.
          </SectionHeader>
          <div className="plans-grid">
            {plansToRender.map((plan) => (
              <article className={`plan-card ${plan.id === effectivePlanId ? "active" : ""}`} key={plan.id}>
              <div className="plan-card__top">
                <span>{plan.id === effectivePlanId ? "Plan efectivo" : "Plan disponible"}</span>
                <StatusPill tone={plan.id.includes("premium") ? "yellow" : "neutral"}>{plan.name}</StatusPill>
              </div>
              <h3>{plan.name}</h3>
              <p>{plan.requires_ruc ? "Requiere RUC para empresa." : "Puede iniciar sin RUC como estudiante."}</p>
              {plan.trial_days ? <small>Trial inicial: {plan.trial_days} dias.</small> : null}
              <div className="plan-limits">
                  {Object.entries(plan.limits).slice(0, 4).map(([key, value]) => (
                    <span key={key}>{featureLabel(key)} <strong>{formatNumber(value)}</strong></span>
                  ))}
                </div>
                <div className="feature-list">
                  {plan.features.slice(0, 4).map((feature) => (
                    <span key={feature}><CheckCircle2 size={15} /> {featureLabel(feature)}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>

        {adminUsers.length ? (
          <section className="command-panel" id="admin-ceo" data-screen="admin">
            <SectionHeader eyebrow="Admin CEO" title="Usuarios y trials">
              Panel protegido por backend para pruebas controladas.
            </SectionHeader>
            <div className="admin-user-grid">
              {adminUsers.slice(0, 8).map((user) => (
                <article className="admin-user-card" key={user.user_id}>
                  <div>
                    <span>{user.role}</span>
                    <h3>{user.username}</h3>
                    <p>{user.company?.razon_social || user.tenant_name} / {user.workspace?.nombre || "Sin workspace"}</p>
                  </div>
                  <div className="admin-user-meta">
                    <StatusPill tone={user.trial?.active ? "yellow" : "neutral"}>
                      {user.trial?.active ? "Premium de prueba" : "Trial inactivo"}
                    </StatusPill>
                    <small>Base {featureLabel(user.plan)} / efectivo {featureLabel(user.plan_effective)}</small>
                    <small>Onboarding {user.onboarding.ready_for_testing ? "listo" : "pendiente"}</small>
                  </div>
                  <div className="admin-actions">
                    <button className="primary-button" type="button" onClick={() => setAdminTrial(user.user_id, true)} disabled={loading}>
                      Activar 7 dias
                    </button>
                    <button className="secondary-link" type="button" onClick={() => setAdminTrial(user.user_id, false)} disabled={loading}>
                      Desactivar
                    </button>
                    <select value={user.plan} onChange={(event) => setAdminPlan(user.user_id, event.target.value)} disabled={loading} aria-label={`Plan de ${user.username}`}>
                      {plansToRender.map((plan) => (
                        <option value={plan.id} key={plan.id}>{plan.name}</option>
                      ))}
                    </select>
                  </div>
                </article>
              ))}
            </div>
          </section>
        ) : null}

        <section className="workspace-grid">
          <article className="command-panel" id="onboarding" data-screen="onboarding">
            <SectionHeader eyebrow="Onboarding inicial" title="Alta de workspace" />
            <form className="onboarding-form" onSubmit={createTenant}>
              <input value={onboardingForm.tenant_name} onChange={(event) => setOnboardingForm({ ...onboardingForm, tenant_name: event.target.value })} aria-label="Empresa" placeholder="Nombre de empresa" disabled={loading || authorized} autoComplete="organization" />
              <input value={onboardingForm.tenant_id} onChange={(event) => setOnboardingForm({ ...onboardingForm, tenant_id: event.target.value })} aria-label="Identificador opcional" placeholder="ID opcional" disabled={loading || authorized} autoComplete="off" />
              <input value={onboardingForm.admin_username} onChange={(event) => setOnboardingForm({ ...onboardingForm, admin_username: event.target.value })} aria-label="Administrador" placeholder="Administrador" disabled={loading || authorized} autoComplete="username" />
              <input value={onboardingForm.admin_password} onChange={(event) => setOnboardingForm({ ...onboardingForm, admin_password: event.target.value })} type="password" aria-label="Clave inicial" placeholder="Clave inicial" disabled={loading || authorized} autoComplete="new-password" />
              <select value={onboardingForm.account_type} onChange={(event) => setOnboardingForm({ ...onboardingForm, account_type: event.target.value, plan: event.target.value === "student" ? "student" : onboardingForm.plan === "student" ? "mype" : onboardingForm.plan })} aria-label="Tipo de cuenta" disabled={loading || authorized}>
                <option value="student">Estudiante / sin RUC</option>
                <option value="business">Empresa / con RUC</option>
              </select>
              <select value={onboardingForm.plan} onChange={(event) => setOnboardingForm({ ...onboardingForm, plan: event.target.value, account_type: event.target.value === "student" ? "student" : "business" })} aria-label="Plan" disabled={loading || authorized}>
                {plansToRender.map((plan) => (
                  <option key={plan.id} value={plan.id}>{plan.name}</option>
                ))}
              </select>
              {onboardingForm.account_type === "business" || onboardingRequiresRuc ? (
                <>
                  <input value={onboardingForm.ruc} onChange={(event) => setOnboardingForm({ ...onboardingForm, ruc: event.target.value })} aria-label="RUC" placeholder="RUC de la empresa" disabled={loading || authorized} inputMode="numeric" />
                  <input value={onboardingForm.razon_social} onChange={(event) => setOnboardingForm({ ...onboardingForm, razon_social: event.target.value })} aria-label="Razon social" placeholder="Razon social" disabled={loading || authorized} autoComplete="organization" />
                  <input value={onboardingForm.nombre_comercial} onChange={(event) => setOnboardingForm({ ...onboardingForm, nombre_comercial: event.target.value })} aria-label="Nombre comercial" placeholder="Nombre comercial opcional" disabled={loading || authorized} autoComplete="organization-title" />
                </>
              ) : null}
              <label className="checkbox-line">
                <input type="checkbox" checked={onboardingForm.trial_requested} onChange={(event) => setOnboardingForm({ ...onboardingForm, trial_requested: event.target.checked })} disabled={loading || authorized} />
                Activar trial inicial de 7 dias
              </label>
              <button className="primary-button" type="submit" disabled={loading || authorized || !canCreateTenant}>
                <UserPlus size={17} />
                Crear workspace
                <ArrowRight size={17} />
              </button>
            </form>
            <div className="empty-state">
              <Landmark size={18} />
              <div>
                <strong>SUNAT seguro</strong>
                <span>Solo preparar usuario secundario/auxiliar. No ingresar Clave SOL principal ni ejecutar declaraciones.</span>
              </div>
            </div>
            {onboardingProgress ? (
              <div className="checklist-grid" aria-label="Checklist de onboarding">
                {Object.entries(onboardingProgress.checklist).map(([key, value]) => (
                  <span className={value ? "done" : "pending"} key={key}>
                    <CheckCircle2 size={15} />
                    {featureLabel(key)}
                  </span>
                ))}
              </div>
            ) : null}
            <div className="video-slot-list" aria-label="Guias de onboarding">
              {(onboardingProgress?.videos || [
                { id: "sunat_auxiliary_user", title: "Como crear usuario secundario / auxiliar SUNAT", description: "Antes de conectar tu empresa, mira este video de 2 minutos para crear un acceso seguro de consulta.", placeholder: true, duration_hint: "2 minutos", seen: false, button_label: "Marcar como visto" },
                { id: "connect_company", title: "Como conectar tu empresa a DCFT", description: "Prepara RUC, razon social y workspace.", placeholder: true, duration_hint: "2 minutos", seen: false, button_label: "Marcar como visto" },
                { id: "interpret_diagnosis", title: "Como interpretar tu diagnostico empresarial", description: "Lee alertas, semaforo empresarial y prioridades.", placeholder: true, duration_hint: "2 minutos", seen: false, button_label: "Marcar como visto" }
              ]).map((video) => (
                <article className={`video-card ${video.seen ? "seen" : ""}`} key={video.id}>
                  <span>{video.duration_hint}</span>
                  <strong>{video.title}</strong>
                  <p>{video.description}</p>
                  <button className="secondary-link" type="button" disabled={!authorized || loading || video.seen} onClick={() => markVideoSeen(video.id)}>
                    {video.button_label}
                  </button>
                </article>
              ))}
            </div>
          </article>

          <article className="command-panel" id="analytics" data-screen="analytics">
            <SectionHeader eyebrow="Adopcion" title="Product analytics" />
            <div className="analytics-grid">
              <MetricTile label="Eventos" value={formatNumber(analytics?.events_total)} tone="green" icon={<BarChart3 size={20} />} />
              <MetricTile label="Fallos" value={formatNumber(analytics?.failures_total)} tone={(analytics?.failures_total ?? 0) > 0 ? "red" : "green"} icon={<AlertTriangle size={20} />} />
              <MetricTile label="Onboarding" value={analytics?.activation.onboarding_completed ? "Completo" : "Pendiente"} tone={analytics?.activation.onboarding_completed ? "green" : "yellow"} icon={<CheckCircle2 size={20} />} />
            </div>
          </article>
        </section>

        <section className="command-panel" id="runtime" data-screen="runtime">
          <SectionHeader eyebrow="Runtime" title="Postura tecnica">
            Health, database, IA, OCR y observabilidad.
          </SectionHeader>
          <div className="runtime-grid">
            <InfoCard icon={<Activity size={22} />} eyebrow="Backend" title={health?.status || "checking"} detail={`DB ${compactStatus(runtime?.database?.backend)} / ${compactStatus(runtime?.database?.status)}`} tone={backendOk ? "green" : "yellow"} />
            <InfoCard icon={<Lock size={22} />} eyebrow="IA" title={compactStatus(runtime?.ai_pipeline)} detail="Provider gobernado por runtime." tone={aiTone} />
            <InfoCard icon={<ClipboardList size={22} />} eyebrow="OCR" title={compactStatus(runtime?.ocr_pipeline)} detail="Documentos con metadata verificable." tone={ocrTone} />
            <InfoCard icon={<Clock3 size={22} />} eyebrow="Observabilidad" title={`${formatNumber(runtime?.persistent_observability?.events_total)} eventos`} detail={`${runtime?.persistent_observability?.avg_latency_ms ?? 0} ms promedio.`} tone={databaseTone} />
          </div>
        </section>

        <footer className="quiet-footer">
          <span>API: {API_URL || "sin configurar"}</span>
          <span>{authorized ? `Tenant: ${summary?.tenant_id || currentUser?.tenant_id || "activo"}` : "Sesion no iniciada"}</span>
        </footer>
      </div>

      <nav className="mobile-tabbar" data-screen="mobile-nav" aria-label="Navegacion mobile">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          if (item.href === "#dashboard") {
            return (
            <a href={item.href} key={item.href}>
              <Icon size={18} />
              <span>{item.label}</span>
            </a>
            );
          }
          const panel = item.label === "Diagnostico" ? "diagnostico" : item.label === "Reportes" ? "reportes" : item.label === "Doctor" ? "doctor" : "perfil";
          return (
            <button type="button" onClick={() => openPanel(panel as PanelKey)} key={item.href}>
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {activePanel ? (
        <div className="panel-backdrop" role="dialog" aria-modal="true" aria-label={panelTitles[activePanel]} onClick={closePanel}>
          <section className="premium-drawer" onClick={(event) => event.stopPropagation()}>
            <header className="drawer-header">
              <div>
                <span className="overline">DCFT</span>
                <h2>{panelTitles[activePanel]}</h2>
              </div>
              <button className="icon-button" type="button" onClick={closePanel} title="Cerrar panel">
                <X size={18} />
              </button>
            </header>
            <div className="drawer-content">
              {publicError ? <section className="calm-alert">{publicError}</section> : null}
              {renderPanelContent()}
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}

export default App;
