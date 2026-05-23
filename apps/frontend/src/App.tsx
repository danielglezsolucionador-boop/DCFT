import {
  ArrowRight,
  BadgeCheck,
  Building2,
  CheckCircle2,
  FileCheck2,
  HeartPulse,
  Landmark,
  Lock,
  LogOut,
  RefreshCcw,
  Scale,
  ShieldCheck,
  Sparkles,
  UserPlus,
  WalletCards
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
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
  runtime: {
    status: string;
    busy_loop: boolean;
    ai_pipeline: string;
    ocr_pipeline: string;
    database?: { status: string; backend: string };
  };
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
  modules: Record<string, string>;
  security_warnings: string[];
};

type CurrentUser = {
  username: string;
  tenant_id: string;
  role: string;
  plan: string;
  permissions: string[];
};

type SignalTone = "green" | "yellow" | "red" | "neutral";

const PRODUCT_NAME = "DCFT";
const PRODUCT_FULL_NAME = "Doctor Contable Financiero Tributario";
const PRODUCT_TAGLINE = "El médico de tu empresa";

function BrandGlyph() {
  return (
    <span className="brand-glyph" aria-hidden="true">
      <span className="brand-glyph__cross" />
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

function DomainCard({
  icon,
  eyebrow,
  title,
  description,
  tone,
  metric
}: {
  icon: React.ReactNode;
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
        <span className="status-pill">{toneLabel(tone)}</span>
      </div>
      <p>{eyebrow}</p>
      <h3>{title}</h3>
      <span>{description}</span>
      <strong>{metric}</strong>
    </article>
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

function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem("dcft_token") || "");
  const [health, setHealth] = useState<Health | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [plans, setPlans] = useState<PlanDefinition[]>([]);
  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
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

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [healthBody, onboardingBody, planBody] = await Promise.all([
        request<Health>("/health"),
        request<OnboardingStatus>("/onboarding/status"),
        request<PlanDefinition[]>("/subscriptions/plans")
      ]);
      setHealth(healthBody);
      setOnboardingStatus(onboardingBody);
      setPlans(planBody);
      if (token) {
        const [me, dashboard, analyticsBody] = await Promise.all([
          request<CurrentUser>("/auth/me", {}, token),
          request<Summary>("/dashboard/summary", {}, token),
          request<AnalyticsSummary>("/analytics/summary", {}, token)
        ]);
        setCurrentUser(me);
        setSummary(dashboard);
        setAnalytics(analyticsBody);
      }
    } catch (err) {
      setError(handleError(err, "No se pudo actualizar DCFT."));
    } finally {
      setLoading(false);
    }
  }, [handleError, token]);

  const login = async () => {
    setLoading(true);
    setError("");
    try {
      const session = await post<Session>("/auth/login", { username, password });
      setToken(session.access_token);
      localStorage.setItem("dcft_token", session.access_token);
    } catch (err) {
      setError(handleError(err, "No se pudo iniciar sesión."));
    } finally {
      setLoading(false);
    }
  };

  const createTenant = async () => {
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
    const alerts = summary?.counts.open_alerts ?? 0;
    const overLimit = Object.keys(summary?.usage?.over_limit || {}).length;
    const failures = analytics?.failures_total ?? 0;
    if (!authorized || !summary) return "neutral" as SignalTone;
    if (alerts > 2 || overLimit > 0 || failures > 0 || summary.runtime.busy_loop) return "red" as SignalTone;
    if (alerts > 0 || (summary.counts.documents ?? 0) === 0) return "yellow" as SignalTone;
    return "green" as SignalTone;
  }, [analytics, authorized, summary]);

  const taxTone: SignalTone = !authorized ? "neutral" : (summary?.counts.open_alerts ?? 0) > 0 ? "yellow" : "green";
  const financeTone: SignalTone = !authorized ? "neutral" : Object.keys(summary?.usage?.over_limit || {}).length > 0 ? "red" : "green";
  const accountingTone: SignalTone = !authorized ? "neutral" : (summary?.counts.documents ?? 0) > 0 ? "green" : "yellow";

  const runtimeCopy = summary?.runtime.status || health?.status || "checking";
  const planName = summary?.plan.name || currentUser?.plan || "Business";

  return (
    <main className={`dcft-shell ${authorized ? "is-authorized" : "is-guest"}`}>
      <header className="nav-shell">
        <div className="brand-lockup">
          <span className="brandmark"><BrandGlyph /></span>
          <div>
            <strong>{PRODUCT_NAME}</strong>
            <span>{PRODUCT_FULL_NAME}</span>
          </div>
        </div>

        <div className="nav-actions" data-screen="login-mobile">
          {!authorized ? (
            <>
              <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label="Usuario" placeholder="Usuario" />
              <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" aria-label="Clave segura" placeholder="Clave segura" />
            </>
          ) : (
            <span className="session-badge"><ShieldCheck size={16} /> Workspace protegido</span>
          )}
          <button className="ghost-button" onClick={refresh} disabled={loading} title="Actualizar">
            <RefreshCcw size={18} />
          </button>
          {!authorized ? (
            <button className="primary-button" onClick={login} disabled={loading}>
              <Lock size={17} />
              Entrar
            </button>
          ) : (
            <button className="ghost-button" onClick={() => logout()} disabled={loading} title="Cerrar sesión">
              <LogOut size={18} />
            </button>
          )}
        </div>
      </header>

      {error ? <section className="calm-alert">{error}</section> : null}

      <section className="hero-experience" data-screen="hero-principal">
        <div className="hero-copy">
          <span className="overline">{PRODUCT_FULL_NAME}</span>
          <h1>{PRODUCT_TAGLINE}</h1>
          <p>
            Diagnóstico contable, financiero y tributario en una vista diseñada para que el empresario sienta control antes de tomar decisiones.
          </p>
          <div className="hero-trust-row">
            <span><BadgeCheck size={16} /> Gobierno humano</span>
            <span><Lock size={16} /> Sin acciones autónomas</span>
            <span><Sparkles size={16} /> Inteligencia controlada</span>
          </div>
        </div>

        <aside className="diagnosis-card" data-screen="semaforo-empresarial">
          <div className="diagnosis-top">
            <span>Semáforo empresarial</span>
            <strong>{toneLabel(signal)}</strong>
          </div>
          <TrafficLight tone={signal} />
          <div className="diagnosis-message">
            <p>{signal === "green" ? "Empresa saludable" : signal === "yellow" ? "Riesgos detectados" : signal === "red" ? "Problemas críticos" : "Diagnóstico pendiente"}</p>
            <span>
              {authorized
                ? "DCFT consolida señales reales del workspace y conserva intervención humana en decisiones sensibles."
                : "Ingresa o crea un workspace para ver el diagnóstico real de tu empresa."}
            </span>
          </div>
        </aside>
      </section>

      <section className="control-room" data-screen="dashboard-principal">
        <div className="control-room__header">
          <div>
            <span className="overline">Vista ejecutiva</span>
            <h2>Estado general de la empresa</h2>
          </div>
          <div className="runtime-chip">
            <HeartPulse size={18} />
            <span>{runtimeCopy}</span>
          </div>
        </div>

        <div className="executive-grid">
          <article className="company-card">
            <div className="company-card__top">
              <span className="company-icon"><Building2 size={24} /></span>
              <div>
                <p>Workspace</p>
                <h3>{summary?.tenant_id || "Empresa no conectada"}</h3>
              </div>
            </div>
            <div className="company-card__bottom">
              <span>Plan</span>
              <strong>{planName}</strong>
              <span>Rol</span>
              <strong>{currentUser?.role || "Acceso pendiente"}</strong>
            </div>
          </article>

          <article className="clinical-summary">
            <span>Diagnóstico DCFT</span>
            <h3>{toneLabel(signal)}</h3>
            <p>
              {signal === "green"
                ? "La lectura inicial no muestra bloqueos críticos."
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
            description="Vencimientos, alertas y revisión fiscal."
            tone={taxTone}
            metric={`${summary?.counts.open_alerts ?? 0} alertas`}
          />
          <DomainCard
            icon={<WalletCards size={22} />}
            eyebrow="Financiero"
            title="Capacidad operativa visible"
            description="Uso del plan y señales de presión."
            tone={financeTone}
            metric={`${Object.keys(summary?.usage?.over_limit || {}).length} excesos`}
          />
          <DomainCard
            icon={<FileCheck2 size={22} />}
            eyebrow="Contable"
            title="Evidencia documental"
            description="Documentos registrados para trazabilidad."
            tone={accountingTone}
            metric={`${summary?.counts.documents ?? 0} documentos`}
          />
        </div>
      </section>

      <section className="onboarding-premium" data-screen="onboarding-premium">
        <div>
          <span className="overline">Activación premium</span>
          <h2>Crear un espacio de diagnóstico</h2>
          <p>El onboarding debe sentirse como entrar a una banca privada: poco ruido, pasos claros y seguridad percibida.</p>
        </div>

        <div className="onboarding-card">
          <div className="onboarding-steps">
            {(onboardingStatus?.steps || ["Crear workspace", "Configurar administrador", "Registrar primera señal"]).slice(0, 3).map((step, index) => (
              <span key={step}><CheckCircle2 size={16} /> {index + 1}. {step}</span>
            ))}
          </div>
          <div className="onboarding-form">
            <input
              value={onboardingForm.tenant_name}
              onChange={(event) => setOnboardingForm({ ...onboardingForm, tenant_name: event.target.value })}
              aria-label="Empresa"
              placeholder="Nombre de empresa"
              disabled={loading || authorized}
            />
            <input
              value={onboardingForm.admin_username}
              onChange={(event) => setOnboardingForm({ ...onboardingForm, admin_username: event.target.value })}
              aria-label="Administrador"
              placeholder="Administrador"
              disabled={loading || authorized}
            />
            <input
              value={onboardingForm.admin_password}
              onChange={(event) => setOnboardingForm({ ...onboardingForm, admin_password: event.target.value })}
              type="password"
              aria-label="Clave inicial"
              placeholder="Clave inicial"
              disabled={loading || authorized}
            />
            <select
              value={onboardingForm.plan}
              onChange={(event) => setOnboardingForm({ ...onboardingForm, plan: event.target.value })}
              aria-label="Plan"
              disabled={loading || authorized}
            >
              {(plans.length ? plans : onboardingStatus?.plans || []).map((plan) => (
                <option key={plan.id} value={plan.id}>{plan.name}</option>
              ))}
            </select>
            <button className="primary-button" onClick={createTenant} disabled={loading || authorized || !onboardingStatus?.signup_enabled}>
              <UserPlus size={17} />
              Crear diagnóstico
              <ArrowRight size={17} />
            </button>
          </div>
        </div>
      </section>

      <footer className="quiet-footer">
        <span>API: {API_URL}</span>
        <span>{authorized ? `Tenant: ${summary?.tenant_id || currentUser?.tenant_id || "activo"}` : "Validación humana pendiente"}</span>
      </footer>
    </main>
  );
}

export default App;
