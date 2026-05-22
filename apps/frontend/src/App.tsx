import {
  Activity,
  AlertTriangle,
  BadgeCheck,
  BarChart3,
  BookOpen,
  Brain,
  BriefcaseBusiness,
  CheckCircle2,
  CreditCard,
  FileText,
  Lock,
  LogOut,
  RefreshCcw,
  ShieldCheck,
  Sparkles,
  UserPlus,
  Workflow
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { API_URL, ApiError, patch, post, request, type Session } from "./lib/api";

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
  activation?: {
    has_alerts: boolean;
    has_documents: boolean;
    has_workflows: boolean;
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
  modules: Record<string, string>;
  security_warnings: string[];
};

type LogItem = {
  label: string;
  status: string;
  detail: string;
};

type CurrentUser = {
  username: string;
  tenant_id: string;
  role: string;
  plan: string;
  permissions: string[];
};

const actionPayloads = {
  alert: { title: "Vencimiento operativo revisable", severity: "high", source: "dashboard" },
  recommendation: {
    category: "tax",
    objective: "Revisar obligaciones del periodo",
    facts: { period: "2026-05", source: "local_dashboard" }
  },
  document: {
    filename: "factura-local-demo.pdf",
    source: "local_dashboard",
    content_type: "application/pdf",
    size_bytes: 2048
  },
  ai: {
    objective: "Evaluar flujo de caja",
    input_summary: "Solicitud local sin proveedor externo",
    constraints: ["no external ai", "human review"]
  }
};

function Metric({ label, value, tone }: { label: string; value: string | number; tone: string }) {
  return (
    <div className={`panel metric ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem("dcft_token") || "");
  const [health, setHealth] = useState<Health | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [plans, setPlans] = useState<PlanDefinition[]>([]);
  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [selectedPlan, setSelectedPlan] = useState("business_basic");
  const [onboardingForm, setOnboardingForm] = useState({
    tenant_name: "Mi empresa",
    tenant_id: "",
    admin_username: "",
    admin_password: "",
    plan: "business_basic"
  });

  const authorized = token.length > 0;

  const addLog = useCallback((item: LogItem) => {
    setLogs((current) => [item, ...current].slice(0, 8));
  }, []);

  const can = useCallback((permission: string) => {
    return currentUser?.permissions.includes("*") || currentUser?.permissions.includes(permission) || false;
  }, [currentUser]);

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
    addLog({ label: "auth", status: "logged out", detail: reason });
  }, [addLog]);

  const handleError = useCallback((err: unknown, fallback: string) => {
    if (err instanceof ApiError) {
      if (err.status === 401) {
        logout("session expired or invalid");
        return "Session expired or invalid. Login again.";
      }
      if (err.status === 403) {
        return "Permission denied by backend RBAC.";
      }
      if (err.status === 429) {
        return "Rate limit active. Slow down and retry shortly.";
      }
      if (err.status === 0) {
        return `${err.message}. Runtime is degraded.`;
      }
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
        setSelectedPlan(dashboard.plan.id);
        setAnalytics(analyticsBody);
      }
    } catch (err) {
      setError(handleError(err, "unknown_error"));
    } finally {
      setLoading(false);
    }
  }, [token]);

  const login = async () => {
    setLoading(true);
    setError("");
    try {
      const session = await post<Session>("/auth/login", {
        username,
        password
      });
      setToken(session.access_token);
      localStorage.setItem("dcft_token", session.access_token);
      addLog({ label: "auth", status: "active", detail: "local bootstrap session" });
    } catch (err) {
      setError(handleError(err, "login_failed"));
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
      addLog({ label: "onboarding", status: "created", detail: `${result.tenant_id} on ${result.plan.name}` });
    } catch (err) {
      setError(handleError(err, "onboarding_failed"));
    } finally {
      setLoading(false);
    }
  };

  const changePlan = async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const result = await patch<{ plan: string; over_limit: Record<string, { current: number; limit: number }> }>(
        "/subscriptions/current",
        { plan: selectedPlan },
        token
      );
      const overLimit = Object.keys(result.over_limit || {}).length;
      addLog({
        label: "subscription",
        status: result.plan,
        detail: overLimit ? `${overLimit} resources exceed the selected plan.` : "plan updated with current usage inside limits"
      });
      await refresh();
    } catch (err) {
      setError(handleError(err, "plan_change_failed"));
    } finally {
      setLoading(false);
    }
  };

  const runAction = async (kind: "alert" | "recommendation" | "document" | "ai") => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      if (kind === "alert") {
        const record = await post<{ status: string }>("/alerts", actionPayloads.alert, token);
        addLog({ label: "alert", status: record.status, detail: "high risk alert recorded" });
      }
      if (kind === "recommendation") {
        const record = await post<{ recommendation: string }>("/recommendations", actionPayloads.recommendation, token);
        addLog({ label: "recommendation", status: "ready", detail: record.recommendation });
      }
      if (kind === "document") {
        const record = await post<{ ingestion: { ocr_status: string } }>("/documents/ingest", actionPayloads.document, token);
        addLog({ label: "document", status: record.ingestion.ocr_status, detail: "metadata registered" });
      }
      if (kind === "ai") {
        const record = await post<{ status: string; explanation: string }>("/ai/requests", actionPayloads.ai, token);
        addLog({ label: "ai", status: record.status, detail: record.explanation });
      }
      await refresh();
    } catch (err) {
      setError(handleError(err, "action_failed"));
    } finally {
      setLoading(false);
    }
  };

  const runGovernanceFlow = async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const approval = await post<{ id: string; status: string }>(
        "/governance/approval-requests",
        { scope: "workflow", action: "advance controlled review", risk: "high", reason: "dashboard controlled run" },
        token
      );
      await post(`/governance/approval-requests/${approval.id}/decision`, { decision: "approved", reason: "human reviewed" }, token);
      const workflowRun = await post<{ id: string }>("/workflows", {
        name: "Cierre mensual revisable",
        objective: "Preparar control local",
        risk: "high",
        steps: ["validar evidencia", "emitir resumen"]
      }, token);
      const advanced = await post<{ status: string; audit_note: string }>(
        `/workflows/${workflowRun.id}/advance`,
        { checkpoint_acknowledged: true, approval_request_id: approval.id, note: "checkpoint approved" },
        token
      );
      addLog({ label: "workflow", status: advanced.status, detail: advanced.audit_note });
      await refresh();
    } catch (err) {
      setError(handleError(err, "governance_flow_failed"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [refresh]);

  const moduleRows = useMemo(() => Object.entries(health?.modules || {}), [health]);
  const usageRows = useMemo(() => {
    const limits = summary?.usage?.limits || summary?.plan.limits || {};
    return Object.entries(limits).map(([name, limit]) => ({
      name,
      current: summary?.usage?.current?.[name] ?? 0,
      limit
    }));
  }, [summary]);
  const activationRows = [
    { label: "Onboarding", active: analytics?.activation.onboarding_completed || false },
    { label: "Business signal", active: analytics?.activation.first_business_signal || false },
    { label: "Workflow", active: analytics?.activation.first_workflow_created || false }
  ];

  return (
    <main className="min-h-screen bg-mist text-ink">
      <header className="topbar">
        <div className="brand">
          <span className="brandmark"><BriefcaseBusiness size={22} /></span>
          <div>
            <h1>DCFT</h1>
            <p>Doctor Contable Financiero Tributario</p>
          </div>
        </div>
        <div className="actions">
          <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label="Username" placeholder="Username" />
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" aria-label="Password" placeholder="Password" />
          <button className="icon-button" onClick={refresh} disabled={loading} title="Refresh">
            <RefreshCcw size={18} />
          </button>
          <button className="primary" onClick={login} disabled={loading || authorized}>
            <Lock size={17} />
            {authorized ? "Session active" : "Login local"}
          </button>
          {authorized ? (
            <button className="icon-button" onClick={() => logout()} disabled={loading} title="Logout">
              <LogOut size={18} />
            </button>
          ) : null}
        </div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">Local enterprise base</p>
          <h2>{summary?.product || "DCFT operational console"}</h2>
          <p>{summary?.tagline || "Backend, governance, audit, and dashboard running locally."}</p>
        </div>
        <div className="hero-status">
          <BadgeCheck size={20} />
          <span>{health?.status || "checking"}</span>
        </div>
      </section>

      {error ? <div className="error"><AlertTriangle size={18} />{error}</div> : null}

      <section className="product-grid">
        <div className="panel">
          <div className="panel-title">
            <UserPlus size={18} />
            <h3>Onboarding</h3>
          </div>
          <div className="form-grid">
            <input
              value={onboardingForm.tenant_name}
              onChange={(event) => setOnboardingForm({ ...onboardingForm, tenant_name: event.target.value })}
              aria-label="Tenant name"
              placeholder="Business name"
              disabled={loading || authorized}
            />
            <input
              value={onboardingForm.tenant_id}
              onChange={(event) => setOnboardingForm({ ...onboardingForm, tenant_id: event.target.value.toLowerCase() })}
              aria-label="Tenant id"
              placeholder="tenant-id optional"
              disabled={loading || authorized}
            />
            <input
              value={onboardingForm.admin_username}
              onChange={(event) => setOnboardingForm({ ...onboardingForm, admin_username: event.target.value })}
              aria-label="Admin username"
              placeholder="admin username"
              disabled={loading || authorized}
            />
            <input
              value={onboardingForm.admin_password}
              onChange={(event) => setOnboardingForm({ ...onboardingForm, admin_password: event.target.value })}
              type="password"
              aria-label="Admin password"
              placeholder="secure password"
              disabled={loading || authorized}
            />
            <select
              value={onboardingForm.plan}
              onChange={(event) => setOnboardingForm({ ...onboardingForm, plan: event.target.value })}
              aria-label="Onboarding plan"
              disabled={loading || authorized}
            >
              {(plans.length ? plans : onboardingStatus?.plans || []).map((plan) => (
                <option key={plan.id} value={plan.id}>{plan.name}</option>
              ))}
            </select>
            <button className="primary" onClick={createTenant} disabled={loading || authorized || !onboardingStatus?.signup_enabled}>
              <UserPlus size={17} />
              Create workspace
            </button>
          </div>
          <div className="empty-state">
            {(onboardingStatus?.steps || ["Create workspace", "Login", "Record first operational signal"]).map((step) => (
              <span key={step}>{step}</span>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-title">
            <CreditCard size={18} />
            <h3>Plans</h3>
          </div>
          <div className="plan-list">
            {(plans.length ? plans : summary?.plan ? [summary.plan as PlanDefinition] : []).map((plan) => (
              <div className={`plan-card ${summary?.plan.id === plan.id ? "active" : ""}`} key={plan.id}>
                <strong>{plan.name}</strong>
                <span>{Object.entries(plan.limits).map(([key, value]) => `${key}: ${value}`).join(" · ")}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="metrics">
        <Metric label="Alerts" value={summary?.counts.open_alerts ?? "-"} tone="blue" />
        <Metric label="Recommendations" value={summary?.counts.recommendations ?? "-"} tone="teal" />
        <Metric label="Documents" value={summary?.counts.documents ?? "-"} tone="amber" />
        <Metric label="Workflows" value={summary?.counts.workflows ?? "-"} tone="slate" />
      </section>

      <section className="layout">
        <div className="panel wide">
          <div className="panel-title">
            <Activity size={18} />
            <h3>Runtime</h3>
          </div>
          <div className="runtime-grid">
            <span>Status</span><strong>{summary?.runtime.status || "unknown"}</strong>
            <span>Busy loop</span><strong>{String(summary?.runtime.busy_loop ?? false)}</strong>
            <span>Database</span><strong>{summary?.runtime.database?.backend || "pending"}</strong>
            <span>AI</span><strong>{summary?.runtime.ai_pipeline || "provider disabled"}</strong>
            <span>OCR</span><strong>{summary?.runtime.ocr_pipeline || "placeholder disabled"}</strong>
          <span>Production ready</span><strong>{String(health?.production_ready ?? false)}</strong>
            <span>Role</span><strong>{currentUser?.role || "anonymous"}</strong>
            <span>Tenant</span><strong>{currentUser?.tenant_id || "none"}</strong>
          </div>
        </div>

        <div className="panel">
          <div className="panel-title">
            <ShieldCheck size={18} />
            <h3>Boundaries</h3>
          </div>
          <ul className="clean-list">
            {(summary?.boundaries || ["No autonomous official actions.", "Human review required."]).map((item) => (
              <li key={item}><CheckCircle2 size={15} />{item}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="layout">
        <div className="panel">
          <div className="panel-title">
            <CreditCard size={18} />
            <h3>Subscription</h3>
          </div>
          <div className="subscription-row">
            <div>
              <span>Current plan</span>
              <strong>{summary?.plan.name || "login required"}</strong>
            </div>
            <select value={selectedPlan} onChange={(event) => setSelectedPlan(event.target.value)} disabled={!authorized || loading || !can("subscriptions:manage")}>
              {plans.map((plan) => (
                <option key={plan.id} value={plan.id}>{plan.name}</option>
              ))}
            </select>
            <button className="primary" onClick={changePlan} disabled={!authorized || loading || !can("subscriptions:manage")}>
              Update plan
            </button>
          </div>
          <div className="usage-list">
            {usageRows.map((item) => (
              <div key={item.name} className={summary?.usage?.over_limit?.[item.name] ? "over" : ""}>
                <span>{item.name}</span>
                <strong>{item.current} / {item.limit}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-title">
            <BarChart3 size={18} />
            <h3>Product analytics</h3>
          </div>
          <div className="analytics-grid">
            <div><span>Events</span><strong>{analytics?.events_total ?? "-"}</strong></div>
            <div><span>Failures</span><strong>{analytics?.failures_total ?? "-"}</strong></div>
          </div>
          <div className="empty-state">
            {activationRows.map((item) => (
              <span className={item.active ? "done" : ""} key={item.label}>{item.label}: {item.active ? "done" : "pending"}</span>
            ))}
          </div>
        </div>
      </section>

      <section className="action-grid">
        <button onClick={() => runAction("alert")} disabled={!authorized || loading || !can("alerts:write")}><AlertTriangle />Create alert</button>
        <button onClick={() => runAction("recommendation")} disabled={!authorized || loading || !can("recommendations:write")}><Sparkles />Recommendation</button>
        <button onClick={() => runAction("document")} disabled={!authorized || loading || !can("documents:write")}><FileText />Register document</button>
        <button onClick={() => runAction("ai")} disabled={!authorized || loading || !can("ai:request")}><Brain />AI blocked check</button>
        <button onClick={runGovernanceFlow} disabled={!authorized || loading || !can("governance:decide") || !can("workflows:high_risk")}><Workflow />Governance flow</button>
        <button onClick={() => request("/education/exercises").then(() => addLog({ label: "education", status: "ready", detail: "exercise registry available" }))} disabled={loading}><BookOpen />Education registry</button>
      </section>

      <section className="layout">
        <div className="panel">
          <div className="panel-title">
            <ShieldCheck size={18} />
            <h3>Modules</h3>
          </div>
          <div className="module-list">
            {moduleRows.map(([name, value]) => (
              <div key={name}><span>{name}</span><strong>{value}</strong></div>
            ))}
          </div>
        </div>
        <div className="panel">
          <div className="panel-title">
            <Activity size={18} />
            <h3>Audit trail</h3>
          </div>
          <div className="log-list">
            {logs.length === 0 ? <p>No local actions yet.</p> : logs.map((item, index) => (
              <div key={`${item.label}-${index}`}>
                <span>{item.label}</span>
                <strong>{item.status}</strong>
                <p>{item.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer>
        <span>API: {API_URL}</span>
        <span>Tenant: {summary?.tenant_id || "login required"}</span>
      </footer>
    </main>
  );
}

export default App;
