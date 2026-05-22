import {
  Activity,
  AlertTriangle,
  BadgeCheck,
  BookOpen,
  Brain,
  BriefcaseBusiness,
  CheckCircle2,
  FileText,
  Lock,
  RefreshCcw,
  ShieldCheck,
  Sparkles,
  Workflow
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { API_URL, post, request, type Session } from "./lib/api";

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
  runtime: {
    status: string;
    busy_loop: boolean;
    ai_pipeline: string;
    ocr_pipeline: string;
    database?: { status: string; backend: string };
  };
  boundaries: string[];
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
  const [token, setToken] = useState<string>("");
  const [health, setHealth] = useState<Health | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState("dcft_admin");
  const [password, setPassword] = useState("dcft_local_admin_change_me");

  const authorized = token.length > 0;

  const addLog = useCallback((item: LogItem) => {
    setLogs((current) => [item, ...current].slice(0, 8));
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const healthBody = await request<Health>("/health");
      setHealth(healthBody);
      if (token) {
        setSummary(await request<Summary>("/dashboard/summary", {}, token));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "unknown_error");
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
      addLog({ label: "auth", status: "active", detail: "local bootstrap session" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "login_failed");
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
      setError(err instanceof Error ? err.message : "action_failed");
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
      setError(err instanceof Error ? err.message : "governance_flow_failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [refresh]);

  const moduleRows = useMemo(() => Object.entries(health?.modules || {}), [health]);

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
          <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label="Username" />
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" aria-label="Password" />
          <button className="icon-button" onClick={refresh} disabled={loading} title="Refresh">
            <RefreshCcw size={18} />
          </button>
          <button className="primary" onClick={login} disabled={loading || authorized}>
            <Lock size={17} />
            {authorized ? "Session active" : "Login local"}
          </button>
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

      <section className="action-grid">
        <button onClick={() => runAction("alert")} disabled={!authorized || loading}><AlertTriangle />Create alert</button>
        <button onClick={() => runAction("recommendation")} disabled={!authorized || loading}><Sparkles />Recommendation</button>
        <button onClick={() => runAction("document")} disabled={!authorized || loading}><FileText />Register document</button>
        <button onClick={() => runAction("ai")} disabled={!authorized || loading}><Brain />AI blocked check</button>
        <button onClick={runGovernanceFlow} disabled={!authorized || loading}><Workflow />Governance flow</button>
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