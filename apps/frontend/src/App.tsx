import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  BarChart3,
  BellRing,
  Building2,
  CheckCircle2,
  Clock3,
  FileCheck2,
  Gauge,
  Landmark,
  Layers3,
  Lock,
  LogOut,
  RefreshCcw,
  Scale,
  ShieldCheck,
  Sparkles,
  UserPlus,
  WalletCards
} from "lucide-react";
import { type FormEvent, type ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import { API_URL, ApiError, post, request, type Session } from "./lib/api";

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
  observability?: Record<string, unknown>;
  audit_integrity?: {
    checked_events: number;
    legacy_unhashed_events: number;
    tamper_detected: boolean;
    chain_forks_detected: boolean;
  };
  persistent_observability?: {
    events_total: number;
    errors_total: number;
    avg_latency_ms: number;
    max_latency_ms: number;
    recent_sample: number;
    by_type: Record<string, number>;
  };
  notes?: string[];
};

type CurrentUser = {
  username: string;
  tenant_id: string;
  role: string;
  plan: string;
  permissions: string[];
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
  requested_by?: string;
  plan?: string;
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

type SignalTone = "green" | "yellow" | "red" | "neutral";

const PRODUCT_NAME = "DCFT";
const PRODUCT_FULL_NAME = "Doctor Contable Financiero Tributario";
const PRODUCT_TAGLINE = "Tu copiloto contable, financiero y tributario.";

const HUMAN_CONTROL_MESSAGES = [
  "DCFT no reemplaza al contador; potencia la gestión empresarial.",
  "Las recomendaciones deben validarse con un profesional cuando corresponda.",
  "Control humano siempre activo."
];

const NAV_ITEMS = [
  { href: "#dashboard", label: "Estado", icon: Gauge },
  { href: "#alerts", label: "Alertas", icon: BellRing },
  { href: "#recommendations", label: "Revisar", icon: Sparkles },
  { href: "#governance", label: "Control", icon: ShieldCheck }
];

function BrandGlyph() {
  return (
    <span className="brand-glyph" aria-hidden="true">
      <span className="brand-glyph__crest" />
      <span className="brand-glyph__pulse" />
    </span>
  );
}

function toneLabel(tone: SignalTone) {
  if (tone === "green") return "Saludable";
  if (tone === "yellow") return "Atención";
  if (tone === "red") return "Crítico";
  return "Evaluando";
}

function severityTone(severity?: string): SignalTone {
  if (severity === "critical" || severity === "high") return "red";
  if (severity === "medium") return "yellow";
  if (severity === "low") return "green";
  return "neutral";
}

function compactStatus(value?: string | boolean) {
  if (typeof value === "boolean") return value ? "Activo" : "Inactivo";
  if (!value) return "Pendiente";
  return value.replace(/_/g, " ");
}

function formatNumber(value: number | undefined) {
  return new Intl.NumberFormat("es-PE").format(value ?? 0);
}

function featureLabel(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter: string) => letter.toUpperCase());
}

function recordDate(value?: string) {
  if (!value) return "Sin fecha";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-PE", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }).format(date);
}

function RiskBadge({ tone, children }: { tone: SignalTone; children: ReactNode }) {
  return <span className={`risk-badge ${tone}`}>{children}</span>;
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

function TrafficLight({ tone }: { tone: SignalTone }) {
  return (
    <div className="traffic-light" data-screen="semaforo-empresarial" aria-label={`Semáforo empresarial ${toneLabel(tone)}`}>
      <span className={tone === "red" ? "active red" : "red"} />
      <span className={tone === "yellow" ? "active yellow" : "yellow"} />
      <span className={tone === "green" ? "active green" : "green"} />
    </div>
  );
}

function MetricTile({
  label,
  value,
  tone,
  icon
}: {
  label: string;
  value: string;
  tone: SignalTone;
  icon: ReactNode;
}) {
  return (
    <article className={`metric-tile ${tone}`}>
      <span className="metric-icon">{icon}</span>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </article>
  );
}

function DomainCard({
  icon,
  eyebrow,
  title,
  description,
  tone,
  metric
}: {
  icon: ReactNode;
  eyebrow: string;
  title: string;
  description: string;
  tone: SignalTone;
  metric: string;
}) {
  return (
    <article className={`domain-card ${tone}`} data-screen={eyebrow.toLowerCase()}>
      <div className="domain-card__top">
        <span className="domain-icon">{icon}</span>
        <RiskBadge tone={tone}>{toneLabel(tone)}</RiskBadge>
      </div>
      <span className="overline">{eyebrow}</span>
      <h3>{title}</h3>
      <p>{description}</p>
      <strong>{metric}</strong>
    </article>
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
    return <EmptyState title="Sin registros reales todavía" text={emptyText} />;
  }

  return (
    <div className="record-list">
      {records.slice(0, 5).map((record) => {
        const tone = kind === "alert" ? severityTone(record.severity) : "green";
        const title = kind === "alert" ? record.title || "Alerta registrada" : record.objective || "Recomendación registrada";
        const body = kind === "alert"
          ? record.source || record.status
          : record.recommendation || record.explainability?.recommendation || "Revisión determinística lista para validar.";
        return (
          <article className="record-row" key={record.id}>
            <div className="record-row__main">
              <RiskBadge tone={tone}>{kind === "alert" ? record.severity || record.status : record.category || record.status}</RiskBadge>
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
            <span className="record-time">{recordDate(record.timestamp)}</span>
          </article>
        );
      })}
    </div>
  );
}

function GovernanceList({ records }: { records: GovernanceRequest[] }) {
  if (!records.length) {
    return <EmptyState title="Sin bloqueos activos registrados" text="Cuando exista una acción sensible, governance la mostrará como pendiente, aprobada o bloqueada." />;
  }

  return (
    <div className="governance-list">
      {records.slice(0, 5).map((record) => (
        <article className="governance-row" key={record.id}>
          <div>
            <RiskBadge tone={severityTone(record.risk)}>{record.status}</RiskBadge>
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
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [plans, setPlans] = useState<PlanDefinition[]>([]);
  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [alerts, setAlerts] = useState<OperationalRecord[]>([]);
  const [recommendations, setRecommendations] = useState<OperationalRecord[]>([]);
  const [governance, setGovernance] = useState<GovernanceRequest[]>([]);
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [onboardingForm, setOnboardingForm] = useState({
    tenant_name: "Mi empresa",
    tenant_id: "",
    admin_username: "",
    admin_password: "",
    plan: "business_basic"
  });

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
    setGovernance([]);
    setAudit(null);
    setError(reason === "session closed" ? "" : reason);
  }, []);

  const handleError = useCallback((err: unknown, fallback: string) => {
    if (err instanceof ApiError) {
      if (err.status === 401) {
        logout("Sesión expirada. Ingresa nuevamente.");
        return "Sesión expirada. Ingresa nuevamente.";
      }
      if (err.status === 403) return "Permiso denegado por seguridad operacional.";
      if (err.status === 429) return "Límite de uso activo. Intenta nuevamente en unos minutos.";
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
        const [me, dashboard, analyticsBody, alertsBody, recommendationsBody, governanceBody, auditBody] = await Promise.all([
          request<CurrentUser>("/auth/me", {}, token),
          request<Summary>("/dashboard/summary", {}, token),
          optionalSecureRequest<AnalyticsSummary | null>("/analytics/summary", null, token),
          optionalSecureRequest<OperationalRecord[]>("/alerts?limit=6", [], token),
          optionalSecureRequest<OperationalRecord[]>("/recommendations?limit=6", [], token),
          optionalSecureRequest<GovernanceRequest[]>("/governance/approval-requests?limit=6", [], token),
          optionalSecureRequest<AuditResponse | null>("/audit/events?limit=6", null, token)
        ]);
        setCurrentUser(me);
        setSummary(dashboard);
        setAnalytics(analyticsBody);
        setAlerts(alertsBody);
        setRecommendations(recommendationsBody);
        setGovernance(governanceBody);
        setAudit(auditBody);
      } else {
        setCurrentUser(null);
        setSummary(null);
        setAnalytics(null);
        setAlerts([]);
        setRecommendations([]);
        setGovernance([]);
        setAudit(null);
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
      setError(handleError(err, "No se pudo iniciar sesión."));
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

  useEffect(() => {
    refresh();
  }, [refresh]);

  const signal = useMemo(() => {
    const openAlerts = summary?.counts.open_alerts ?? 0;
    const overLimit = Object.keys(summary?.usage?.over_limit || {}).length;
    const failures = analytics?.failures_total ?? 0;
    if (!authorized || !summary) return "neutral" as SignalTone;
    if (openAlerts > 2 || overLimit > 0 || failures > 0 || runtimeStatus?.busy_loop) return "red" as SignalTone;
    if (openAlerts > 0 || (summary.counts.documents ?? 0) === 0) return "yellow" as SignalTone;
    return "green" as SignalTone;
  }, [analytics, authorized, runtimeStatus, summary]);

  const openAlerts = summary?.counts.open_alerts ?? alerts.filter((alert) => alert.status === "open").length;
  const overLimitCount = Object.keys(summary?.usage?.over_limit || {}).length;
  const taxTone: SignalTone = !authorized ? "neutral" : openAlerts > 2 ? "red" : openAlerts > 0 ? "yellow" : "green";
  const financeTone: SignalTone = !authorized ? "neutral" : overLimitCount > 0 ? "red" : "green";
  const accountingTone: SignalTone = !authorized ? "neutral" : (summary?.counts.documents ?? 0) > 0 ? "green" : "yellow";

  const runtime = runtimeStatus || summary?.runtime || null;
  const planName = summary?.plan.name || currentUser?.plan || "Business";
  const plansToRender = plans.length ? plans : onboardingStatus?.plans || [];
  const activePlanId = summary?.plan.id || currentUser?.plan || onboardingForm.plan;
  const backendOk = health?.status === "ok" && runtime?.status === "active";
  const canCreateTenant = Boolean(onboardingStatus?.signup_enabled && onboardingForm.admin_username.trim() && onboardingForm.admin_password.length >= 10);

  return (
    <main className={`dcft-shell ${authorized ? "is-authorized" : "is-guest"}`}>
      <header className="nav-shell">
        <a className="brand-lockup" href="#top" aria-label="DCFT inicio">
          <span className="brandmark"><BrandGlyph /></span>
          <span className="brand-copy">
            <strong>{PRODUCT_NAME}</strong>
            <span>{PRODUCT_FULL_NAME}</span>
          </span>
        </a>

        <nav className="nav-links" aria-label="Navegación principal">
          <a href="#dashboard">Dashboard</a>
          <a href="#plans">Planes</a>
          <a href="#governance">Governance</a>
          <a href="#runtime">Runtime</a>
        </nav>

        <div className="nav-actions" data-screen="login-mobile">
          <span className={`session-badge ${backendOk ? "ok" : "warn"}`}>
            <ShieldCheck size={16} />
            {authorized ? "Workspace protegido" : "Acceso seguro"}
          </span>
          <button className="ghost-button" onClick={refresh} disabled={loading} title="Actualizar">
            <RefreshCcw size={18} />
          </button>
          {authorized ? (
            <button className="ghost-button" onClick={() => logout()} disabled={loading} title="Cerrar sesión">
              <LogOut size={18} />
            </button>
          ) : null}
        </div>
      </header>

      {loading ? (
        <div className="loading-strip" role="status">
          <span />
          Actualizando datos reales del backend local...
        </div>
      ) : null}

      {error ? <section className="calm-alert">{error}</section> : null}

      <section className="hero-experience" id="top" data-screen="hero-principal">
        <div className="hero-copy">
          <span className="overline">Producto premium empresarial</span>
          <h1>{PRODUCT_TAGLINE}</h1>
          <p>
            Una cabina clara para entender cómo está tu empresa, qué riesgo requiere atención y qué debe validar un profesional antes de actuar.
          </p>
          <div className="hero-trust-row">
            {HUMAN_CONTROL_MESSAGES.map((message) => (
              <span key={message}><BadgeCheck size={16} /> {message}</span>
            ))}
          </div>
        </div>

        <aside className="hero-console">
          <div className="console-brand">
            <img src="/dcft-icon.svg" alt="Logo DCFT" />
            <div>
              <span>Doctor Contable Financiero Tributario</span>
              <strong>{authorized ? summary?.tenant_id || currentUser?.tenant_id : "Modo demo/local"}</strong>
            </div>
          </div>

          <div className="diagnosis-panel" data-screen="semaforo-empresarial">
            <div className="diagnosis-top">
              <span>Semáforo empresarial</span>
              <RiskBadge tone={signal}>{toneLabel(signal)}</RiskBadge>
            </div>
            <TrafficLight tone={signal} />
            <p>
              {authorized
                ? "Lectura calculada con señales reales del workspace y límites del plan activo."
                : "Ingresa o crea un workspace para ver el diagnóstico real de tu empresa."}
            </p>
          </div>

          {!authorized ? (
            <form className="login-panel" onSubmit={login}>
              <span className="overline">Login seguro</span>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                aria-label="Usuario"
                placeholder="Usuario"
                autoComplete="username"
              />
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                aria-label="Clave segura"
                placeholder="Clave segura"
                autoComplete="current-password"
              />
              <button className="primary-button" type="submit" disabled={loading || !username || !password}>
                <Lock size={17} />
                Entrar a DCFT
                <ArrowRight size={17} />
              </button>
            </form>
          ) : (
            <div className="session-panel">
              <span className="overline">Sesión activa</span>
              <strong>{currentUser?.username}</strong>
              <p>{currentUser?.role} · {planName}</p>
            </div>
          )}
        </aside>
      </section>

      <section className="control-room section-band" id="dashboard" data-screen="dashboard">
        <SectionHeader
          eyebrow="Dashboard ejecutivo"
          title="Estado general de la empresa"
          action={<RiskBadge tone={signal}>{toneLabel(signal)}</RiskBadge>}
        >
          Datos operativos conectados al backend. Los bloques vacíos indican ausencia real de registros, no datos inventados.
        </SectionHeader>

        <div className="metric-grid">
          <MetricTile label="Alertas abiertas" value={formatNumber(openAlerts)} tone={taxTone} icon={<BellRing size={21} />} />
          <MetricTile label="Recomendaciones" value={formatNumber(summary?.counts.recommendations)} tone="green" icon={<Sparkles size={21} />} />
          <MetricTile label="Documentos" value={formatNumber(summary?.counts.documents)} tone={accountingTone} icon={<FileCheck2 size={21} />} />
          <MetricTile label="Audit trail" value={formatNumber(summary?.counts.audit_events ?? runtime?.audit_events)} tone="green" icon={<Layers3 size={21} />} />
        </div>

        <div className="executive-grid">
          <article className="company-panel">
            <div className="company-panel__top">
              <span className="company-icon"><Building2 size={24} /></span>
              <div>
                <span>Workspace</span>
                <h3>{summary?.tenant_id || "Empresa no conectada"}</h3>
              </div>
            </div>
            <div className="company-panel__facts">
              <span>Plan</span>
              <strong>{planName}</strong>
              <span>Rol</span>
              <strong>{currentUser?.role || "Acceso pendiente"}</strong>
              <span>Backend</span>
              <strong>{health?.status || "checking"}</strong>
            </div>
          </article>

          <article className="diagnosis-summary">
            <span>Diagnóstico DCFT</span>
            <h3>{toneLabel(signal)}</h3>
            <p>
              {signal === "green"
                ? "No hay bloqueos críticos en la lectura actual."
                : signal === "yellow"
                  ? "Hay señales que conviene revisar antes del cierre."
                  : signal === "red"
                    ? "Se requiere revisión prioritaria con control humano."
                    : "El sistema está listo para evaluar tu empresa."}
            </p>
          </article>
        </div>

        <div className="domain-grid">
          <DomainCard
            icon={<Scale size={22} />}
            eyebrow="Tributario"
            title="Obligaciones bajo control"
            description="Vencimientos, alertas y revisión fiscal sin acciones oficiales autónomas."
            tone={taxTone}
            metric={`${formatNumber(openAlerts)} alertas`}
          />
          <DomainCard
            icon={<WalletCards size={22} />}
            eyebrow="Financiero"
            title="Capacidad operativa visible"
            description="Límites del plan, presión de uso y señales de operación."
            tone={financeTone}
            metric={`${formatNumber(overLimitCount)} excesos`}
          />
          <DomainCard
            icon={<Landmark size={22} />}
            eyebrow="Contable"
            title="Evidencia documental"
            description="Documentos y trazabilidad para sostener decisiones verificables."
            tone={accountingTone}
            metric={`${formatNumber(summary?.counts.documents)} documentos`}
          />
        </div>
      </section>

      <section className="section-band split-band" id="alerts" data-screen="alerts">
        <SectionHeader eyebrow="Alertas premium" title="Riesgos que requieren revisión">
          Las alertas se muestran desde el backend. Si no hay registros, DCFT mantiene una lectura limpia sin inventar urgencias.
        </SectionHeader>
        <RecordList records={alerts} kind="alert" emptyText="No existen alertas abiertas en este workspace." />
      </section>

      <section className="section-band split-band" id="recommendations" data-screen="recommendations">
        <SectionHeader eyebrow="Recomendaciones" title="Qué recomienda revisar DCFT">
          Reglas determinísticas locales, explicables y sujetas a validación humana cuando corresponda.
        </SectionHeader>
        <RecordList records={recommendations} kind="recommendation" emptyText="No existen recomendaciones registradas para este tenant." />
      </section>

      <section className="section-band analytics-band" id="analytics" data-screen="analytics">
        <SectionHeader eyebrow="Product analytics" title="Activación y señales de adopción">
          Product analytics con métricas operativas reales para entender onboarding, primer flujo y primera señal empresarial.
        </SectionHeader>
        <div className="analytics-grid">
          <MetricTile label="Eventos" value={formatNumber(analytics?.events_total)} tone="green" icon={<BarChart3 size={21} />} />
          <MetricTile label="Fallos" value={formatNumber(analytics?.failures_total)} tone={(analytics?.failures_total ?? 0) > 0 ? "red" : "green"} icon={<AlertTriangle size={21} />} />
          <MetricTile label="Onboarding" value={analytics?.activation.onboarding_completed ? "Completo" : "Pendiente"} tone={analytics?.activation.onboarding_completed ? "green" : "yellow"} icon={<CheckCircle2 size={21} />} />
          <MetricTile label="Primera señal" value={analytics?.activation.first_business_signal ? "Activa" : "Pendiente"} tone={analytics?.activation.first_business_signal ? "green" : "yellow"} icon={<Activity size={21} />} />
        </div>
      </section>

      <section className="section-band" id="governance" data-screen="governance">
        <SectionHeader eyebrow="Governance y control humano" title="Qué está bloqueado o pendiente">
          Controlled feedback, aprobaciones humanas y trazabilidad para acciones sensibles.
        </SectionHeader>
        <div className="governance-layout">
          <GovernanceList records={governance} />
          <aside className="human-control-panel">
            <span className="overline">Apple Store awareness</span>
            {HUMAN_CONTROL_MESSAGES.map((message) => (
              <p key={message}><ShieldCheck size={17} /> {message}</p>
            ))}
            <div className="audit-mini">
              <span>Audit trail</span>
              <strong>{audit?.integrity?.tamper_detected ? "Revisar integridad" : "Integridad visible"}</strong>
              <small>{formatNumber(audit?.integrity?.checked_events)} eventos verificados</small>
            </div>
          </aside>
        </div>
      </section>

      <section className="section-band" id="plans" data-screen="plans-detail">
        <SectionHeader eyebrow="Subscription / Planes" title="Planes claros, sin pagos activados">
          Subscription se lee desde el backend y muestra límites reales. No se habilitan pagos ni cambios comerciales externos.
        </SectionHeader>
        <div className="plans-grid">
          {plansToRender.map((plan) => (
            <article className={`plan-card ${plan.id === activePlanId ? "active" : ""}`} key={plan.id}>
              <div className="plan-card__top">
                <span>{plan.id === activePlanId ? "Plan actual" : "Plan disponible"}</span>
                <RiskBadge tone={plan.id.includes("premium") ? "yellow" : "neutral"}>{plan.name}</RiskBadge>
              </div>
              <h3>{plan.name}</h3>
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

      <section className="section-band onboarding-premium" id="onboarding" data-screen="onboarding-premium">
        <SectionHeader eyebrow="Onboarding premium" title="Crear un espacio de diagnóstico">
          Un alta breve, segura y marcada como local cuando se usa en esta instancia.
        </SectionHeader>
        <form className="onboarding-form" onSubmit={createTenant}>
          <input
            value={onboardingForm.tenant_name}
            onChange={(event) => setOnboardingForm({ ...onboardingForm, tenant_name: event.target.value })}
            aria-label="Empresa"
            placeholder="Nombre de empresa"
            disabled={loading || authorized}
            autoComplete="organization"
          />
          <input
            value={onboardingForm.tenant_id}
            onChange={(event) => setOnboardingForm({ ...onboardingForm, tenant_id: event.target.value })}
            aria-label="Identificador opcional"
            placeholder="ID opcional"
            disabled={loading || authorized}
            autoComplete="off"
          />
          <input
            value={onboardingForm.admin_username}
            onChange={(event) => setOnboardingForm({ ...onboardingForm, admin_username: event.target.value })}
            aria-label="Administrador"
            placeholder="Administrador"
            disabled={loading || authorized}
            autoComplete="username"
          />
          <input
            value={onboardingForm.admin_password}
            onChange={(event) => setOnboardingForm({ ...onboardingForm, admin_password: event.target.value })}
            type="password"
            aria-label="Clave inicial"
            placeholder="Clave inicial"
            disabled={loading || authorized}
            autoComplete="new-password"
          />
          <select
            value={onboardingForm.plan}
            onChange={(event) => setOnboardingForm({ ...onboardingForm, plan: event.target.value })}
            aria-label="Plan"
            disabled={loading || authorized}
          >
            {plansToRender.map((plan) => (
              <option key={plan.id} value={plan.id}>{plan.name}</option>
            ))}
          </select>
          <button className="primary-button" type="submit" disabled={loading || authorized || !canCreateTenant}>
            <UserPlus size={17} />
            Crear diagnóstico
            <ArrowRight size={17} />
          </button>
        </form>
      </section>

      <section className="section-band runtime-band" id="runtime" data-screen="runtime">
        <SectionHeader eyebrow="Runtime y Staging posture" title="Estado técnico sin activar IA ni OCR">
          Visibilidad del backend local, privacidad, auditoría y módulos bloqueados por diseño.
        </SectionHeader>
        <div className="runtime-grid">
          <article className="runtime-panel">
            <span className="runtime-icon"><Activity size={21} /></span>
            <h3>Runtime</h3>
            <p>{compactStatus(runtime?.status)} · {compactStatus(runtime?.runtime_loop)}</p>
          </article>
          <article className="runtime-panel">
            <span className="runtime-icon"><Lock size={21} /></span>
            <h3>IA / OCR</h3>
            <p>{compactStatus(runtime?.ai_pipeline)} · {compactStatus(runtime?.ocr_pipeline)}</p>
          </article>
          <article className="runtime-panel">
            <span className="runtime-icon"><Clock3 size={21} /></span>
            <h3>Observabilidad</h3>
            <p>{formatNumber(runtime?.persistent_observability?.events_total)} eventos · {runtime?.persistent_observability?.avg_latency_ms ?? 0} ms promedio</p>
          </article>
          <article className="runtime-panel">
            <span className="runtime-icon"><ShieldCheck size={21} /></span>
            <h3>Staging posture</h3>
            <p>Prod {runtime?.production_ready ? "ready" : "off"} · Staging {runtime?.staging_ready ? "ready" : "off"}</p>
          </article>
        </div>
      </section>

      <footer className="quiet-footer">
        <span>API: {API_URL}</span>
        <span>{authorized ? `Tenant: ${summary?.tenant_id || currentUser?.tenant_id || "activo"}` : "Demo/local: sin datos críticos inventados"}</span>
      </footer>

      <nav className="mobile-tabbar" data-screen="mobile-nav" aria-label="Navegación mobile">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <a href={item.href} key={item.href}>
              <Icon size={18} />
              <span>{item.label}</span>
            </a>
          );
        })}
      </nav>
    </main>
  );
}

export default App;
