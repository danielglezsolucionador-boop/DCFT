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
  Eye,
  EyeOff,
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
import { type CSSProperties, type FormEvent, type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { API_URL, ApiError, patch, post, request, type Session } from "./lib/api";

type SignalTone = "green" | "yellow" | "red" | "neutral";
type PanelKey = "diagnostico" | "reportes" | "doctor" | "ejercicios" | "perfil" | "premium" | "onboarding" | "sunat" | "empresa" | "admin" | "beneficios";

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
  premium?: boolean;
  payment_required?: boolean;
  internal?: boolean;
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
  prices?: PlanPrices;
};

type PlanPrices = {
  currency: string;
  monthly: { amount_cents: number; label: string };
  annual: { amount_cents: number; label: string };
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
  access_token?: string;
  token_type?: string;
  existing_company?: boolean;
  ruc_status?: ExistingRucStatus;
  plan?: PlanDefinition;
  plan_requested?: string;
  billing_cycle?: string;
  subscription_status?: string;
  checkout_url?: string | null;
  message?: string;
  payment?: CheckoutStatus & { checkout?: CheckoutResult | null };
  trial?: {
    status: string;
    started_at?: string | null;
    ends_at?: string | null;
    days?: number;
  };
  company?: Company | null;
  workspace?: Workspace | null;
  context?: ActiveContext | null;
  email_verification?: {
    required: boolean;
    email_verified: boolean;
    sent: boolean;
    email_provider_missing: boolean;
    message: string;
  };
  next_steps: string[];
};

type ExistingRucStatus = {
  exists: boolean;
  ruc: string;
  usuario_sol_masked?: string | null;
  has_sunat_connection: boolean;
  subscription_status: "pending" | "active" | "expired" | "none" | string;
  plan?: "mype" | "premium" | null;
  checkout_status?: string | null;
  checkout_url?: string | null;
  can_continue: boolean;
  can_update_sol: boolean;
  can_checkout: boolean;
};

type EmailVerificationResult = {
  email_verified: boolean;
  email_provider_missing: boolean;
  sent: boolean;
  message: string;
};

type CheckoutStatus = {
  provider?: string | null;
  payment_provider_missing: boolean;
  payment_public_key_missing?: boolean;
  payment_webhook_missing?: boolean;
  provider_supported?: boolean;
  message: string;
  current_plan?: string;
  payment_status?: string;
  payment_required?: boolean;
  premium?: boolean;
  internal?: boolean;
  plans: Record<string, PlanPrices>;
  subscription?: {
    plan?: string;
    status?: string;
    billing_cycle?: string | null;
    interval?: string | null;
    provider?: string | null;
    started_at?: string | null;
    ends_at?: string | null;
  } | null;
};

type CheckoutResult = {
  checkout_url?: string | null;
  payment_provider_missing?: boolean;
  message?: string;
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
  premium?: boolean;
  payment_required?: boolean;
  internal?: boolean;
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
  real_sunat_session?: boolean;
  read_only?: boolean;
  remote_actions_enabled?: boolean;
  pilot_requires_auxiliary_user?: boolean;
  credential_capture_enabled?: boolean;
  credential_storage_enabled?: boolean;
};

type SunatCredentialStatus = {
  id?: string | null;
  tenant_id?: string | null;
  empresa_id?: string | null;
  workspace_id?: string | null;
  status: string;
  ruc_masked?: string | null;
  sunat_username_masked?: string | null;
  read_only: boolean;
  remote_actions_enabled: boolean;
  real_sunat_session: boolean;
  real_connector_enabled: boolean;
  credential_capture_enabled: boolean;
  credential_storage_enabled: boolean;
  encrypted_credential_storage: boolean;
  last_validated_at?: string | null;
  disconnected_at?: string | null;
};

type SunatReadonlyRun = {
  id: string;
  status: string;
  connector_status: string;
  real_sunat_session: boolean;
  summary?: Record<string, unknown>;
  started_at?: string | null;
  completed_at?: string | null;
};

type SunatPermissionCheck = {
  id: string;
  permission_name: string;
  permission_path: string;
  permission_type: string;
  is_available: boolean;
  is_recommended: boolean;
  is_sensitive: boolean;
  can_read: boolean;
  can_execute: boolean;
  status: string;
  metadata?: { missing_message?: string; sensitive_message?: string };
};

type SunatFinding = {
  id: string;
  severity: string;
  category: string;
  title: string;
  message: string;
  status: string;
};

type SunatReadonlyStatus = {
  flags: Record<string, unknown>;
  latest_run: SunatReadonlyRun | null;
  can_start_new_read: boolean;
};

type SunatPermissionsResponse = {
  run: SunatReadonlyRun | null;
  recommended_permissions: string[];
  permissions: SunatPermissionCheck[];
  missing: SunatPermissionCheck[];
  additional: SunatPermissionCheck[];
  sensitive: SunatPermissionCheck[];
};

type SunatDiagnosisResponse = {
  run: SunatReadonlyRun | null;
  summary: Record<string, unknown>;
  findings: SunatFinding[];
  prioritized_findings: SunatFinding[];
};

type SunatApiCredential = {
  id: string;
  client_id_masked: string;
  status: string;
  services: Record<string, { status?: string; last_error?: string; period?: string }>;
  token_configured: boolean;
  token_expires_at?: string | null;
  last_test_status?: string | null;
  last_error?: string | null;
  sensitive_actions_enabled: boolean;
};

type SunatApiStatus = {
  api_configured: boolean;
  sol_configured: boolean;
  credential: SunatApiCredential | null;
  status: string;
  read_only: boolean;
  sensitive_actions_enabled: boolean;
  permission_guide?: { permission: string; copy: string; warning: string };
};

type SunatApiDiscoveryService = {
  service: string;
  label: string;
  official_api_available: boolean;
  requires_api_credentials?: boolean;
  requires_sol_credentials?: boolean;
  requires_sire?: boolean;
  read_only: boolean;
  status: string;
};

type SunatApiDiscovery = {
  services: SunatApiDiscoveryService[];
  api_configured: boolean;
  sol_configured: boolean;
  read_only: boolean;
  sensitive_actions_enabled: boolean;
};

type OnboardingVideo = {
  id: string;
  title: string;
  description: string;
  placeholder: boolean;
  duration_hint: string;
  seen: boolean;
  button_label: string;
  status?: "pending" | "available";
  written_guide?: string;
};

type AccessMode = "student" | "business" | "admin";
type DiagnosticScenario = "pending" | "green" | "yellow" | "red";
type ExerciseCategory = "Contabilidad" | "Finanzas" | "Tributación";

type StudentExercise = {
  id: string;
  category: ExerciseCategory;
  level: "Basico" | "Intermedio";
  title: string;
  statement: string;
  guidedSteps: string[];
  expectedAnswer: string;
  explanation: string;
};

type StudentDoctorQuota = {
  user_id: string;
  tenant_id: string;
  month_key: string;
  year: number;
  month: number;
  questions_used: number;
  questions_limit: number;
  questions_remaining: number;
  timestamps: string[];
  last_question?: string | null;
  status: string;
  created_at?: string | null;
  updated_at?: string | null;
  last_asked_at?: string | null;
};

type StudentDoctorStatus = {
  doctor_name: string;
  available: boolean;
  ai_provider_missing: boolean;
  provider?: string | null;
  model?: string | null;
  quota: StudentDoctorQuota;
  message: string;
};

type StudentDoctorAnswer = {
  doctor_name: string;
  answer: string;
  provider: string;
  model?: string | null;
  quota: StudentDoctorQuota;
  educational_disclaimer: string;
};

type TaxAIAnswer = {
  answer: string;
  provider?: string | null;
  model?: string | null;
  ai_provider_missing: boolean;
  configured: boolean;
  educational_disclaimer: string;
};

type PlanContableItem = {
  code: string;
  name: string;
  categoryName: string;
  use: string;
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
const PRODUCT_PROMISE = "Diagnóstico, prevención y tranquilidad para la salud empresarial.";

const NAV_ITEMS = [
  { href: "#dashboard", label: "Inicio", icon: Home },
  { href: "#diagnostic", label: "Diagnóstico", icon: Search },
  { href: "#reports", label: "Reportes", icon: FileText },
  { href: "#exercises", label: "Ejercicios", icon: ClipboardList },
  { href: "#profile", label: "Perfil", icon: UserCircle }
];

const DESKTOP_NAV_ITEMS: Array<{ label: string; icon: typeof Home; href?: string; panel?: PanelKey }> = [
  { href: "#dashboard", label: "Inicio", icon: Home },
  { panel: "diagnostico", label: "Diagnóstico", icon: Search },
  { panel: "diagnostico", label: "Alertas", icon: BellRing },
  { panel: "reportes", label: "Reportes", icon: FileText },
  { panel: "doctor", label: "Doctor", icon: Stethoscope },
  { panel: "empresa", label: "Empresas", icon: Building2 },
  { panel: "admin", label: "Admin CEO", icon: Settings2 },
  { panel: "perfil", label: "Perfil", icon: UserCircle }
];

function toneLabel(tone: SignalTone) {
  if (tone === "green") return "Operativo";
  if (tone === "yellow") return "Atención";
  if (tone === "red") return "Crítico";
  return "Pendiente";
}

function businessStatusLabel(tone: SignalTone) {
  if (tone === "green") return "En orden";
  if (tone === "yellow") return "Atención";
  if (tone === "red") return "Riesgo";
  return "Pendiente";
}

function trafficColorLabel(tone: SignalTone) {
  if (tone === "green") return "Verde";
  if (tone === "yellow") return "Ámbar";
  if (tone === "red") return "Rojo";
  return "Pendiente";
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
  const normalized = value.toLowerCase();
  const labels: Record<string, string> = {
    free: "Gratis",
    student: "Estudiante",
    mype: "MYPE",
    premium: "Premium",
    internal: "Internal CEO",
    admin: "Admin CEO",
    consultas: "Consultas",
    reportes: "Reportes",
    basic_dashboard: "Panel básico",
    practice_workflows: "Práctica guiada",
    advanced_recommendations: "Recomendaciones avanzadas",
    deep_simulations: "Simulaciones avanzadas",
    premium_modules_visible_locked: "Módulos Premium visibles bloqueados",
    workspace: "Espacio de trabajo",
    workspaces: "Espacios de trabajo",
    onboarding_completed: "Primeros pasos completos",
    company_registered: "Empresa registrada",
    ruc_validated: "RUC validado",
    videos_seen: "Videos vistos",
    sunat_auxiliary_prepared: "Usuario SOL configurado",
    diagnosis_pending: "Diagnóstico inicial pendiente",
    trial_active: "Prueba activa"
  };
  if (labels[normalized]) return labels[normalized];
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter: string) => letter.toUpperCase());
}

function planDisplayPrice(planId: string) {
  if (planId === "student") return "S/ 0";
  if (planId === "mype") return "S/ 89 / mes · S/ 890 / año";
  if (planId === "premium") return "S/ 199 / mes · S/ 1,990 / año";
  return "";
}

function planPriceOptions(planId: string, prices?: PlanPrices) {
  if (prices) {
    return [prices.monthly.label, prices.annual.label].filter(Boolean);
  }
  if (planId === "student") return ["S/ 0"];
  if (planId === "mype") return ["S/ 89 / mes", "S/ 890 / año"];
  if (planId === "premium") return ["S/ 199 / mes", "S/ 1,990 / año"];
  return [];
}

function planDisplayDescription(planId: string) {
  if (planId === "student") return "Plan estudiante gratis para practicar ejercicios y ver soluciones guiadas.";
  if (planId === "mype") return "Camino empresa para micro y pequeñas empresas que necesitan vigilancia básica.";
  if (planId === "premium") return "Camino empresa para diagnóstico, alertas, médico de cabecera y análisis avanzado.";
  return "Plan disponible para operar DCFT.";
}

const DOCTOR_AVATAR_SRC = "/doctor-ceo-placeholder-premium.svg";
const SUNAT_SAFE_COPY = "Ingresa tu RUC, Usuario SOL y Clave SOL para que DCFT pueda consultar tu información tributaria y generar diagnóstico automático. DCFT no mostrará ni devolverá tu Clave SOL; se guardará cifrada y podrás desconectar SUNAT cuando quieras.";
const SUNAT_CONSENT_ERROR = "Debes aceptar el consentimiento para guardar el acceso SUNAT SOL.";
const SUNAT_RECOMMENDED_QUERY_PERMISSIONS = [
  "Mis Declaraciones y pagos > Consultas",
  "Mis Declaraciones y pagos > Declaraciones y Pagos",
  "Mis Declaraciones y pagos > Consulta de transferencia dólares",
  "Mi RUC y Otros Registros > Mis Datos del RUC",
  "Mi RUC y Otros Registros > RUC",
  "Mi RUC y Otros Registros > Ficha RUC",
  "Mi RUC y Otros Registros > Captura de Acuse de Recibo",
  "Reporte Tributario y Aduanero > Reporte",
  "Reporte Tributario y Aduanero > Consulto mis reportes",
  "T-Registro > Consultas",
  "T-Registro > Registro de derechohabientes",
  "T-Registro > Consulta individual",
  "Envio Reporte Tributario > Envío Reporte Tributario",
  "Guía de Remisión Electrónica > Consulta de GRE",
  "Guía de Remisión Electrónica > Consulta de obligados",
  "Comprobantes de pago > Consulta de Validez de Comprobantes de Pago",
  "Comprobantes de pago > Consulta Integrada de Comprobantes de Pago"
];
const EXERCISE_CATEGORIES: Array<"Todos" | ExerciseCategory> = ["Todos", "Contabilidad", "Finanzas", "Tributación"];

const STUDENT_EXERCISES: StudentExercise[] = [
  {
    id: "cont-ventas-igv",
    category: "Contabilidad",
    level: "Basico",
    title: "Registro de venta con IGV",
    statement: "Una empresa vende mercaderia por S/ 1,180 incluido IGV. Registra la venta y separa base imponible e impuesto.",
    guidedSteps: [
      "Identifica si el importe incluye IGV.",
      "Divide el total entre 1.18 para hallar la base.",
      "Calcula el IGV como diferencia entre total y base.",
      "Registra cuentas por cobrar, ventas e IGV por pagar."
    ],
    expectedAnswer: "Base S/ 1,000; IGV S/ 180; cargo a cuentas por cobrar S/ 1,180; abono a ventas S/ 1,000 e IGV por pagar S/ 180.",
    explanation: "La venta gravada separa ingreso e impuesto. El IGV no es ingreso de la empresa; queda como obligacion tributaria."
  },
  {
    id: "cont-compra-credito",
    category: "Contabilidad",
    level: "Basico",
    title: "Compra al credito",
    statement: "Se compra inventario por S/ 590 incluido IGV y se pagará a 30 días.",
    guidedSteps: [
      "Separa la base imponible del IGV.",
      "Reconoce el inventario como activo.",
      "Reconoce el credito fiscal si cumple requisitos.",
      "Registra la cuenta por pagar al proveedor."
    ],
    expectedAnswer: "Inventario S/ 500; IGV credito fiscal S/ 90; cuentas por pagar S/ 590.",
    explanation: "La compra al credito no afecta caja al inicio. Aumenta inventario, credito fiscal y deuda con proveedor."
  },
  {
    id: "cont-depreciacion",
    category: "Contabilidad",
    level: "Intermedio",
    title: "Depreciacion mensual",
    statement: "Un equipo cuesta S/ 12,000 y se depreciara en 5 anos por metodo lineal.",
    guidedSteps: [
      "Convierte los 5 anos en 60 meses.",
      "Divide el costo entre la vida util mensual.",
      "Reconoce gasto y depreciacion acumulada.",
      "Verifica que no se supere el costo del activo."
    ],
    expectedAnswer: "Depreciacion mensual S/ 200; gasto por depreciacion S/ 200 contra depreciacion acumulada S/ 200.",
    explanation: "El metodo lineal reparte el costo del activo durante su vida util de forma uniforme."
  },
  {
    id: "cont-caja-chica",
    category: "Contabilidad",
    level: "Basico",
    title: "Reposicion de caja chica",
    statement: "Caja chica tiene comprobantes por S/ 320 y saldo en efectivo de S/ 80. El fondo fijo aprobado es S/ 400.",
    guidedSteps: [
      "Confirma el monto total del fondo fijo.",
      "Suma comprobantes y efectivo disponible.",
      "Calcula la reposicion necesaria.",
      "Clasifica los comprobantes por gasto."
    ],
    expectedAnswer: "Reposicion S/ 320 para volver al fondo fijo de S/ 400.",
    explanation: "La caja chica se repone por los gastos sustentados; el saldo final vuelve al monto autorizado."
  },
  {
    id: "cont-cierre-gasto",
    category: "Contabilidad",
    level: "Intermedio",
    title: "Devengo de servicio pendiente",
    statement: "La empresa recibio un servicio de asesoria en junio por S/ 900 mas IGV, pero la factura llegara en julio.",
    guidedSteps: [
      "Determina si el servicio ya fue recibido.",
      "Aplica el principio de devengo.",
      "Reconoce el gasto del periodo.",
      "Registra la obligacion pendiente."
    ],
    expectedAnswer: "Registrar gasto de asesoría S/ 900 y cuenta por pagar provisionada. El IGV se reconoce según sustento tributario aplicable.",
    explanation: "El gasto pertenece al periodo en que se recibe el servicio, aunque el documento llegue después."
  },
  {
    id: "fin-flujo-caja",
    category: "Finanzas",
    level: "Basico",
    title: "Flujo de caja semanal",
    statement: "Ingresos previstos S/ 4,500; pagos a proveedores S/ 2,800; planilla S/ 1,200; alquiler S/ 700.",
    guidedSteps: [
      "Suma todos los egresos previstos.",
      "Resta egresos a ingresos.",
      "Identifica si hay excedente o faltante.",
      "Define una accion preventiva."
    ],
    expectedAnswer: "Egresos S/ 4,700; flujo neto -S/ 200; se necesita cubrir o reprogramar S/ 200.",
    explanation: "El flujo de caja mira entradas y salidas reales de dinero, no solo utilidad contable."
  },
  {
    id: "fin-margen-bruto",
    category: "Finanzas",
    level: "Basico",
    title: "Margen bruto",
    statement: "Ventas S/ 10,000 y costo de ventas S/ 6,200.",
    guidedSteps: [
      "Resta costo de ventas a ventas.",
      "Divide la utilidad bruta entre ventas.",
      "Convierte el resultado a porcentaje.",
      "Interpreta el margen para decisiones."
    ],
    expectedAnswer: "Utilidad bruta S/ 3,800; margen bruto 38%.",
    explanation: "El margen bruto indica cuanto queda para cubrir gastos operativos, impuestos y utilidad."
  },
  {
    id: "fin-punto-equilibrio",
    category: "Finanzas",
    level: "Intermedio",
    title: "Punto de equilibrio",
    statement: "Costos fijos S/ 3,000; precio unitario S/ 50; costo variable unitario S/ 30.",
    guidedSteps: [
      "Calcula el margen de contribucion por unidad.",
      "Divide costos fijos entre margen de contribucion.",
      "Redondea al entero superior si aplica.",
      "Explica que significa vender esa cantidad."
    ],
    expectedAnswer: "Margen de contribucion S/ 20; punto de equilibrio 150 unidades.",
    explanation: "A partir de 150 unidades se cubren costos fijos y variables; luego empieza la ganancia."
  },
  {
    id: "fin-capital-trabajo",
    category: "Finanzas",
    level: "Intermedio",
    title: "Capital de trabajo",
    statement: "Activo corriente S/ 18,000 y pasivo corriente S/ 11,500.",
    guidedSteps: [
      "Identifica activos corrientes.",
      "Identifica pasivos corrientes.",
      "Resta pasivos corrientes a activos corrientes.",
      "Evalua si el resultado permite operar con calma."
    ],
    expectedAnswer: "Capital de trabajo S/ 6,500.",
    explanation: "Un capital de trabajo positivo sugiere capacidad para cubrir obligaciones de corto plazo."
  },
  {
    id: "fin-cobranza",
    category: "Finanzas",
    level: "Basico",
    title: "Dias de cobranza",
    statement: "Cuentas por cobrar S/ 9,000 y ventas mensuales al credito S/ 18,000.",
    guidedSteps: [
      "Divide cuentas por cobrar entre ventas al credito.",
      "Multiplica por 30 días.",
      "Compara con la politica de credito.",
      "Define si la cobranza esta sana."
    ],
    expectedAnswer: "Días de cobranza estimados: 15 días.",
    explanation: "Mientras menor sea el plazo real frente a la politica, mas saludable es la liquidez."
  },
  {
    id: "tri-igv-debito",
    category: "Tributación",
    level: "Basico",
    title: "IGV debito fiscal",
    statement: "Ventas gravadas del mes S/ 8,000 sin IGV.",
    guidedSteps: [
      "Confirma que la base no incluye IGV.",
      "Aplica la tasa de 18%.",
      "Reconoce el debito fiscal.",
      "Relaciona el monto con la declaracion mensual."
    ],
    expectedAnswer: "IGV debito fiscal S/ 1,440.",
    explanation: "El debito fiscal nace por ventas gravadas y se compensa con credito fiscal valido."
  },
  {
    id: "tri-igv-credito",
    category: "Tributación",
    level: "Basico",
    title: "Credito fiscal",
    statement: "Compras gravadas S/ 3,500 sin IGV, sustentadas con comprobantes validos.",
    guidedSteps: [
      "Verifica que las compras esten sustentadas.",
      "Aplica la tasa de 18%.",
      "Identifica el credito fiscal.",
      "Resta contra el debito fiscal cuando corresponda."
    ],
    expectedAnswer: "Credito fiscal S/ 630.",
    explanation: "El credito fiscal reduce el IGV por pagar si cumple requisitos formales y sustanciales."
  },
  {
    id: "tri-renta-pago-cuenta",
    category: "Tributación",
    level: "Intermedio",
    title: "Pago a cuenta de renta",
    statement: "Ingresos netos mensuales S/ 25,000 y coeficiente aplicable 1.5%.",
    guidedSteps: [
      "Identifica los ingresos netos del mes.",
      "Aplica el coeficiente.",
      "Determina el pago a cuenta.",
      "Revisa si hay credito o saldo aplicable."
    ],
    expectedAnswer: "Pago a cuenta S/ 375.",
    explanation: "El pago a cuenta anticipa impuesto a la renta anual según régimen y coeficiente aplicable."
  },
  {
    id: "tri-retencion-recibo",
    category: "Tributación",
    level: "Basico",
    title: "Retencion por recibo por honorarios",
    statement: "Un recibo por honorarios es de S/ 2,000 y corresponde aplicar retencion de 8%.",
    guidedSteps: [
      "Confirma si supera el umbral y si aplica retencion.",
      "Multiplica el importe por 8%.",
      "Resta la retencion al pago neto.",
      "Registra la obligacion de enterar la retencion."
    ],
    expectedAnswer: "Retencion S/ 160; pago neto S/ 1,840.",
    explanation: "La retencion se descuenta al proveedor y se entrega a la administracion tributaria."
  },
  {
    id: "tri-cronograma",
    category: "Tributación",
    level: "Intermedio",
    title: "Riesgo por vencimiento",
    statement: "La empresa tiene IGV por declarar y el vencimiento es mañana. No hay información completa.",
    guidedSteps: [
      "Identifica la obligación próxima.",
      "Lista la información faltante.",
      "Prioriza ventas, compras y libros.",
      "Define alerta preventiva sin declarar por el sistema."
    ],
    expectedAnswer: "Estado Riesgo por información incompleta y vencimiento cercano; preparar documentos y revisión humana.",
    explanation: "DCFT alerta y prepara diagnóstico. No declara, no paga y no modifica información."
  },
  {
    id: "cont-plan-contable-caja",
    category: "Contabilidad",
    level: "Basico",
    title: "Cuenta contable para caja",
    statement: "La empresa recibe S/ 800 en efectivo por una venta menor. Identifica la cuenta contable principal y el efecto.",
    guidedSteps: [
      "Reconoce que el dinero ingresa a caja.",
      "Ubica caja dentro del activo corriente.",
      "Determina si aumenta o disminuye.",
      "Relaciona el ingreso con venta e IGV si corresponde."
    ],
    expectedAnswer: "La cuenta principal es Caja. Aumenta el activo por S/ 800 y se reconoce la contrapartida de venta e impuesto si aplica.",
    explanation: "Caja representa efectivo disponible. El plan contable sirve como referencia para clasificar el movimiento."
  },
  {
    id: "cont-asiento-aporte",
    category: "Contabilidad",
    level: "Basico",
    title: "Aporte de capital",
    statement: "Los socios aportan S/ 5,000 a la cuenta bancaria de la empresa.",
    guidedSteps: [
      "Identifica el ingreso de dinero al banco.",
      "Reconoce que no es venta ni prestamo.",
      "Registra aumento de patrimonio.",
      "Verifica que activo y patrimonio crezcan por el mismo monto."
    ],
    expectedAnswer: "Cargo a bancos S/ 5,000 y abono a capital social o aportes de socios S/ 5,000.",
    explanation: "El aporte incrementa recursos de la empresa y patrimonio, no genera ingreso operativo."
  },
  {
    id: "cont-anticipo-cliente",
    category: "Contabilidad",
    level: "Intermedio",
    title: "Anticipo de cliente",
    statement: "Un cliente adelanta S/ 1,200 por un servicio que se entregara el proximo mes.",
    guidedSteps: [
      "Identifica que aun no se presto el servicio.",
      "Registra el dinero recibido.",
      "Reconoce una obligacion con el cliente.",
      "Difiere el ingreso hasta cumplir el servicio."
    ],
    expectedAnswer: "Cargo a bancos S/ 1,200 y abono a anticipo de clientes o pasivo equivalente S/ 1,200.",
    explanation: "El anticipo no es ingreso devengado todavia; representa una obligacion de entregar el servicio."
  },
  {
    id: "cont-provision-cts",
    category: "Contabilidad",
    level: "Intermedio",
    title: "Provision de beneficio laboral",
    statement: "La empresa estima S/ 650 de beneficio laboral devengado del mes.",
    guidedSteps: [
      "Identifica el gasto laboral del periodo.",
      "Aplica devengo aunque el pago sea posterior.",
      "Reconoce la obligacion por pagar.",
      "Separa la provision de pagos ya efectuados."
    ],
    expectedAnswer: "Cargo a gasto de personal S/ 650 y abono a beneficios sociales por pagar S/ 650.",
    explanation: "Los beneficios laborales se reconocen cuando se devengan, no solo cuando se pagan."
  },
  {
    id: "cont-ajuste-inventario",
    category: "Contabilidad",
    level: "Intermedio",
    title: "Ajuste por merma",
    statement: "El conteo fisico muestra merma de inventario valorizada en S/ 240.",
    guidedSteps: [
      "Compara inventario contable y fisico.",
      "Determina el valor de la diferencia.",
      "Reconoce gasto o perdida segun sustento.",
      "Reduce el inventario registrado."
    ],
    expectedAnswer: "Cargo a gasto o perdida por merma S/ 240 y abono a inventarios S/ 240.",
    explanation: "El inventario debe reflejar existencia real. La merma requiere sustento y tratamiento tributario revisable."
  },
  {
    id: "fin-liquidez-corriente",
    category: "Finanzas",
    level: "Basico",
    title: "Ratio de liquidez corriente",
    statement: "Activo corriente S/ 24,000 y pasivo corriente S/ 16,000.",
    guidedSteps: [
      "Toma activo corriente.",
      "Toma pasivo corriente.",
      "Divide activo corriente entre pasivo corriente.",
      "Interpreta si cubre obligaciones de corto plazo."
    ],
    expectedAnswer: "Liquidez corriente 1.5.",
    explanation: "Por cada sol de deuda corriente hay S/ 1.50 de activo corriente."
  },
  {
    id: "fin-endeudamiento",
    category: "Finanzas",
    level: "Intermedio",
    title: "Nivel de endeudamiento",
    statement: "Pasivo total S/ 45,000 y activo total S/ 90,000.",
    guidedSteps: [
      "Identifica pasivo total.",
      "Identifica activo total.",
      "Divide pasivo entre activo.",
      "Convierte el resultado en porcentaje."
    ],
    expectedAnswer: "Endeudamiento 50%.",
    explanation: "La mitad de los activos se financia con deuda; requiere comparar con el sector y capacidad de pago."
  },
  {
    id: "fin-rotacion-inventario",
    category: "Finanzas",
    level: "Intermedio",
    title: "Rotacion de inventario",
    statement: "Costo de ventas anual S/ 120,000 e inventario promedio S/ 20,000.",
    guidedSteps: [
      "Usa costo de ventas, no ventas.",
      "Divide costo de ventas entre inventario promedio.",
      "Interpreta cuantas veces rota el inventario.",
      "Relaciona la rotacion con compras y caja."
    ],
    expectedAnswer: "Rotacion de inventario 6 veces al ano.",
    explanation: "Una rotacion de 6 indica que el inventario promedio se renueva unas seis veces en el periodo."
  },
  {
    id: "fin-descuento-pronto-pago",
    category: "Finanzas",
    level: "Basico",
    title: "Descuento por pronto pago",
    statement: "Un proveedor ofrece 3% de descuento si se paga una factura de S/ 2,500 esta semana.",
    guidedSteps: [
      "Multiplica el importe por 3%.",
      "Calcula el pago neto.",
      "Compara ahorro con disponibilidad de caja.",
      "Decide si conviene tomar el descuento."
    ],
    expectedAnswer: "Descuento S/ 75; pago neto S/ 2,425.",
    explanation: "El descuento mejora caja futura si la empresa puede pagar sin afectar obligaciones prioritarias."
  },
  {
    id: "fin-presupuesto-variacion",
    category: "Finanzas",
    level: "Intermedio",
    title: "Variacion de presupuesto",
    statement: "El gasto presupuestado fue S/ 6,000 y el gasto real fue S/ 6,900.",
    guidedSteps: [
      "Resta presupuesto a gasto real.",
      "Determina si la variacion es favorable o desfavorable.",
      "Calcula el porcentaje sobre presupuesto.",
      "Propone una revision de causa."
    ],
    expectedAnswer: "Variacion desfavorable S/ 900, equivalente a 15% sobre presupuesto.",
    explanation: "Una variacion desfavorable indica gasto mayor al previsto y requiere explicar causa y correccion."
  },
  {
    id: "tri-igv-por-pagar",
    category: "Tributación",
    level: "Basico",
    title: "IGV por pagar",
    statement: "Debito fiscal S/ 2,160 y credito fiscal valido S/ 1,350.",
    guidedSteps: [
      "Identifica debito fiscal.",
      "Identifica credito fiscal.",
      "Resta credito a debito.",
      "Determina si hay impuesto por pagar o saldo."
    ],
    expectedAnswer: "IGV por pagar S/ 810.",
    explanation: "El credito fiscal valido reduce el debito fiscal del periodo."
  },
  {
    id: "tri-percepcion",
    category: "Tributación",
    level: "Intermedio",
    title: "Percepcion aplicada",
    statement: "Una factura de compra incluye percepcion de S/ 45. La empresa debe reconocerla para compensacion futura.",
    guidedSteps: [
      "Separa percepcion del costo y del IGV.",
      "Identifica que es un pago adelantado.",
      "Registra una cuenta por aplicar.",
      "Controla su uso en declaraciones posteriores."
    ],
    expectedAnswer: "Registrar la percepcion como credito o saldo por aplicar de S/ 45, separado del gasto o inventario.",
    explanation: "La percepcion no es gasto; se controla para su aplicacion tributaria segun reglas vigentes."
  },
  {
    id: "tri-detraccion",
    category: "Tributación",
    level: "Intermedio",
    title: "Detraccion de servicio",
    statement: "Un servicio de S/ 1,000 esta sujeto a detraccion de 12%.",
    guidedSteps: [
      "Verifica si el servicio esta sujeto al sistema.",
      "Aplica el porcentaje de detraccion.",
      "Calcula el monto depositado.",
      "Determina el pago al proveedor luego del deposito."
    ],
    expectedAnswer: "Detraccion S/ 120; pago directo al proveedor S/ 880, sujeto a comprobante y deposito correspondiente.",
    explanation: "La detraccion separa una parte del pago para depositarla en cuenta habilitada, no es descuento comercial."
  },
  {
    id: "tri-renta-anual-estimada",
    category: "Tributación",
    level: "Intermedio",
    title: "Renta anual estimada",
    statement: "Utilidad tributaria estimada S/ 40,000 y tasa referencial 29.5%.",
    guidedSteps: [
      "Identifica la base tributaria.",
      "Aplica la tasa indicada.",
      "Calcula impuesto estimado.",
      "Recuerda revisar adiciones, deducciones y pagos a cuenta."
    ],
    expectedAnswer: "Impuesto estimado S/ 11,800 antes de compensar pagos a cuenta u otros creditos.",
    explanation: "Es una estimacion de estudio. La determinacion real exige revision tributaria completa."
  },
  {
    id: "tri-no-declaracion-automatica",
    category: "Tributación",
    level: "Basico",
    title: "Limite operativo DCFT",
    statement: "Un usuario pregunta si DCFT puede presentar la declaracion mensual automaticamente.",
    guidedSteps: [
      "Identifica la accion oficial solicitada.",
      "Reconoce que requiere decision humana y sistema autorizado.",
      "Separa diagnostico de ejecucion oficial.",
      "Responde con el limite de seguridad."
    ],
    expectedAnswer: "DCFT puede preparar alertas y revision, pero no declara, no paga y no modifica informacion tributaria automaticamente.",
    explanation: "La frontera protege al usuario: DCFT acompana y diagnostica, pero no ejecuta acciones oficiales sin marco aprobado."
  }
];

const STUDENT_DOCTOR_SUGGESTIONS = [
  "Explícame el crédito fiscal con un ejemplo.",
  "¿Cómo registro una venta con IGV?",
  "¿Qué es capital de trabajo?",
  "¿Cómo calculo el punto de equilibrio?",
  "¿Qué diferencia hay entre gasto deducible y no deducible?"
];

const PLAN_CONTABLE_BASE: PlanContableItem[] = [
  { code: "10", name: "Efectivo y equivalentes de efectivo", categoryName: "Activo", use: "Caja, bancos y fondos disponibles para operaciones de corto plazo." },
  { code: "12", name: "Cuentas por cobrar comerciales", categoryName: "Activo", use: "Facturas, boletas y letras pendientes de cobro a clientes." },
  { code: "20", name: "Mercaderías", categoryName: "Activo", use: "Bienes adquiridos para venta sin transformación relevante." },
  { code: "33", name: "Propiedad, planta y equipo", categoryName: "Activo", use: "Activos fijos usados en la operación, como equipos o muebles." },
  { code: "40", name: "Tributos por pagar", categoryName: "Pasivo", use: "IGV, renta u otras obligaciones tributarias por liquidar." },
  { code: "42", name: "Cuentas por pagar comerciales", categoryName: "Pasivo", use: "Obligaciones con proveedores por compras de bienes o servicios." },
  { code: "50", name: "Capital", categoryName: "Patrimonio", use: "Aportes de socios o titulares registrados como patrimonio." },
  { code: "60", name: "Compras", categoryName: "Gasto/costo", use: "Adquisiciones relacionadas con bienes o insumos de la actividad." },
  { code: "70", name: "Ventas", categoryName: "Ingreso", use: "Ingresos por venta de bienes o prestación de servicios." },
  { code: "94", name: "Gastos administrativos", categoryName: "Gasto", use: "Destino de gastos vinculados con administración y soporte." }
];

const DEFAULT_ONBOARDING_VIDEOS: OnboardingVideo[] = [
  {
    id: "bienvenida_dcft",
    title: "Bienvenida a DCFT",
    description: "Conoce el centro de salud empresarial y cómo navegar sin exponer datos sensibles.",
    placeholder: true,
    duration_hint: "2 minutos",
    seen: false,
    button_label: "Ver guía escrita",
    status: "pending",
    written_guide: "Lee la portada, identifica Inicio, Diagnóstico, Empresa, Ejercicios y Primeros pasos. Usa una cuenta de estudiante si no tienes RUC."
  },
  {
    id: "student_account",
    title: "Crear cuenta estudiante",
    description: "Registro con correo y contraseña; no solicita RUC ni datos de empresa.",
    placeholder: true,
    duration_hint: "2 minutos",
    seen: false,
    button_label: "Ver guía escrita",
    status: "pending",
    written_guide: "Elige Estudiante, escribe tu nombre, correo y contraseña segura. El plan Estudiante mantiene ejercicios y módulos premium visibles bloqueados."
  },
  {
    id: "business_account",
    title: "Crear cuenta empresarial",
    description: "Alta con RUC, Usuario SOL, Clave SOL, consentimiento y plan MYPE o Premium.",
    placeholder: true,
    duration_hint: "3 minutos",
    seen: false,
    button_label: "Ver guía escrita",
    status: "pending",
    written_guide: "Elige Empresa, registra RUC, Usuario SOL, Clave SOL y consentimiento. La razón social queda pendiente de validación y no bloquea el flujo."
  },
  {
    id: "sunat_sol_access",
    title: "Acceso SUNAT con Clave SOL",
    description: "Prepara acceso de consulta para diagnóstico seguro con Usuario SOL y Clave SOL.",
    placeholder: true,
    duration_hint: "2 minutos",
    seen: false,
    button_label: "Ver guía escrita",
    status: "pending",
    written_guide: "Ingresa tu RUC, Usuario SOL y Clave SOL solo si autorizas a DCFT a consultar información tributaria para diagnóstico. DCFT no declara, no paga, no emite y no modifica."
  },
  {
    id: "connect_company",
    title: "Empresa y espacio de trabajo",
    description: "Confirma empresa activa, RUC, régimen y plan antes del diagnóstico.",
    placeholder: true,
    duration_hint: "2 minutos",
    seen: false,
    button_label: "Ver guía escrita",
    status: "pending",
    written_guide: "Abre Empresa, verifica la empresa activa y el espacio de trabajo. Si falta alguno, el semáforo debe quedarse en Pendiente."
  },
  {
    id: "interpret_diagnosis",
    title: "Interpretar el diagnóstico",
    description: "Lee el semáforo: En orden, Atención, Riesgo, Pendiente o Diagnóstico pendiente.",
    placeholder: true,
    duration_hint: "3 minutos",
    seen: false,
    button_label: "Ver guía escrita",
    status: "pending",
    written_guide: "Verde significa En orden, ámbar significa Atención y rojo significa Riesgo. Pendiente indica que falta empresa o información inicial."
  },
  {
    id: "student_exercises",
    title: "Ejercicios guiados",
    description: "Filtra contabilidad, finanzas o tributación y revisa soluciones paso a paso.",
    placeholder: true,
    duration_hint: "4 minutos",
    seen: false,
    button_label: "Ver guía escrita",
    status: "pending",
    written_guide: "Abre Ejercicios, elige categoría, selecciona un caso y presiona Ver solución. Luego puedes preguntar al Doctor."
  },
  {
    id: "premium_trial",
    title: "Prueba Premium de 7 días",
    description: "Entiende que se desbloquea, fechas de inicio y fin, y regreso al plan base.",
    placeholder: true,
    duration_hint: "2 minutos",
    seen: false,
    button_label: "Ver guía escrita",
    status: "pending",
    written_guide: "Admin CEO activa o desactiva la Prueba Premium. Al vencer, la cuenta vuelve al plan base y conserva historial; los módulos premium se bloquean."
  }
];

const BUSINESS_GUIDE_STEPS = [
  {
    id: "business-guide-sol-access",
    title: "Cómo conectar SUNAT con Clave SOL",
    text: "Guía escrita disponible mientras preparamos el video.",
    buttonLabel: "Ver guía de acceso SUNAT",
    guide: "Conecta SUNAT con RUC, Usuario SOL y Clave SOL solo si autorizas a DCFT a consultar información tributaria para diagnóstico."
  },
  {
    id: "business-guide-permissions",
    title: "Permisos SUNAT recomendados",
    text: "Guía escrita disponible mientras preparamos el video.",
    buttonLabel: "Ver primeros pasos",
    guide: "Para que DCFT pueda hacer un diagnóstico completo, habilita estos permisos de consulta en SUNAT."
  },
  {
    id: "business-guide-boundaries",
    title: "Qué NO puede hacer DCFT con ese acceso",
    text: "Guía escrita disponible mientras preparamos el video.",
    buttonLabel: "Ver seguridad de DCFT",
    guide: "DCFT no declara impuestos, no paga impuestos, no emite facturas, no modifica datos y no cambia información de la empresa."
  },
  {
    id: "business-guide-connect",
    title: "Cómo conectar tu empresa a DCFT",
    text: "Guía escrita disponible mientras preparamos el video.",
    buttonLabel: "Ver primeros pasos",
    guide: "Registra RUC, Usuario SOL, Clave SOL, consentimiento y plan empresarial para preparar el diagnóstico seguro. La razón social queda pendiente de validación y no bloquea el flujo."
  },
  {
    id: "business-guide-diagnosis",
    title: "Cómo interpretar tu diagnóstico",
    text: "Guía escrita disponible mientras preparamos el video.",
    buttonLabel: "Ver primeros pasos",
    guide: "El diagnóstico resume señales tributarias, financieras y contables. Si falta empresa o información inicial, el estado queda Pendiente."
  },
  {
    id: "business-guide-traffic",
    title: "Qué significa el semáforo tributario, financiero y contable",
    text: "Guía escrita disponible mientras preparamos el video.",
    buttonLabel: "Ver primeros pasos",
    guide: "Verde indica en orden, ámbar indica atención, rojo indica riesgo y Pendiente indica que falta conectar empresa o información inicial."
  }
];

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
    return <EmptyState title="Espacio protegido" text="Inicia sesión para ver evidencia documental de tu empresa." />;
  }
  if (!documents.length) {
    return <EmptyState title="Sin documentos cargados" text="No existen documentos reales registrados para este espacio de trabajo." />;
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
    return <EmptyState title="Sin aprobaciones pendientes" text="No hay acciones sensibles bloqueadas para esta empresa." />;
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

type PasswordFieldProps = {
  value: string;
  onChange: (value: string) => void;
  visible: boolean;
  onToggle: () => void;
  ariaLabel: string;
  placeholder: string;
  autoComplete: string;
  disabled?: boolean;
};

function PasswordField({ value, onChange, visible, onToggle, ariaLabel, placeholder, autoComplete, disabled = false }: PasswordFieldProps) {
  const Icon = visible ? EyeOff : Eye;
  return (
    <div className="password-field">
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        type={visible ? "text" : "password"}
        aria-label={ariaLabel}
        placeholder={placeholder}
        autoComplete={autoComplete}
        disabled={disabled}
      />
      <button
        className="password-toggle"
        type="button"
        onClick={onToggle}
        disabled={disabled}
        aria-label={visible ? `Ocultar ${ariaLabel.toLowerCase()}` : `Mostrar ${ariaLabel.toLowerCase()}`}
        title={visible ? "Ocultar" : "Mostrar"}
      >
        <Icon size={17} />
      </button>
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
  const [successMessage, setSuccessMessage] = useState("");
  const [rucExistsNotice, setRucExistsNotice] = useState(false);
  const [existingRucStatus, setExistingRucStatus] = useState<ExistingRucStatus | null>(null);
  const [existingRucLoading, setExistingRucLoading] = useState(false);
  const [existingRucUpdateMode, setExistingRucUpdateMode] = useState(false);
  const [creatingAccountType, setCreatingAccountType] = useState<"" | "student" | "business">("");
  const [loginNeedsVerification, setLoginNeedsVerification] = useState(false);
  const [loginPasswordVisible, setLoginPasswordVisible] = useState(false);
  const [onboardingPasswordVisible, setOnboardingPasswordVisible] = useState(false);
  const [sunatPasswordVisible, setSunatPasswordVisible] = useState(false);
  const [businessLoginForm, setBusinessLoginForm] = useState({
    ruc: "",
    plan: "mype",
    billing_cycle: "monthly" as "monthly" | "annual"
  });
  const [plans, setPlans] = useState<PlanDefinition[]>([]);
  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [alerts, setAlerts] = useState<OperationalRecord[]>([]);
  const [recommendations, setRecommendations] = useState<OperationalRecord[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [documentIngestions, setDocumentIngestions] = useState<DocumentRecord[]>([]);
  const [governance, setGovernance] = useState<GovernanceRequest[]>([]);
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [checkoutStatus, setCheckoutStatus] = useState<CheckoutStatus | null>(null);
  const [studentDoctorStatus, setStudentDoctorStatus] = useState<StudentDoctorStatus | null>(null);
  const [studentDoctorQuestion, setStudentDoctorQuestion] = useState("");
  const [studentDoctorAnswer, setStudentDoctorAnswer] = useState<StudentDoctorAnswer | null>(null);
  const [studentDoctorError, setStudentDoctorError] = useState("");
  const [studentDoctorLoading, setStudentDoctorLoading] = useState(false);
  const [taxAiQuestion, setTaxAiQuestion] = useState("");
  const [taxAiAnswer, setTaxAiAnswer] = useState<TaxAIAnswer | null>(null);
  const [taxAiError, setTaxAiError] = useState("");
  const [taxAiLoading, setTaxAiLoading] = useState(false);
  const [planContableQuery, setPlanContableQuery] = useState("");
  const [onboardingForm, setOnboardingForm] = useState({
    tenant_name: "",
    tenant_id: "",
    admin_username: "",
    admin_password: "",
    plan: "student",
    account_type: "student",
    ruc: "",
    razon_social: "",
    nombre_comercial: "",
    regimen_tributario: "mype_tributario",
    trial_requested: true
  });
  const [sunatAuxForm, setSunatAuxForm] = useState({
    ruc: "",
    auxiliary_user_alias: "",
    sunat_password: "",
    consent_accepted: false
  });
  const [sunatApiForm, setSunatApiForm] = useState({
    client_id: "",
    client_secret: "",
    consent_accepted: false
  });
  const [sunatCredentialStatus, setSunatCredentialStatus] = useState<SunatCredentialStatus | null>(null);
  const [sunatReadonlyStatus, setSunatReadonlyStatus] = useState<SunatReadonlyStatus | null>(null);
  const [sunatPermissions, setSunatPermissions] = useState<SunatPermissionsResponse | null>(null);
  const [sunatDiagnosis, setSunatDiagnosis] = useState<SunatDiagnosisResponse | null>(null);
  const [sunatApiStatus, setSunatApiStatus] = useState<SunatApiStatus | null>(null);
  const [sunatApiDiscovery, setSunatApiDiscovery] = useState<SunatApiDiscovery | null>(null);
  const [sunatApiLoading, setSunatApiLoading] = useState(false);
  const [sunatRunLoading, setSunatRunLoading] = useState(false);
  const [activePanel, setActivePanel] = useState<PanelKey | null>(null);
  const [accessMode, setAccessMode] = useState<AccessMode>(() => {
    if (typeof window !== "undefined") {
      const requestedAccess = new URLSearchParams(window.location.search).get("access");
      if (requestedAccess === "admin") return "admin";
      if (requestedAccess === "business") return "business";
    }
    return "student";
  });
  const [diagnosticScenario, setDiagnosticScenario] = useState<DiagnosticScenario>("pending");
  const [exerciseCategory, setExerciseCategory] = useState<"Todos" | ExerciseCategory>("Todos");
  const [selectedExerciseId, setSelectedExerciseId] = useState(STUDENT_EXERCISES[0].id);
  const exerciseDetailRef = useRef<HTMLElement | null>(null);
  const [showExerciseSolution, setShowExerciseSolution] = useState(false);
  const [openGuideId, setOpenGuideId] = useState(DEFAULT_ONBOARDING_VIDEOS[0].id);
  const [adminSearch, setAdminSearch] = useState("");

  const authorized = token.length > 0;

  const logout = useCallback((reason = "session closed") => {
    const activeToken = localStorage.getItem("dcft_token");
    if (activeToken) {
      post("/auth/logout", {}, activeToken).catch(() => undefined);
    }
    localStorage.removeItem("dcft_token");
    setToken("");
    setPassword("");
    setSuccessMessage("");
    setRucExistsNotice(false);
    setExistingRucStatus(null);
    setExistingRucUpdateMode(false);
    setExistingRucLoading(false);
    setLoginNeedsVerification(false);
    setActivePanel(null);
    setAccessMode("student");
    setCurrentUser(null);
    setSummary(null);
    setAnalytics(null);
    setAlerts([]);
    setRecommendations([]);
    setDocuments([]);
    setDocumentIngestions([]);
    setGovernance([]);
    setAudit(null);
    setCheckoutStatus(null);
    setStudentDoctorStatus(null);
    setStudentDoctorQuestion("");
    setStudentDoctorAnswer(null);
    setStudentDoctorError("");
    setStudentDoctorLoading(false);
    setPlanContableQuery("");
    setCompanies([]);
    setWorkspaces([]);
    setActiveContext(null);
    setPermissions(null);
    setSunatStatus(null);
    setSunatCredentialStatus(null);
    setSunatReadonlyStatus(null);
    setSunatPermissions(null);
    setSunatDiagnosis(null);
    setSunatApiStatus(null);
    setSunatApiDiscovery(null);
    setSunatApiLoading(false);
    setSunatRunLoading(false);
    setSunatAuxForm((previous) => ({ ...previous, sunat_password: "" }));
    setSunatApiForm((previous) => ({ ...previous, client_secret: "" }));
    setOnboardingProgress(null);
    setAdminUsers([]);
    setError(reason === "session closed" ? "" : reason);
  }, []);

  const handleError = useCallback((err: unknown, fallback: string) => {
    if (err instanceof ApiError) {
      if (err.status === 401) {
        logout("Sesión expirada. Ingresa nuevamente.");
        return "Sesión expirada. Ingresa nuevamente.";
      }
      if (err.status === 403 && (err.code === "email_not_verified" || err.message.includes("Confirma tu correo"))) return "Confirma tu correo para activar tu cuenta.";
      if (err.code === "usuario_sol_mismatch" || err.code === "sunat_sol_connection_missing" || err.code?.startsWith("credential_vault_")) return err.message;
      if (err.status === 403) return "Permiso denegado por seguridad operacional.";
      if (err.status === 409 && err.code === "ruc_exists") return "Este RUC ya tiene una cuenta empresarial en DCFT. Puedes continuar con el acceso existente o actualizar el acceso SOL.";
      if (err.code === "payment_provider_missing" || err.code === "email_provider_missing" || err.code === "ai_provider_missing" || err.code === "student_doctor_quota_exceeded") return err.message;
      if (err.status === 429) return err.message || "Limite de uso activo. Intenta nuevamente en unos minutos.";
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
        const me = await request<CurrentUser>("/auth/me", {}, token);
        const canRequestAdmin = ["admin", "ceo", "owner", "super_admin"].includes(String(me.role || "").toLowerCase()) || Boolean(me.internal);
        const [
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
          checkoutBody,
          adminBody
        ] = await Promise.all([
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
          optionalSecureRequest<CheckoutStatus | null>("/subscriptions/checkout/status", null, token),
          canRequestAdmin ? optionalSecureRequest<AdminUsersResponse | null>("/admin/ceo/users", null, token) : Promise.resolve(null)
        ]);
        const studentDoctorBody = ["student", "free_student"].includes(String(me.plan || "").toLowerCase())
          ? await optionalSecureRequest<StudentDoctorStatus | null>("/student/doctor/status", null, token)
          : null;
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
        setCheckoutStatus(checkoutBody);
        setStudentDoctorStatus(studentDoctorBody);
        const selectedCompanyId = contextBody?.active_company_id || companyBody[0]?.id || "";
        const selectedWorkspaceId = contextBody?.active_workspace_id || workspaceBody.find((workspace) => workspace.empresa_id === selectedCompanyId)?.id || workspaceBody[0]?.id || "";
        if (selectedCompanyId && selectedWorkspaceId) {
          const credentialBody = await optionalSecureRequest<SunatCredentialStatus | null>(
            `/sunat/auxiliary/status?workspace_id=${encodeURIComponent(selectedWorkspaceId)}&empresa_id=${encodeURIComponent(selectedCompanyId)}`,
            null,
            token
          );
          setSunatCredentialStatus(credentialBody);
          const [readonlyStatusBody, permissionsBody, diagnosisBody] = await Promise.all([
            optionalSecureRequest<SunatReadonlyStatus | null>(
              `/sunat/readonly/status?workspace_id=${encodeURIComponent(selectedWorkspaceId)}&empresa_id=${encodeURIComponent(selectedCompanyId)}`,
              null,
              token
            ),
            optionalSecureRequest<SunatPermissionsResponse | null>(
              `/sunat/readonly/permissions?workspace_id=${encodeURIComponent(selectedWorkspaceId)}&empresa_id=${encodeURIComponent(selectedCompanyId)}`,
              null,
              token
            ),
            optionalSecureRequest<SunatDiagnosisResponse | null>(
              `/sunat/readonly/diagnosis?workspace_id=${encodeURIComponent(selectedWorkspaceId)}&empresa_id=${encodeURIComponent(selectedCompanyId)}`,
              null,
              token
            )
          ]);
          setSunatReadonlyStatus(readonlyStatusBody);
          setSunatPermissions(permissionsBody);
          setSunatDiagnosis(diagnosisBody);
          const [apiStatusBody, apiDiscoveryBody] = await Promise.all([
            optionalSecureRequest<SunatApiStatus | null>(
              `/sunat/api/status?workspace_id=${encodeURIComponent(selectedWorkspaceId)}&empresa_id=${encodeURIComponent(selectedCompanyId)}`,
              null,
              token
            ),
            optionalSecureRequest<SunatApiDiscovery | null>(
              `/sunat/api/discovery?workspace_id=${encodeURIComponent(selectedWorkspaceId)}&empresa_id=${encodeURIComponent(selectedCompanyId)}`,
              null,
              token
            )
          ]);
          setSunatApiStatus(apiStatusBody);
          setSunatApiDiscovery(apiDiscoveryBody);
        } else {
          setSunatCredentialStatus(null);
          setSunatReadonlyStatus(null);
          setSunatPermissions(null);
          setSunatDiagnosis(null);
          setSunatApiStatus(null);
          setSunatApiDiscovery(null);
        }
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
        setCheckoutStatus(null);
        setStudentDoctorStatus(null);
        setStudentDoctorAnswer(null);
        setStudentDoctorError("");
        setCompanies([]);
        setWorkspaces([]);
        setActiveContext(null);
        setPermissions(null);
        setSunatStatus(null);
        setSunatReadonlyStatus(null);
        setSunatPermissions(null);
        setSunatDiagnosis(null);
        setSunatCredentialStatus(null);
        setSunatApiStatus(null);
        setSunatApiDiscovery(null);
        setOnboardingProgress(null);
        setAdminUsers([]);
      }
    } catch (err) {
      setError(handleError(err, "No se pudo actualizar DCFT."));
    } finally {
      setLoading(false);
    }
  }, [handleError, optionalSecureRequest, token]);

  useEffect(() => {
    const verifyToken = new URLSearchParams(window.location.search).get("verify_email_token");
    if (!verifyToken) return;
    setLoading(true);
    request<EmailVerificationResult>(`/auth/verify-email?token=${encodeURIComponent(verifyToken)}`)
      .then((result) => {
        setSuccessMessage(result.message || "Correo confirmado. Ya puedes iniciar sesión.");
        setError("");
        setLoginNeedsVerification(false);
        const url = new URL(window.location.href);
        url.searchParams.delete("verify_email_token");
        window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
      })
      .catch((err) => setError(handleError(err, "No se pudo confirmar el correo.")))
      .finally(() => setLoading(false));
  }, [handleError]);

  const login = async (event?: FormEvent) => {
    event?.preventDefault();
    setLoading(true);
    setError("");
    setSuccessMessage("");
    setLoginNeedsVerification(false);
    try {
      const session = await post<Session>("/auth/login", { username, password });
      setToken(session.access_token);
      localStorage.setItem("dcft_token", session.access_token);
      setPassword("");
    } catch (err) {
      if (err instanceof ApiError && (err.code === "email_not_verified" || err.message.includes("Confirma tu correo"))) {
        setLoginNeedsVerification(true);
      }
      setError(handleError(err, "No se pudo iniciar sesión."));
    } finally {
      setLoading(false);
    }
  };

  const resendVerification = async () => {
    if (!username.trim()) {
      setError("Escribe tu correo para reenviar la verificación.");
      return;
    }
    setLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      const result = await post<EmailVerificationResult>("/auth/resend-verification", { username: username.trim() });
      setSuccessMessage(result.message);
      setLoginNeedsVerification(!result.email_verified);
    } catch (err) {
      setError(handleError(err, "No se pudo reenviar la verificación."));
    } finally {
      setLoading(false);
    }
  };

  const requestCheckout = async (plan: string, billingCycle: "monthly" | "annual") => {
    if (!token) {
      setError("Inicia sesión para activar checkout real.");
      openPanel("perfil");
      return;
    }
    setLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      const result = await post<CheckoutResult>("/subscriptions/checkout", { plan, billing_cycle: billingCycle }, token);
      if (result.checkout_url) {
        window.location.assign(result.checkout_url);
        return;
      }
      setSuccessMessage(result.message || "Checkout preparado por proveedor real.");
    } catch (err) {
      setError(handleError(err, "No se pudo abrir checkout real."));
    } finally {
      setLoading(false);
    }
  };

  const askStudentDoctor = async (event?: FormEvent) => {
    event?.preventDefault();
    const question = studentDoctorQuestion.trim();
    if (!token) {
      setError("Inicia sesión como estudiante para preguntar al Doctor.");
      openPanel("perfil");
      return;
    }
    if (question.length < 3) {
      setStudentDoctorError("Escribe una pregunta de estudio.");
      return;
    }
    setStudentDoctorLoading(true);
    setStudentDoctorError("");
    setStudentDoctorAnswer(null);
    try {
      const answer = await post<StudentDoctorAnswer>("/student/doctor/ask", { question }, token);
      setStudentDoctorAnswer(answer);
      setStudentDoctorStatus((previous) => ({
        doctor_name: answer.doctor_name,
        available: true,
        ai_provider_missing: false,
        provider: answer.provider,
        model: answer.model,
        quota: answer.quota,
        message: "Puedes hacer hasta 5 preguntas mensuales sobre contabilidad, finanzas y tributación."
      }));
      setStudentDoctorQuestion("");
    } catch (err) {
      setStudentDoctorError(handleError(err, "No se pudo preguntar al Doctor."));
      try {
        const statusBody = await request<StudentDoctorStatus>("/student/doctor/status", {}, token);
        setStudentDoctorStatus(statusBody);
      } catch {
        // Status refresh is best effort after provider or quota errors.
      }
    } finally {
      setStudentDoctorLoading(false);
    }
  };

  const askTaxAi = async (event?: FormEvent) => {
    event?.preventDefault();
    const question = taxAiQuestion.trim();
    if (!token) {
      setError("Inicia sesiÃ³n para consultar al Doctor DCFT.");
      openPanel("perfil");
      return;
    }
    if (question.length < 3) {
      setTaxAiError("Escribe una pregunta contable o tributaria.");
      return;
    }
    setTaxAiLoading(true);
    setTaxAiError("");
    setTaxAiAnswer(null);
    try {
      const answer = await post<TaxAIAnswer>(
        "/ai/tax/ask",
        {
          question,
          context: activeCompany ? `Empresa activa con RUC ${activeCompany.ruc}. Plan efectivo ${effectivePlanId}.` : `Plan efectivo ${effectivePlanId}.`
        },
        token
      );
      setTaxAiAnswer(answer);
      setTaxAiQuestion("");
    } catch (err) {
      setTaxAiError(handleError(err, "No se pudo consultar al Doctor DCFT."));
    } finally {
      setTaxAiLoading(false);
    }
  };

  const createTenant = async (event?: FormEvent) => {
    event?.preventDefault();
    const accountType = onboardingForm.account_type === "student" || onboardingForm.plan === "student" ? "student" : "business";
    setCreatingAccountType(accountType);
    setLoading(true);
    setError("");
    setSuccessMessage(accountType === "student" ? "Creando cuenta estudiante..." : "Creando cuenta empresarial...");
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
      setUsername(result.admin_username);
      setPassword("");
      setOnboardingForm((previous) => ({ ...previous, admin_password: "" }));
      if (result.access_token) {
        setToken(result.access_token);
        localStorage.setItem("dcft_token", result.access_token);
        setSuccessMessage(accountType === "student" ? "Cuenta estudiante creada correctamente." : "Cuenta empresarial creada correctamente.");
        if (accountType === "student") {
          setActivePanel("ejercicios");
        }
      } else {
        const verificationMessage = result.email_verification?.message || "Confirma tu correo para activar tu cuenta.";
        setLoginNeedsVerification(true);
        setSuccessMessage(verificationMessage);
      }
    } catch (err) {
      setError(handleError(err, "No se pudo crear el espacio de trabajo."));
      setSuccessMessage("");
    } finally {
      setLoading(false);
      setCreatingAccountType("");
    }
  };

  const finishBusinessAccessResult = (result: OnboardingResult, ruc: string) => {
    setUsername("");
    setPassword("");
    setOnboardingForm((previous) => ({
      ...previous,
      admin_password: "",
      admin_username: "",
      account_type: "business",
      plan: businessLoginForm.plan,
      ruc,
      razon_social: "",
      tenant_name: `Empresa RUC ${ruc}`
    }));
    setSunatAuxForm((previous) => ({ ...previous, ruc: result.company?.ruc || ruc, sunat_password: "" }));
    if (result.ruc_status) {
      setExistingRucStatus(result.ruc_status);
      setRucExistsNotice(result.ruc_status.exists);
    }
    setExistingRucUpdateMode(false);
    if (result.payment) setCheckoutStatus(result.payment);
    if (result.access_token) {
      setToken(result.access_token);
      localStorage.setItem("dcft_token", result.access_token);
    }
    if (result.checkout_url) {
      window.location.assign(result.checkout_url);
      return true;
    }
    setLoginNeedsVerification(false);
    setSuccessMessage(result.message || "Pago pendiente de configuración. Tu acceso no se activará hasta completar el pago.");
    setActivePanel(result.subscription_status === "active" ? "diagnostico" : "premium");
    return false;
  };

  const createBusinessAccountFromAccess = async () => {
    const ruc = businessLoginForm.ruc.trim();
    const sunatUsername = sunatAuxForm.auxiliary_user_alias.trim();
    const sunatPassword = sunatAuxForm.sunat_password;
    if (existingRucStatus?.exists && !existingRucUpdateMode) {
      await continueWithExistingRuc();
      return;
    }
    if (!ruc || ruc.length < 8 || sunatUsername.length < 3 || sunatPassword.length < 8 || !sunatAuxForm.consent_accepted) {
      setError("Completa RUC, Usuario SOL, Clave SOL, consentimiento y plan.");
      setSuccessMessage("");
      return;
    }
    setCreatingAccountType("business");
    setLoading(true);
    setRucExistsNotice(false);
    setError("");
    setSuccessMessage(`Preparando acceso ${businessLoginForm.plan === "mype" ? "MYPE" : "Premium"}...`);
    try {
      const result = await post<OnboardingResult>("/onboarding/company-sunat-access", {
        ruc,
        sunat_username: sunatUsername,
        sunat_password: sunatPassword,
        consent_accepted: sunatAuxForm.consent_accepted,
        plan: businessLoginForm.plan,
        billing_cycle: businessLoginForm.billing_cycle
      });
      if (finishBusinessAccessResult(result, ruc)) return;
    } catch (err) {
      if (err instanceof ApiError && err.status === 409 && err.code === "ruc_exists") {
        setRucExistsNotice(true);
        setExistingRucStatus((previous) => previous?.ruc === ruc ? previous : {
          exists: true,
          ruc,
          usuario_sol_masked: null,
          has_sunat_connection: false,
          subscription_status: "none",
          plan: null,
          checkout_status: null,
          checkout_url: null,
          can_continue: true,
          can_update_sol: true,
          can_checkout: true
        });
        setExistingRucUpdateMode(false);
        setSunatAuxForm((previous) => ({ ...previous, sunat_password: "" }));
        setError("");
        setSuccessMessage("");
        return;
      }
      setSunatAuxForm((previous) => ({ ...previous, sunat_password: "" }));
      setError(handleError(err, "No se pudo preparar el acceso empresa."));
      setSuccessMessage("");
    } finally {
      setLoading(false);
      setCreatingAccountType("");
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
      setError(handleError(err, "No se pudo seleccionar el espacio de trabajo."));
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
      setSunatAuxForm({ ruc: activeCompany.ruc, auxiliary_user_alias: sunatAuxForm.auxiliary_user_alias.trim(), sunat_password: "", consent_accepted: sunatAuxForm.consent_accepted });
      await refresh();
    } catch (err) {
      setError(handleError(err, "No se pudo preparar el acceso SUNAT SOL."));
    } finally {
      setLoading(false);
    }
  };

  const storeSunatAuxiliaryCredentials = async (event?: FormEvent) => {
    event?.preventDefault();
    if (!token || !activeCompany || !activeWorkspace) return;
    if (!sunatAuxForm.consent_accepted) {
      setError(SUNAT_CONSENT_ERROR);
      setSuccessMessage("");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const credential = await post<SunatCredentialStatus>(
        "/sunat/auxiliary/credentials",
        {
          empresa_id: activeCompany.id,
          workspace_id: activeWorkspace.id,
          ruc: sunatAuxForm.ruc.trim() || activeCompany.ruc,
          sunat_username: sunatAuxForm.auxiliary_user_alias.trim(),
          sunat_password: sunatAuxForm.sunat_password,
          consent_accepted: sunatAuxForm.consent_accepted,
          auxiliary_user_acknowledged: true,
          read_only_acknowledged: true,
          no_tax_action_acknowledged: true
        },
        token
      );
      setSunatCredentialStatus(credential);
      setSunatAuxForm({ ruc: activeCompany.ruc, auxiliary_user_alias: "", sunat_password: "", consent_accepted: true });
      await refresh();
    } catch (err) {
      setError(handleError(err, "No se pudo guardar el acceso SUNAT SOL."));
    } finally {
      setLoading(false);
    }
  };

  const runSunatReadonly = async () => {
    if (!token || !activeCompany || !activeWorkspace) return;
    setSunatRunLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      const result = await post<{
        run: SunatReadonlyRun;
        permissions: SunatPermissionCheck[];
        findings: SunatFinding[];
        summary: Record<string, unknown>;
      }>(
        "/sunat/readonly/run",
        {
          empresa_id: activeCompany.id,
          workspace_id: activeWorkspace.id
        },
        token
      );
      setSunatPermissions({
        run: result.run,
        recommended_permissions: SUNAT_RECOMMENDED_QUERY_PERMISSIONS,
        permissions: result.permissions,
        missing: result.permissions.filter((permission) => permission.is_recommended && !permission.is_available),
        additional: result.permissions.filter((permission) => permission.is_available && !permission.is_recommended && !permission.is_sensitive),
        sensitive: result.permissions.filter((permission) => permission.is_sensitive)
      });
      setSunatDiagnosis({
        run: result.run,
        summary: result.summary,
        findings: result.findings,
        prioritized_findings: result.findings
      });
      setSuccessMessage(result.run.real_sunat_session ? "Lectura SUNAT read-only registrada." : "SUNAT bloqueó la lectura automática; revisa validación manual o permisos.");
      await refresh();
    } catch (err) {
      setError(handleError(err, "No se pudo ejecutar lectura SUNAT read-only."));
    } finally {
      setSunatRunLoading(false);
    }
  };

  const storeSunatApiCredentials = async (event?: FormEvent) => {
    event?.preventDefault();
    if (!token || !activeCompany || !activeWorkspace) return;
    if (!sunatApiForm.consent_accepted) {
      setError("Autoriza el uso de Credenciales de API SUNAT antes de guardarlas.");
      setSuccessMessage("");
      return;
    }
    setSunatApiLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      const result = await post<{ credential: SunatApiCredential }>(
        "/sunat/api/credentials",
        {
          empresa_id: activeCompany.id,
          workspace_id: activeWorkspace.id,
          ruc: activeCompany.ruc,
          client_id: sunatApiForm.client_id.trim(),
          client_secret: sunatApiForm.client_secret,
          consent_accepted: sunatApiForm.consent_accepted,
          api_credentials_acknowledged: true,
          official_api_acknowledged: true,
          no_sensitive_actions_acknowledged: true
        },
        token
      );
      setSunatApiStatus((previous) => ({ ...(previous || { api_configured: true, sol_configured: Boolean(sunatCredentialStatus?.id), status: result.credential.status, read_only: true, sensitive_actions_enabled: false }), api_configured: true, credential: result.credential, status: result.credential.status }));
      setSunatApiForm({ client_id: "", client_secret: "", consent_accepted: true });
      setSuccessMessage("Credenciales API SUNAT guardadas cifradas.");
      await refresh();
    } catch (err) {
      setError(handleError(err, "No se pudieron guardar las Credenciales API SUNAT."));
    } finally {
      setSunatApiLoading(false);
    }
  };

  const testSunatApi = async () => {
    if (!token || !activeCompany || !activeWorkspace) return;
    setSunatApiLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      await post("/sunat/api/test", { empresa_id: activeCompany.id, workspace_id: activeWorkspace.id }, token);
      setSuccessMessage("API SUNAT probada con ruta oficial.");
      await refresh();
    } catch (err) {
      setError(handleError(err, "No se pudo probar API SUNAT."));
    } finally {
      setSunatApiLoading(false);
    }
  };

  const syncSunatApi = async (kind: "sales" | "purchases") => {
    if (!token || !activeCompany || !activeWorkspace) return;
    const period = new Date().toISOString().slice(0, 7).replace("-", "");
    setSunatApiLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      await post(`/sunat/api/sire/${kind}/sync`, { empresa_id: activeCompany.id, workspace_id: activeWorkspace.id, period }, token);
      setSuccessMessage(kind === "sales" ? "SIRE Ventas sincronizado por API oficial." : "SIRE Compras sincronizado por API oficial.");
      await refresh();
    } catch (err) {
      setError(handleError(err, kind === "sales" ? "No se pudo sincronizar SIRE Ventas." : "No se pudo sincronizar SIRE Compras."));
    } finally {
      setSunatApiLoading(false);
    }
  };

  const disconnectSunatAuxiliaryCredentials = async () => {
    if (!token || !activeCompany || !activeWorkspace) return;
    setLoading(true);
    setError("");
    try {
      const credential = await request<SunatCredentialStatus>(
        `/sunat/auxiliary/credentials?workspace_id=${encodeURIComponent(activeWorkspace.id)}&empresa_id=${encodeURIComponent(activeCompany.id)}&reason=user_revoked`,
        { method: "DELETE" },
        token
      );
      setSunatCredentialStatus(credential);
      setSunatAuxForm({ ruc: activeCompany.ruc, auxiliary_user_alias: "", sunat_password: "", consent_accepted: false });
      await refresh();
    } catch (err) {
      setError(handleError(err, "No se pudo desconectar SUNAT."));
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
      setError(handleError(err, "No se pudo actualizar la prueba."));
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

  useEffect(() => {
    if (accessMode !== "business") {
      setExistingRucStatus(null);
      setRucExistsNotice(false);
      setExistingRucUpdateMode(false);
      setExistingRucLoading(false);
      return;
    }
    const ruc = businessLoginForm.ruc.trim();
    if (ruc.length < 8) {
      setExistingRucStatus(null);
      setRucExistsNotice(false);
      setExistingRucUpdateMode(false);
      setExistingRucLoading(false);
      return;
    }
    let cancelled = false;
    setExistingRucLoading(true);
    const timer = window.setTimeout(() => {
      request<ExistingRucStatus>(`/onboarding/company-sunat-access/status?ruc=${encodeURIComponent(ruc)}`)
        .then((status) => {
          if (cancelled) return;
          setExistingRucStatus(status);
          setRucExistsNotice(status.exists);
          if (!status.exists) {
            setExistingRucUpdateMode(false);
          }
        })
        .catch(() => {
          if (cancelled) return;
          setExistingRucStatus(null);
          setRucExistsNotice(false);
        })
        .finally(() => {
          if (!cancelled) setExistingRucLoading(false);
        });
    }, 350);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [accessMode, businessLoginForm.ruc]);

  const runtime = runtimeStatus || summary?.runtime || null;
  const backendOk = health?.status === "ok" && runtime?.busy_loop === false;
  const planName = summary?.plan.name || currentUser?.plan || "Pendiente";
  const plansToRender = plans.length ? plans : onboardingStatus?.plans || [];
  const activePlanId = summary?.plan.id || currentUser?.plan || onboardingForm.plan;
  const trialActive = Boolean(summary?.trial?.active || onboardingProgress?.trial?.active);
  const trialExpired = Boolean(summary?.trial?.expired || onboardingProgress?.trial?.expired);
  const trialDaysRemaining = summary?.trial?.days_remaining ?? onboardingProgress?.trial?.days_remaining ?? 0;
  const effectivePlanId = summary?.trial?.plan_effective || onboardingProgress?.plan_effective || activePlanId;
  const basePlanId = summary?.trial?.plan_base || onboardingProgress?.plan_base || activePlanId;
  const normalizedPlanIds = [currentUser?.plan, activePlanId, basePlanId, effectivePlanId]
    .filter(Boolean)
    .map((value) => String(value).toLowerCase());
  const isStudentAccount = authorized && normalizedPlanIds.some((planId) => planId === "student");

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
  const currentSunatTone = sunatTone(sunatCredentialStatus?.status || sunatStatus?.status);
  const sunatReadonlyRun = sunatDiagnosis?.run || sunatReadonlyStatus?.latest_run || null;
  const sunatReadOnlySession = Boolean(sunatReadonlyRun?.real_sunat_session);
  const sunatCriticalFindings = (sunatDiagnosis?.prioritized_findings || []).filter((finding) => ["critical", "high"].includes(finding.severity));
  const sunatMissingPermissions = sunatPermissions?.missing || [];
  const sunatSensitivePermissions = sunatPermissions?.sensitive || [];

  const activeCompany = companies.find((company) => company.id === activeContext?.active_company_id) || companies[0] || null;
  const activeWorkspace = workspaces.find((workspace) => workspace.id === activeContext?.active_workspace_id) || workspaces[0] || null;
  const simulatedDiagnosisTone: SignalTone | null = diagnosticScenario === "pending" ? null : diagnosticScenario;
  const hasDiagnosticEvidence = Boolean(
    simulatedDiagnosisTone
    || documentCount > 0
    || openAlerts > 0
    || recommendationCount > 0
    || overLimitCount > 0
    || taxEvidenceCount > 0
    || financialEvidenceCount > 0
    || Boolean(sunatReadonlyRun)
  );
  const trafficPendingCause = isStudentAccount
    ? "Disponible para empresas. Tu cuenta estudiante no necesita empresa para estudiar."
    : !activeCompany
    ? "Falta conectar empresa para diagnóstico inicial."
    : !activeWorkspace
      ? "Falta crear o seleccionar espacio de trabajo."
      : !hasDiagnosticEvidence
        ? "Esperando datos autorizados para diagnóstico completo."
        : "Diagnostico simulado o datos reales disponibles.";
  const trafficBaseTone: SignalTone = (isStudentAccount || !activeCompany || !activeWorkspace || !hasDiagnosticEvidence)
    ? "neutral"
    : simulatedDiagnosisTone || signal;
  const trafficStatus = isStudentAccount
    ? "Disponible para empresas"
    : !activeCompany || !activeWorkspace
    ? "Pendiente"
    : !hasDiagnosticEvidence
      ? "Diagnóstico pendiente"
      : businessStatusLabel(trafficBaseTone);
  const trafficColor = isStudentAccount ? "Pendiente" : trafficColorLabel(trafficBaseTone);
  const resolveTrafficTone = (fallback: SignalTone): SignalTone => {
    if (isStudentAccount) return "neutral";
    if (trafficBaseTone === "neutral") return "neutral";
    return simulatedDiagnosisTone || fallback;
  };
  const canAttemptSunatAux = Boolean(
    authorized &&
    activeCompany &&
    activeWorkspace &&
    sunatAuxForm.auxiliary_user_alias.trim().length >= 3 &&
    sunatAuxForm.sunat_password.length >= 8
  );
  const canRunSunatReadonly = Boolean(
    authorized &&
    activeCompany &&
    activeWorkspace &&
    sunatCredentialStatus?.id &&
    sunatCredentialStatus.status !== "DISCONNECTED"
  );
  const canStoreSunatApi = Boolean(
    authorized &&
    activeCompany &&
    activeWorkspace &&
    sunatApiForm.client_id.trim().length >= 8 &&
    sunatApiForm.client_secret.length >= 8 &&
    sunatApiForm.consent_accepted
  );
  const canTestSunatApi = Boolean(authorized && activeCompany && activeWorkspace && sunatApiStatus?.api_configured);
  const canSyncSireApi = Boolean(canTestSunatApi && sunatApiStatus?.sol_configured);
  const rolePermissions = currentUser?.role && permissions?.roles[currentUser.role] ? permissions.roles[currentUser.role] : currentUser?.permissions || [];
  const onboardingRequiresRuc = ["mype", "premium", "business_basic", "business_premium"].includes(onboardingForm.plan);
  const canCreateTenant = Boolean(
    (onboardingStatus?.signup_enabled ?? true)
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
      detail: authorized ? `${formatNumber(openAlerts)} alertas abiertas y ${formatNumber(taxEvidenceCount)} señales tributarias.` : "Lectura privada pendiente de sesión.",
      tone: taxTone,
      meta: "Alertas, documentos y recomendaciones"
    },
    {
      icon: <WalletCards size={22} />,
      eyebrow: "Financiero",
      title: overLimitCount > 0 ? "Limites excedidos" : "Uso bajo control",
      detail: authorized ? `${formatNumber(overLimitCount)} límites excedidos y ${formatNumber(financialEvidenceCount)} señales financieras.` : "Uso de plan protegido.",
      tone: financeTone,
      meta: "Plan, uso y documentos"
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
      detail: authorized ? `Base segura ${sunatStatus?.foundation_only ? "activa" : "pendiente"}; conector real ${sunatStatus?.real_connector_enabled ? "activo" : "inactivo"}.` : "Estado SUNAT protegido.",
      tone: currentSunatTone,
      meta: "Usuario SOL"
    }
  ];

  const businessScore = trafficBaseTone === "neutral"
    ? 0
    : authorized
    ? Math.max(48, Math.min(96, 82 - openAlerts * 5 - overLimitCount * 8 + Math.min(documentCount, 4) * 2 + Math.min(recommendationCount, 3)))
    : 82;
  const businessScoreTone: SignalTone = trafficBaseTone === "neutral" ? "neutral" : businessScore >= 78 ? "green" : businessScore >= 62 ? "yellow" : "red";
  const scoreTrend = [60, 68, 75, businessScore];
  const healthTitle = isStudentAccount
    ? "Disponible para empresas"
    : trafficBaseTone === "neutral"
    ? trafficStatus
    : businessScore >= 80 ? "Buena salud" : businessScore >= 62 ? "Salud en vigilancia" : "Requiere atención";
  const healthText = isStudentAccount
    ? "No necesitas empresa para estudiar. El diagnostico empresarial se desbloquea en una cuenta empresa."
    : trafficBaseTone === "neutral"
    ? trafficPendingCause
    : businessScore >= 80 ? "Vas por buen camino." : "Hay señales que conviene revisar antes de que escalen.";
  const primaryAlertTitle = isStudentAccount
    ? "Modo estudiante activo"
    : financeTone === "red" || financeTone === "yellow" ? "Atención financiera" : openAlerts > 0 ? "Atención tributaria" : "Vigilancia preventiva";
  const primaryAlertText = isStudentAccount
    ? "Practica ejercicios de contabilidad, finanzas y tributacion. Los modulos empresariales quedan visibles como futuros desbloqueos."
    : authorized && alerts[0]?.title
    ? `${alerts[0].title}. ${alerts[0].source || "Revisa la recomendación para prevenir riesgos futuros."}`
    : "Hemos detectado señales que merecen revisión para prevenir riesgos futuros.";
  const businessSignals = [
    {
      label: "Tributaria",
      tone: resolveTrafficTone(taxTone),
      icon: <ShieldCheck size={26} />,
      status: trafficStatus,
      detail: trafficBaseTone === "neutral" ? trafficPendingCause : `Color ${trafficColor}; ${formatNumber(taxEvidenceCount)} señales tributarias revisadas`
    },
    {
      label: "Financiera",
      tone: resolveTrafficTone(financeTone),
      icon: <WalletCards size={26} />,
      status: trafficStatus,
      detail: trafficBaseTone === "neutral" ? trafficPendingCause : `Color ${trafficColor}; ${formatNumber(overLimitCount)} límites en vigilancia`
    },
    {
      label: "Contable",
      tone: resolveTrafficTone(accountingTone),
      icon: <FileCheck2 size={26} />,
      status: trafficStatus,
      detail: trafficBaseTone === "neutral" ? trafficPendingCause : `Color ${trafficColor}; ${formatNumber(documentCount)} documentos registrados`
    }
  ];
  const lockedModules = [
    {
      title: "Médico de Cabecera Empresarial",
      text: "Recibe cada mañana un diagnóstico automático de tu empresa sin necesidad de preguntar.",
      plan: "Premium"
    },
    {
      title: "Auditoría Integral",
      text: "Detecta riesgos contables, financieros y tributarios antes de que se conviertan en problemas.",
      plan: "Premium"
    }
  ];
  const defaultAccessPlans: PlanDefinition[] = [
      {
        id: "student",
        name: "Estudiante",
        features: ["consultas limitadas", "biblioteca", "casos prácticos", "premium visible bloqueado"],
        limits: { consultas: 10, reportes: 0 },
        requires_ruc: false
      },
      {
        id: "mype",
        name: "MYPE",
        features: ["vigilancia básica", "semáforos", "alertas básicas", "chat limitado"],
        limits: { precio_soles: 89, empresas: 1 },
        trial_days: 7,
        requires_ruc: true
      },
      {
        id: "premium",
        name: "Premium",
        features: ["vigilancia completa", "médico de cabecera", "auditoría inteligente", "chat avanzado"],
        limits: { precio_soles: 199, empresas: 3 },
        trial_days: 7,
        requires_ruc: true
      }
    ];
  const visiblePlanIds = ["student", "mype", "premium"];
  const rawAccessPlans = plansToRender.length ? plansToRender : defaultAccessPlans;
  const accessPlans = visiblePlanIds.map((planId) => {
    const backendPlan = rawAccessPlans.find((plan) => plan.id === planId)
      || (planId === "student" ? rawAccessPlans.find((plan) => plan.id === "free") : undefined);
    const fallbackPlan = defaultAccessPlans.find((plan) => plan.id === planId)!;
    return {
      ...fallbackPlan,
      ...(backendPlan || {}),
      id: planId,
      name: fallbackPlan.name,
      features: planId === "student"
        ? ["ejercicios guiados", "Doctor 5 preguntas/mes", "Plan Contable base", "módulos premium visibles bloqueados"]
        : planId === "mype"
          ? ["vigilancia básica", "semáforo empresarial", "alertas básicas", "reportes básicos"]
          : ["diagnóstico avanzado", "alertas inteligentes", "médico de cabecera", "análisis avanzado"],
      limits: {
        ...fallbackPlan.limits,
        ...(backendPlan?.limits || {})
      },
      prices: backendPlan?.prices,
      requires_ruc: planId !== "student",
      trial_days: planId === "student" ? undefined : (backendPlan?.trial_days ?? fallbackPlan.trial_days)
    };
  });

  const panelTitles: Record<PanelKey, string> = {
    diagnostico: "Diagnóstico empresarial",
    reportes: "Reportes y evidencia",
    doctor: "Médico de Cabecera",
    ejercicios: "Ejercicios",
    perfil: "Perfil y acceso",
    premium: "Premium y prueba",
    onboarding: "Primeros pasos",
    sunat: "Acceso seguro de consulta",
    empresa: "Empresa y espacio de trabajo",
    admin: "Admin CEO",
    beneficios: "Qué encontrarás en DCFT"
  };

  const quickActions: Array<{ panel: PanelKey; label: string; detail: string; icon: ReactNode }> = isStudentAccount
    ? [
        { panel: "ejercicios", label: "Ejercicios", detail: "Casos guiados", icon: <ClipboardList size={19} /> },
        { panel: "doctor", label: "Doctor", detail: "5 preguntas/mes", icon: <Stethoscope size={19} /> },
        { panel: "premium", label: "Planes", detail: "MYPE y Premium", icon: <Lock size={19} /> },
        { panel: "perfil", label: "Perfil", detail: "Cuenta estudiante", icon: <UserPlus size={19} /> }
      ]
    : [
        { panel: "doctor", label: "Doctor", detail: "Consulta ejecutiva", icon: <Stethoscope size={19} /> },
        { panel: "premium", label: "Premium", detail: "Prueba y módulos", icon: <Lock size={19} /> },
        { panel: "empresa", label: "Empresa", detail: "Espacio activo", icon: <Building2 size={19} /> },
        { panel: "diagnostico", label: "Diagnóstico", detail: "Salud y alertas", icon: <Search size={19} /> },
        { panel: "onboarding", label: "Primeros pasos", detail: "Videos y alta", icon: <CheckCircle2 size={19} /> }
      ];
  const guestValueItems = [
    { title: "Semáforo empresarial", text: "Pendiente, verde, ámbar o rojo según empresa e información inicial.", icon: <Gauge size={19} /> },
    { title: "Médico de cabecera", text: "Diagnóstico diario y recomendaciones para prevenir riesgos.", icon: <Stethoscope size={19} /> },
    { title: "Ejercicios guiados", text: "30 casos de contabilidad, finanzas y tributación.", icon: <ClipboardList size={19} /> },
    { title: "Primeros pasos", text: "Guías escritas para empresa y conexión SUNAT SOL.", icon: <CheckCircle2 size={19} /> }
  ];
  const studentValueItems = [
    { title: "Estudia sin RUC", text: "Correo y contraseña para practicar sin empresa ni datos SUNAT.", icon: <UserPlus size={19} /> },
    { title: "Práctica guiada", text: "30 casos de contabilidad, finanzas y tributación con explicación clara.", icon: <ClipboardList size={19} /> },
    { title: "Pregunta al Doctor", text: "5 preguntas mensuales sobre contabilidad, finanzas y tributación.", icon: <Stethoscope size={19} /> },
    { title: "Camino empresa", text: "MYPE y Premium quedan visibles como siguiente paso comercial.", icon: <ShieldCheck size={19} /> }
  ];
  const studentActiveBenefitItems = [
    { title: "Ejercicios por tema", text: "Contabilidad, finanzas y tributación en casos cortos para estudiar." },
    { title: "Soluciones guiadas", text: "Pasos, respuesta esperada y explicación clara después de iniciar sesión." },
    { title: "Práctica para clases/exámenes", text: "Casos pensados para repasar antes de clases, trabajos y evaluaciones." },
    { title: "Cuenta estudiante sin RUC", text: "Puedes estudiar en DCFT sin empresa, RUC ni workspace." },
    { title: "Plan Contable base", text: "Cuentas PCGE iniciales para búsqueda y referencia de estudio." },
    { title: "Doctor de estudio", text: "5 preguntas mensuales para aprender con guía educativa paso a paso." }
  ];
  const studentUpcomingBenefitItems = [
    { title: "Subir ejercicio en PDF", text: "Próximamente podrás subir un ejercicio en PDF." },
    { title: "Recibir solución guiada desde PDF", text: "Próximamente recibirás una solución guiada desde tu archivo." },
    { title: "Descargar solución en PDF", text: "Próximamente podrás obtener una respuesta descargable." },
    { title: "Más bancos de ejercicios avanzados", text: "Próximamente se ampliarán los casos por nivel y tema." }
  ];

  const chooseAccessMode = (mode: AccessMode) => {
    setAccessMode(mode);
    setRucExistsNotice(false);
    setExistingRucStatus(null);
    setExistingRucUpdateMode(false);
    if (mode === "student") {
      setOnboardingForm((previous) => ({
        ...previous,
        account_type: "student",
        plan: "student",
        ruc: "",
        razon_social: "",
        nombre_comercial: ""
      }));
      return;
    }
    if (mode === "business") {
      setOnboardingForm((previous) => ({
        ...previous,
        account_type: "business",
        plan: previous.plan === "student" ? "mype" : previous.plan,
        trial_requested: true
      }));
    }
  };

  const continueWithExistingRuc = async () => {
    const ruc = businessLoginForm.ruc.trim();
    const sunatUsername = sunatAuxForm.auxiliary_user_alias.trim();
    if (!ruc || ruc.length < 8) {
      setError("Escribe el RUC de la empresa para continuar.");
      setSuccessMessage("");
      return;
    }
    if (sunatUsername.length < 3) {
      setError("Escribe el Usuario SOL completo para validar este RUC.");
      setSuccessMessage("");
      return;
    }
    setCreatingAccountType("business");
    setLoading(true);
    setError("");
    setSuccessMessage(existingRucStatus?.subscription_status === "active" ? "Validando acceso empresa..." : "Revisando pago pendiente...");
    try {
      const result = await post<OnboardingResult>("/onboarding/company-sunat-access/continue", {
        ruc,
        sunat_username: sunatUsername,
        plan: businessLoginForm.plan,
        billing_cycle: businessLoginForm.billing_cycle
      });
      if (finishBusinessAccessResult(result, ruc)) return;
    } catch (err) {
      setSunatAuxForm((previous) => ({ ...previous, sunat_password: "" }));
      setError(handleError(err, "No se pudo continuar con este RUC."));
      setSuccessMessage("");
    } finally {
      setLoading(false);
      setCreatingAccountType("");
    }
  };

  const updateExistingSunatAccess = () => {
    setRucExistsNotice(true);
    setExistingRucUpdateMode(true);
    setError("");
    setSuccessMessage("Actualiza Usuario SOL y Clave SOL. DCFT cifrará la Clave SOL y no creará otra empresa.");
  };

  const dismissRucExistsNotice = () => {
    setRucExistsNotice(false);
    setExistingRucUpdateMode(false);
    setError("");
    setSuccessMessage("");
  };

  const filteredExercises = useMemo(
    () => STUDENT_EXERCISES.filter((exercise) => exerciseCategory === "Todos" || exercise.category === exerciseCategory),
    [exerciseCategory]
  );
  const selectedExercise = STUDENT_EXERCISES.find((exercise) => exercise.id === selectedExerciseId) || filteredExercises[0] || STUDENT_EXERCISES[0];
  const normalizedPlanContableQuery = planContableQuery.trim().toLowerCase();
  const filteredPlanContable = PLAN_CONTABLE_BASE.filter((item) => {
    if (!normalizedPlanContableQuery) return true;
    return [item.code, item.name, item.categoryName, item.use].join(" ").toLowerCase().includes(normalizedPlanContableQuery);
  });
  const studentDoctorQuota = studentDoctorStatus?.quota || studentDoctorAnswer?.quota || null;
  const studentDoctorRemaining = studentDoctorQuota?.questions_remaining ?? 5;
  const studentDoctorLimit = studentDoctorQuota?.questions_limit ?? 5;
  const onboardingVideos = DEFAULT_ONBOARDING_VIDEOS.map((video) => {
    const backendVideo = onboardingProgress?.videos.find((item) => item.id === video.id);
    return {
      ...video,
      seen: Boolean(backendVideo?.seen || video.seen),
      duration_hint: backendVideo?.duration_hint || video.duration_hint,
      placeholder: backendVideo?.placeholder ?? video.placeholder,
      description: video.description,
      button_label: video.button_label
    };
  });
  const normalizedAdminSearch = adminSearch.trim().toLowerCase();
  const filteredAdminUsers = adminUsers.filter((user) => {
    if (!normalizedAdminSearch) return true;
    return [
      user.username,
      user.email,
      user.name,
      user.tenant_name,
      user.company?.razon_social,
      user.workspace?.nombre,
      user.plan,
      user.plan_effective
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(normalizedAdminSearch);
  });

  const scrollExerciseDetailIntoView = () => {
    window.setTimeout(() => {
      exerciseDetailRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  };
  const isInternalAccount = Boolean(currentUser?.internal || summary?.internal || checkoutStatus?.internal || ["admin", "ceo", "owner", "super_admin"].includes(String(currentUser?.role || "").toLowerCase()) || ["internal", "admin"].includes(String(currentUser?.plan || "").toLowerCase()));
  const hasPremiumAccess = Boolean(isInternalAccount || currentUser?.premium || summary?.premium || checkoutStatus?.premium || ["mype", "premium"].includes(String(effectivePlanId || "").toLowerCase()));
  const canUseAdminPanel = authorized && isInternalAccount;
  const openPanel = (panel: PanelKey) => setActivePanel(panel);
  const closePanel = () => setActivePanel(null);
  const publicNavItems = authorized ? DESKTOP_NAV_ITEMS.filter((item) => item.panel !== "admin" || canUseAdminPanel) : [];
  const publicError = error && (error.toLowerCase().includes("backend") || error.toLowerCase().includes("runtime") || error.toLowerCase().includes("api"))
    ? "No pudimos actualizar los datos ahora. Tu cabina sigue disponible; vuelve a intentarlo en unos segundos."
    : error;
  const publicSuccess = successMessage;

  const renderResendVerificationAction = () => loginNeedsVerification ? (
    <button className="secondary-link verification-resend-button" type="button" onClick={resendVerification} disabled={loading || !username.trim()}>
      <RefreshCcw size={16} />
      Reenviar verificación
    </button>
  ) : null;

  const renderPlanPriceLabels = (plan: PlanDefinition) => (
    <div className="plan-price-options" aria-label={`Precios ${plan.name}`}>
      {planPriceOptions(plan.id, plan.prices).map((price, index) => (
        <span key={`${price}-${index}`}>{price}</span>
      ))}
    </div>
  );

  const renderCheckoutActions = (plan: PlanDefinition) => {
    if (plan.id === "student") return null;
    if (isInternalAccount) {
      return (
        <div className="checkout-actions">
          <small>Admin CEO: premium interno habilitado. Mercado Pago no requerido.</small>
        </div>
      );
    }
    if (!authorized) {
      return (
        <button className={`secondary-link checkout-action ${plan.id === "premium" ? "premium-checkout-action" : ""}`} type="button" onClick={() => chooseAccessMode("business")}>
          <UserPlus size={16} />
          Crear cuenta empresa
        </button>
      );
    }
    const providerMissing = checkoutStatus?.payment_provider_missing ?? true;
    if (providerMissing) {
      return (
        <div className="checkout-actions">
          <small>{checkoutStatus?.message || "Pago pendiente de configuración."}</small>
          <button className={`secondary-link checkout-action ${plan.id === "premium" ? "premium-checkout-action" : ""}`} type="button" disabled>
            <WalletCards size={16} />
            Solicitar activación
          </button>
        </div>
      );
    }
    return (
      <div className="checkout-actions two">
        <button className={`premium-action-button checkout-action ${plan.id === "premium" ? "premium-checkout-action" : ""}`} type="button" onClick={() => requestCheckout(plan.id, "monthly")} disabled={loading}>
          <WalletCards size={16} />
          Pagar {plan.name} mensual
        </button>
        <button className="secondary-link checkout-action" type="button" onClick={() => requestCheckout(plan.id, "annual")} disabled={loading}>
          Pagar {plan.name} anual
        </button>
      </div>
    );
  };

  const renderSubscriptionNotice = () => {
    if (!authorized || isStudentAccount || isInternalAccount) return null;
    const subscription = checkoutStatus?.subscription;
    const statusLabel = String(subscription?.status || checkoutStatus?.current_plan || "").toLowerCase();
    const endsAt = subscription?.ends_at ? new Date(subscription.ends_at) : null;
    const daysRemaining = endsAt && !Number.isNaN(endsAt.getTime())
      ? Math.ceil((endsAt.getTime() - Date.now()) / 86_400_000)
      : null;
    let message = "";
    if (statusLabel === "pending" || checkoutStatus?.payment_provider_missing) {
      message = "Pago pendiente de configuración. Tu acceso no se activará hasta completar el pago.";
    } else if (statusLabel === "expired" || (daysRemaining !== null && daysRemaining < 0)) {
      message = "Suscripción vencida. Renueva para mantener activo el diagnóstico empresarial. Tu historial se conserva.";
    } else if (daysRemaining === 0) {
      message = "Tu suscripción vence hoy. Renueva para mantener activo el diagnóstico empresarial.";
    } else if (daysRemaining === 3) {
      message = "Faltan 3 días para vencer. Renueva para mantener activo el diagnóstico empresarial.";
    } else if (daysRemaining !== null && daysRemaining <= 7) {
      message = "Tu suscripción vence pronto. Renueva para mantener activo el diagnóstico empresarial.";
    }
    if (!message) return null;
    return (
      <section className={`trial-banner subscription-notice ${statusLabel === "expired" ? "expired" : ""}`} aria-label="Aviso de suscripción">
        <span>Suscripción empresa</span>
        <strong>{message}</strong>
        <small>Estados visibles: activo, vencido, pendiente de pago, cancelado o piloto. Los datos históricos no se borran al vencer.</small>
      </section>
    );
  };

  const renderAccessForm = (mode: AccessMode = accessMode, showHelper = true) => {
    if (mode === "business") {
      const existingRucFound = Boolean(existingRucStatus?.exists && rucExistsNotice);
      const businessNeedsSolPassword = !existingRucFound || existingRucUpdateMode;
      const businessContinueReady = Boolean(
        existingRucFound
        && businessLoginForm.ruc.trim().length >= 8
        && sunatAuxForm.auxiliary_user_alias.trim().length >= 3
      );
      const businessCreateReady = Boolean(
        businessLoginForm.ruc.trim().length >= 8
        && sunatAuxForm.auxiliary_user_alias.trim().length >= 3
        && (!businessNeedsSolPassword || (sunatAuxForm.sunat_password.length >= 8 && sunatAuxForm.consent_accepted))
      );
      const rucSubscriptionLabel = existingRucStatus?.subscription_status === "active"
        ? "Plan activo"
        : existingRucStatus?.subscription_status === "pending"
          ? "Pago pendiente"
          : existingRucStatus?.subscription_status === "expired"
            ? "Plan vencido"
            : "Sin plan activo";
      return (
        <form className="mini-login business-login-form" onSubmit={(event) => { event.preventDefault(); createBusinessAccountFromAccess(); }}>
          {showHelper ? <p className="form-helper">Acceso SUNAT para MYPE/Premium.</p> : null}
          <small className="form-subtext">{businessNeedsSolPassword ? "Usa el RUC de tu empresa, Usuario SOL y Clave SOL para diagnóstico automático autorizado." : "Usa el RUC de tu empresa y el Usuario SOL completo para continuar."}</small>
          <small className="form-subtext">{businessNeedsSolPassword ? "DCFT guarda la Clave SOL cifrada, no la muestra y no ejecuta acciones irreversibles." : "DCFT recuerda solo el Usuario SOL enmascarado y no muestra ni pide Clave SOL para continuar."}</small>
          <input
            value={businessLoginForm.ruc}
            onChange={(event) => {
              const ruc = event.target.value;
              setRucExistsNotice(false);
              setExistingRucStatus(null);
              setExistingRucUpdateMode(false);
              setBusinessLoginForm({ ...businessLoginForm, ruc });
              setOnboardingForm((previous) => ({ ...previous, account_type: "business", plan: businessLoginForm.plan, ruc }));
              setSunatAuxForm((previous) => ({ ...previous, ruc }));
            }}
            aria-label="RUC"
            placeholder="RUC"
            inputMode="numeric"
            autoComplete="off"
          />
          <input
            value={sunatAuxForm.auxiliary_user_alias}
            onChange={(event) => setSunatAuxForm({ ...sunatAuxForm, auxiliary_user_alias: event.target.value })}
            aria-label="Usuario SOL"
            placeholder={existingRucFound && !existingRucUpdateMode ? "Usuario SOL completo" : "Usuario SOL"}
            autoComplete="off"
          />
          {businessNeedsSolPassword ? (
            <>
              <PasswordField
                value={sunatAuxForm.sunat_password}
                onChange={(value) => setSunatAuxForm({ ...sunatAuxForm, sunat_password: value })}
                visible={sunatPasswordVisible}
                onToggle={() => setSunatPasswordVisible((visible) => !visible)}
                ariaLabel="Clave SOL"
                placeholder="Clave SOL"
                autoComplete="new-password"
              />
              <label className="check-row business-consent-line">
                <input
                  type="checkbox"
                  checked={sunatAuxForm.consent_accepted}
                  onChange={(event) => setSunatAuxForm({ ...sunatAuxForm, consent_accepted: event.target.checked })}
                />
                <span>Autorizo a DCFT a usar mi RUC, Usuario SOL y Clave SOL para consultar información tributaria disponible en SUNAT, guardar evidencia, generar diagnósticos y mostrar recomendaciones. DCFT no realizará pagos, declaraciones, emisiones, modificaciones ni acciones irreversibles sin autorización expresa.</span>
              </label>
            </>
          ) : (
            <small className="form-subtext">Para continuar no necesitas ingresar Clave SOL. Si quieres cambiar credenciales, usa Actualizar acceso SOL.</small>
          )}
          <div className="business-plan-toggle" role="group" aria-label="Plan MYPE/Premium">
            {(["mype", "premium"] as const).map((plan) => (
              <button
                key={plan}
                type="button"
                className={businessLoginForm.plan === plan ? "active" : ""}
                onClick={() => {
                  setBusinessLoginForm({ ...businessLoginForm, plan });
                  setOnboardingForm((previous) => ({ ...previous, account_type: "business", plan }));
                }}
              >
                {plan === "mype" ? "MYPE" : "Premium"}
              </button>
            ))}
          </div>
          <div className="business-plan-toggle business-billing-toggle" role="group" aria-label="Periodo de pago">
            {(["monthly", "annual"] as const).map((billingCycle) => {
              const amountLabel = businessLoginForm.plan === "mype"
                ? billingCycle === "monthly" ? "S/ 89" : "S/ 890"
                : billingCycle === "monthly" ? "S/ 199" : "S/ 1,990";
              return (
                <button
                  key={billingCycle}
                  type="button"
                  className={businessLoginForm.billing_cycle === billingCycle ? "active" : ""}
                  onClick={() => setBusinessLoginForm({ ...businessLoginForm, billing_cycle: billingCycle })}
                >
                  {billingCycle === "monthly" ? "Mensual" : "Anual"} {amountLabel}
                </button>
              );
            })}
          </div>
          <div className="business-entry-actions">
            {existingRucFound && !existingRucUpdateMode ? (
              <button className="primary-button" type="button" onClick={continueWithExistingRuc} disabled={loading || !businessContinueReady}>
                <ArrowRight size={16} />
                {existingRucStatus?.subscription_status === "active" ? "Entrar al dashboard" : "Continuar con este RUC"}
              </button>
            ) : (
              <button className="primary-button" type="submit" disabled={loading || !businessCreateReady}>
                {existingRucUpdateMode ? <RefreshCcw size={16} /> : <UserPlus size={16} />}
                {existingRucUpdateMode ? "Guardar acceso SOL" : businessLoginForm.plan === "mype" ? "Continuar con MYPE" : "Continuar con Premium"}
              </button>
            )}
            <button className="secondary-link" type="button" onClick={() => openPanel("sunat")}>
              <ShieldCheck size={16} />
              Ver permisos SUNAT
            </button>
          </div>
          {existingRucLoading ? <small className="form-subtext">Validando RUC en DCFT...</small> : null}
          {existingRucFound ? (
            <div className="ruc-exists-panel" role="status" aria-live="polite">
              <strong>Este RUC ya tiene una cuenta empresarial en DCFT.</strong>
              <span>
                Usuario SOL guardado: <b>{existingRucStatus?.usuario_sol_masked || "pendiente de actualización"}</b>
              </span>
              <div className="ruc-existing-meta">
                <span>{rucSubscriptionLabel}</span>
                {existingRucStatus?.checkout_status ? <span>Checkout: {existingRucStatus.checkout_status}</span> : null}
                {existingRucUpdateMode ? <span>Modo actualización SOL</span> : null}
              </div>
              <span>
                {existingRucStatus?.subscription_status === "active"
                  ? "Puedes entrar al dashboard empresa con el Usuario SOL completo."
                  : "Pago pendiente. Puedes continuar y abrir el checkout de Mercado Pago cuando esté disponible."}
              </span>
              <div className="ruc-exists-actions">
                <button className="secondary-link" type="button" onClick={continueWithExistingRuc} disabled={loading || !businessContinueReady}>
                  <ArrowRight size={16} />
                  {existingRucStatus?.subscription_status === "active" ? "Entrar al dashboard" : "Continuar con este RUC"}
                </button>
                {existingRucStatus?.can_checkout ? (
                  <button className="secondary-link" type="button" onClick={continueWithExistingRuc} disabled={loading || !businessContinueReady}>
                    <WalletCards size={16} />
                    Ir a pago pendiente
                  </button>
                ) : null}
                <button className="secondary-link" type="button" onClick={updateExistingSunatAccess} disabled={loading}>
                  <RefreshCcw size={16} />
                  Actualizar acceso SOL
                </button>
                <button className="secondary-link" type="button" onClick={dismissRucExistsNotice} disabled={loading}>
                  <X size={16} />
                  Volver
                </button>
              </div>
            </div>
          ) : null}
        </form>
      );
    }

    const isAdmin = mode === "admin";
    return (
      <form className="mini-login" onSubmit={login}>
        {showHelper ? <p className="form-helper">{isAdmin ? "Acceso protegido para activar pruebas, revisar cuentas y administrar usuarios." : "Como estudiante puedes entrar con tu correo y contraseña. No necesitas RUC."}</p> : null}
        <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label={isAdmin ? "Usuario Admin CEO" : "Correo"} placeholder={isAdmin ? "Usuario Admin CEO" : "Correo"} autoComplete={isAdmin ? "username" : "email"} />
        <PasswordField
          value={password}
          onChange={setPassword}
          visible={loginPasswordVisible}
          onToggle={() => setLoginPasswordVisible((visible) => !visible)}
          ariaLabel={isAdmin ? "Contraseña Admin CEO" : "Contraseña"}
          placeholder={isAdmin ? "Contraseña Admin CEO" : "Contraseña"}
          autoComplete="current-password"
        />
        <button className="primary-button" type="submit" disabled={loading || !username || !password}>
          <Lock size={16} />
          {mode === "student" ? "Entrar como estudiante" : "Entrar Admin CEO"}
        </button>
        {renderResendVerificationAction()}
      </form>
    );
  };

  const renderOnboardingForm = () => {
    const onboardingIsStudent = onboardingForm.account_type === "student" || onboardingForm.plan === "student";
    if (onboardingIsStudent) {
      const creatingStudent = loading && creatingAccountType === "student";
      return (
        <form className="onboarding-form student-form clean-student-form" onSubmit={createTenant}>
          <div className="student-account-note">
            <strong>Cuenta estudiante</strong>
            <span>Como estudiante puedes entrar con tu correo y contraseña.</span>
          </div>
          <input value={onboardingForm.tenant_name} onChange={(event) => setOnboardingForm({ ...onboardingForm, tenant_name: event.target.value, account_type: "student", plan: "student", ruc: "", razon_social: "", nombre_comercial: "" })} aria-label="Nombre estudiante" placeholder="Nombre estudiante" disabled={loading || authorized} autoComplete="name" />
          <input value={onboardingForm.admin_username} onChange={(event) => setOnboardingForm({ ...onboardingForm, admin_username: event.target.value, account_type: "student", plan: "student" })} aria-label="Correo" placeholder="Correo" disabled={loading || authorized} autoComplete="email" />
          <PasswordField
            value={onboardingForm.admin_password}
            onChange={(value) => setOnboardingForm({ ...onboardingForm, admin_password: value, account_type: "student", plan: "student" })}
            visible={onboardingPasswordVisible}
            onToggle={() => setOnboardingPasswordVisible((visible) => !visible)}
            ariaLabel="Contraseña estudiante"
            placeholder="Contraseña"
            disabled={loading || authorized}
            autoComplete="new-password"
          />
          <button className="primary-button" type="submit" disabled={loading || authorized || !canCreateTenant}>
            <UserPlus size={17} />
            {creatingStudent ? "Creando cuenta..." : "Crear cuenta estudiante"}
            <ArrowRight size={17} />
          </button>
        </form>
      );
    }
    return (
      <div className="onboarding-form business-form sunat-company-access">
        <div className="student-account-note">
          <strong>Empresa con conexión SUNAT SOL</strong>
          <span>Razón social pendiente de validación. No bloquea el flujo inicial.</span>
        </div>
        {renderAccessForm("business", false)}
      </div>
    );
  };

  const renderStudentBenefitsPreview = (variant: "compact" | "full" = "compact") => (
    <section className={`guest-value-preview student-benefits-preview ${variant === "compact" ? "compact-public-card" : ""}`} aria-label="Beneficios para estudiantes">
      <div className={variant === "compact" ? "compact-card-header" : "official-section-title"}>
        <span>Estudiante</span>
        <h2>Qué encontrarás en DCFT</h2>
        <p>Aprende y practica con una cuenta estudiante simple.</p>
      </div>
      {variant === "compact" ? (
        <>
          <div className="student-benefits-list compact-student-benefits">
            {studentActiveBenefitItems.slice(0, 3).map((item) => (
              <article className="student-benefit-row" key={item.title}>
                <CheckCircle2 size={18} />
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.text}</p>
                </div>
              </article>
            ))}
          </div>
          <button className="premium-action-button student-benefits-cta" type="button" onClick={() => openPanel("beneficios")}>
            <Sparkles size={18} />
            Ver beneficios
          </button>
        </>
      ) : (
        <div className="student-benefit-sections">
          <div className="student-benefit-section">
            <div className="student-benefit-section-title">
              <span>Activo ahora</span>
              <small>Disponible con cuenta estudiante</small>
            </div>
            <div className="student-benefits-list">
              {studentActiveBenefitItems.map((item) => (
                <article className="student-benefit-row" key={item.title}>
                  <CheckCircle2 size={18} />
                  <div>
                    <strong>{item.title}</strong>
                    <p>{item.text}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>
          <div className="student-benefit-section upcoming">
            <div className="student-benefit-section-title">
              <span>Próximamente</span>
              <small>Roadmap, no activo todavía</small>
            </div>
            <div className="student-benefits-list">
              {studentUpcomingBenefitItems.map((item) => (
                <article className="student-benefit-row upcoming" key={item.title}>
                  <Clock3 size={18} />
                  <div>
                    <strong>{item.title}</strong>
                    <p>{item.text}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );

  const renderStudentCommercialPath = () => (
    <section className="plans-preview student-commercial-path compact-public-card" aria-label="Camino comercial estudiante a empresa">
      <div className="compact-card-header">
        <span>Planes</span>
        <h2>Camino empresa</h2>
        <p>Empieza gratis como estudiante y pasa a empresa cuando necesites RUC, diagnóstico y reportes.</p>
      </div>
      <div className="student-plan-list">
        {accessPlans.map((plan) => (
          <article className="plan-preview-card" key={plan.id}>
            <span>{plan.id === "student" ? "Plan estudiante" : "Camino empresa"}</span>
            <strong>{plan.name}</strong>
            {renderPlanPriceLabels(plan)}
            <small>{planDisplayDescription(plan.id)}</small>
            {renderCheckoutActions(plan)}
          </article>
        ))}
      </div>
      <button className="secondary-link plans-action" type="button" onClick={() => chooseAccessMode("business")}>
        Ver planes empresa
      </button>
    </section>
  );

  const renderStudentAccessGate = (title = "Contenido protegido", text = "Crea o inicia una cuenta estudiante para acceder al contenido completo.") => (
    <div className="protected-lock-card">
      <Lock size={20} />
      <div>
        <strong>{title}</strong>
        <p>{text}</p>
      </div>
      <div className="protected-lock-actions">
        <button className="primary-button" type="button" onClick={() => openPanel("onboarding")}>
          <UserPlus size={17} />
          Crear cuenta estudiante
        </button>
        <button className="secondary-link" type="button" onClick={() => openPanel("beneficios")}>
          Ver detalle
        </button>
      </div>
    </div>
  );

  const renderStudentExerciseSpotlight = () => (
    <article className="student-exercise-spotlight">
      <div>
        <span className="overline">Ejercicios para estudiantes</span>
        <h3>Ejercicios para estudiantes</h3>
        <p>Practica contabilidad, finanzas y tributación con casos guiados.</p>
      </div>
      <div className="exercise-spotlight-stats" aria-label="Resumen de ejercicios">
        <span>{STUDENT_EXERCISES.length} ejercicios disponibles</span>
        <span>Contabilidad</span>
        <span>Finanzas</span>
        <span>Tributación</span>
      </div>
      <button className="primary-button" type="button" onClick={() => openPanel("ejercicios")}>
        <ClipboardList size={17} />
        Ver ejercicios
      </button>
    </article>
  );

  const renderBusinessSafetyBlock = (variant: "compact" | "full" = "full") => (
    <article className={`business-security-card ${variant === "compact" ? "compact-public-card" : ""}`}>
      <div>
        <span className="overline">Acceso seguro de consulta</span>
        <h3>Acceso seguro de consulta</h3>
        <div className="security-copy">
          <p>Usa RUC, Usuario SOL y Clave SOL solo con autorización expresa.</p>
          <p>DCFT no declara, no paga, no emite comprobantes y no modifica información.</p>
          <p>El acceso se guarda cifrado. La lectura SUNAT es solo consulta y queda bloqueada si SUNAT exige validación humana.</p>
        </div>
      </div>
      {variant === "compact" ? (
        <button className="premium-action-button" type="button" onClick={() => openPanel("sunat")}>
          <ShieldCheck size={17} />
          Ver seguridad
        </button>
      ) : (
      <div className="security-columns">
        <div>
          <strong>DCFT no puede:</strong>
          <ul>
            <li>declarar impuestos</li>
            <li>pagar impuestos</li>
            <li>emitir facturas</li>
            <li>modificar datos</li>
            <li>cambiar información de la empresa</li>
          </ul>
        </div>
        <div>
          <strong>DCFT solo puede:</strong>
          <ul>
            <li>leer información autorizada</li>
            <li>preparar diagnóstico</li>
            <li>detectar riesgos</li>
            <li>generar alertas</li>
            <li>ayudarte a prevenir problemas</li>
          </ul>
        </div>
      </div>
      )}
    </article>
  );

  const renderSunatCredentialState = () => {
    const credentialSaved = Boolean(sunatCredentialStatus?.id && sunatCredentialStatus.status !== "DISCONNECTED");
    const usernameLabel = sunatCredentialStatus?.sunat_username_masked || "Pendiente";
    const modeLabel = (sunatCredentialStatus?.read_only ?? sunatStatus?.read_only ?? true) ? "solo consulta" : "revisar";
    const remoteActionsLabel = (sunatCredentialStatus?.remote_actions_enabled ?? sunatStatus?.remote_actions_enabled) ? "activadas" : "desactivadas";
    const realConnectorLabel = (sunatCredentialStatus?.real_connector_enabled ?? sunatStatus?.real_connector_enabled) ? "activo" : "pendiente";
    const realSessionLabel = sunatReadOnlySession ? "activa" : "sin sesión";
    const vaultLabel = sunatCredentialStatus?.encrypted_credential_storage ? "cifrado" : "pendiente";

    return (
      <div className={`sunat-status-panel ${credentialSaved ? "stored" : "pending"}`}>
        <div>
          <span className="overline">Conexión SUNAT</span>
          <strong>{credentialSaved ? "Acceso SOL guardado seguro" : "Acceso SUNAT pendiente"}</strong>
          <p>{credentialSaved ? "La Clave SOL no vuelve al frontend y el Usuario SOL aparece enmascarado." : "Guarda RUC, Usuario SOL y Clave SOL cifrados para diagnóstico autorizado."}</p>
        </div>
        <div className="sunat-status-grid">
          <span><b>Usuario SOL</b><small>{usernameLabel}</small></span>
          <span><b>Modo</b><small>{modeLabel}</small></span>
          <span><b>Vault</b><small>{vaultLabel}</small></span>
          <span><b>SUNAT real</b><small>{realConnectorLabel}</small></span>
          <span><b>Última lectura</b><small>{realSessionLabel}</small></span>
          <span><b>Acciones remotas</b><small>{remoteActionsLabel}</small></span>
        </div>
      </div>
    );
  };

  const renderSunatReadonlyIntelligence = () => (
    <section className="sunat-readonly-panel" aria-label="SUNAT read-only intelligence">
      <div className="sunat-readonly-header">
        <div>
          <span className="overline">SUNAT read-only</span>
          <strong>{sunatReadonlyRun ? compactStatus(sunatReadonlyRun.connector_status) : "Pendiente de lectura"}</strong>
          <p>{sunatReadOnlySession ? "Sesión SUNAT de solo consulta registrada." : "DCFT puede intentar lectura real; si SUNAT exige captcha o validación manual, quedará bloqueado sin simular éxito."}</p>
        </div>
        <button className="primary-button" type="button" onClick={runSunatReadonly} disabled={!canRunSunatReadonly || sunatRunLoading || loading}>
          <Search size={17} />
          {sunatRunLoading ? "Leyendo..." : "Leer SUNAT"}
        </button>
      </div>
      <div className="sunat-readonly-grid">
        <span><b>Faltantes</b><small>{formatNumber(sunatMissingPermissions.length)}</small></span>
        <span><b>Sensibles</b><small>{formatNumber(sunatSensitivePermissions.length)}</small></span>
        <span><b>Hallazgos</b><small>{formatNumber(sunatDiagnosis?.prioritized_findings?.length || 0)}</small></span>
        <span><b>Críticos/altos</b><small>{formatNumber(sunatCriticalFindings.length)}</small></span>
      </div>
      {sunatMissingPermissions[0] ? (
        <div className="sunat-readonly-note">
          <strong>Permiso faltante</strong>
          <p>{sunatMissingPermissions[0].metadata?.missing_message || `SUNAT requiere validación manual para continuar con ${sunatMissingPermissions[0].permission_name}. DCFT no puede completar automáticamente esta sesión sin esa validación.`}</p>
        </div>
      ) : null}
      {sunatSensitivePermissions[0] ? (
        <div className="sunat-readonly-note protected">
          <strong>Permiso sensible bloqueado</strong>
          <p>Este permiso está disponible, pero DCFT no ejecuta acciones sensibles. Solo puede leer información consultable.</p>
        </div>
      ) : null}
      {(sunatDiagnosis?.prioritized_findings || []).slice(0, 3).map((finding) => (
        <div className="sunat-readonly-note" key={finding.id}>
          <strong>{finding.title}</strong>
          <p>{finding.message}</p>
        </div>
      ))}
    </section>
  );

  const renderSunatApiAutomation = () => {
    const apiConfigured = Boolean(sunatApiStatus?.api_configured);
    const solConfigured = Boolean(sunatApiStatus?.sol_configured || sunatCredentialStatus?.id);
    const services = sunatApiDiscovery?.services || [];

    return (
      <section className="sunat-api-panel" aria-label="Conexión SUNAT automática">
        <div className="sunat-api-header">
          <div>
            <span className="overline">SUNAT API oficial</span>
            <strong>Conexión SUNAT automática</strong>
            <p>Para automatización avanzada, DCFT puede usar Credenciales de API SUNAT autorizadas por el contribuyente. Estas credenciales permiten consultar servicios oficiales disponibles, como SIRE y comprobantes, cuando SUNAT lo permite.</p>
          </div>
          <StatusPill tone={apiConfigured ? "green" : "yellow"}>{apiConfigured ? "API configurada" : "API pendiente"}</StatusPill>
        </div>
        <form className="sunat-api-form" onSubmit={storeSunatApiCredentials}>
          <label>
            <span>Client ID API SUNAT</span>
            <input
              value={sunatApiForm.client_id}
              onChange={(event) => setSunatApiForm({ ...sunatApiForm, client_id: event.target.value })}
              placeholder={sunatApiStatus?.credential?.client_id_masked || "ID generado en SOL"}
              autoComplete="off"
            />
          </label>
          <label>
            <span>Client secret API SUNAT</span>
            <input
              type="password"
              value={sunatApiForm.client_secret}
              onChange={(event) => setSunatApiForm({ ...sunatApiForm, client_secret: event.target.value })}
              placeholder="Se guarda cifrado"
              autoComplete="new-password"
            />
          </label>
          <label className="inline-check sunat-api-consent">
            <input
              type="checkbox"
              checked={sunatApiForm.consent_accepted}
              onChange={(event) => setSunatApiForm({ ...sunatApiForm, consent_accepted: event.target.checked })}
            />
            <span>Autorizo el uso de Credenciales de API SUNAT solo para consultas oficiales. DCFT no declara, no paga, no emite y no modifica.</span>
          </label>
          <button className="secondary-link" type="submit" disabled={!canStoreSunatApi || sunatApiLoading || loading}>
            <ShieldCheck size={17} />
            Guardar API cifrada
          </button>
        </form>
        <div className="sunat-api-status-grid">
          <span><b>Usuario SOL</b><small>{solConfigured ? "configurado" : "pendiente"}</small></span>
          <span><b>Credenciales API</b><small>{apiConfigured ? sunatApiStatus?.credential?.client_id_masked || "configuradas" : "no configuradas"}</small></span>
          <span><b>Estado API</b><small>{compactStatus(sunatApiStatus?.status || "API_CREDENTIALS_MISSING")}</small></span>
          <span><b>Token</b><small>{sunatApiStatus?.credential?.token_configured ? "hash guardado" : "pendiente"}</small></span>
        </div>
        <div className="sunat-api-actions">
          <button className="primary-button" type="button" onClick={testSunatApi} disabled={!canTestSunatApi || sunatApiLoading || loading}>
            <Search size={17} />
            Probar API SUNAT
          </button>
          <button className="secondary-link" type="button" onClick={() => syncSunatApi("purchases")} disabled={!canSyncSireApi || sunatApiLoading || loading}>
            <FileText size={17} />
            Sincronizar compras
          </button>
          <button className="secondary-link" type="button" onClick={() => syncSunatApi("sales")} disabled={!canSyncSireApi || sunatApiLoading || loading}>
            <FileText size={17} />
            Sincronizar ventas
          </button>
          <button className="secondary-link" type="button" onClick={refresh} disabled={!authorized || sunatApiLoading || loading}>
            <Activity size={17} />
            Diagnóstico automático
          </button>
        </div>
        <div className="sunat-api-services">
          {services.slice(0, 6).map((service) => (
            <div className="sunat-api-service" key={service.service}>
              <strong>{service.label}</strong>
              <span>{compactStatus(service.status)}</span>
              <small>{service.official_api_available ? "API oficial investigada" : "Sin API oficial comprobada"}</small>
            </div>
          ))}
        </div>
        <div className="sunat-readonly-note protected">
          <strong>Permiso para automatización API</strong>
          <p>{sunatApiStatus?.permission_guide?.copy || "Credenciales de API SUNAT permite habilitar servicios oficiales para consultas automáticas. Actívalo solo si deseas que DCFT use APIs oficiales de SUNAT para automatizar consultas."}</p>
        </div>
      </section>
    );
  };

  const renderBusinessGuidePreview = (variant: "compact" | "full" = "full") => (
    <section className={`business-guide-panel ${variant === "compact" ? "compact-public-card" : ""}`} aria-label="Primeros pasos para empresas">
      <div className="business-guide-header">
        <div>
          <span className="overline">Primeros pasos</span>
          <h3>{variant === "compact" ? "Primeros pasos" : "Primeros pasos para empresas"}</h3>
          {variant === "compact" ? <p>Aprende cómo entrar, conectar tu empresa y entender tu diagnóstico.</p> : null}
        </div>
        <button className={variant === "compact" ? "premium-action-button" : "secondary-link"} type="button" onClick={() => openPanel("onboarding")}>
          <CheckCircle2 size={17} />
          Ver primeros pasos
        </button>
      </div>
      {variant === "compact" ? null : <div className="business-guide-list">
        {BUSINESS_GUIDE_STEPS.map((guide) => (
          <article className="business-guide-card" key={guide.id}>
            <strong>{guide.title}</strong>
            <p>{guide.text}</p>
            {openGuideId === guide.id ? (
              <div className="written-guide">
                <p>{guide.guide}</p>
                {guide.id === "business-guide-permissions" ? (
                  <>
                    <strong>Permisos SUNAT recomendados</strong>
                    <ul>
                      {SUNAT_RECOMMENDED_QUERY_PERMISSIONS.map((permission) => (
                        <li key={permission}>{permission}</li>
                      ))}
                    </ul>
                    <small>Para este diagnóstico falta habilitar el permiso SUNAT: [nombre exacto del permiso]. Entra a SUNAT - Administración de usuarios secundarios - Modificar programas - marca ese permiso.</small>
                  </>
                ) : null}
              </div>
            ) : null}
            <button className="secondary-link" type="button" onClick={() => setOpenGuideId(openGuideId === guide.id ? "" : guide.id)}>
              {openGuideId === guide.id ? "Ocultar guía" : guide.buttonLabel}
            </button>
          </article>
        ))}
      </div>}
    </section>
  );

  const renderGuestValuePreview = (variant: "compact" | "full" = "full") => (
    <section className={`guest-value-preview ${variant === "compact" ? "compact-public-card" : ""}`} aria-label="Vista previa DCFT">
      <div className={variant === "compact" ? "compact-card-header" : "official-section-title"}>
        <span>Vista previa</span>
        <h2>Lo que encontrarás en DCFT</h2>
        {variant === "compact" ? <p>{accessMode === "student" ? "Beneficios de estudio con cuenta simple." : "Semáforo, Doctor, empresa y primeros pasos en un solo lugar."}</p> : null}
      </div>
      {variant === "compact" ? (
        <button className="premium-action-button" type="button" onClick={() => openPanel(accessMode === "student" ? "beneficios" : "premium")}>
          <Sparkles size={17} />
          Ver DCFT
        </button>
      ) : (
      <div className="guest-value-grid">
        {(accessMode === "student" ? studentValueItems : guestValueItems).map((item) => (
          <article className="guest-value-card" key={item.title}>
            <span>{item.icon}</span>
            <strong>{item.title}</strong>
            <p>{item.text}</p>
          </article>
        ))}
      </div>
      )}
    </section>
  );

  const renderGuestAccessPortal = () => (
    <section className={`guest-access-portal ${accessMode === "business" ? "business-access-portal" : ""}`} id="access" data-screen="access" aria-label="Acceso inicial DCFT">
      <div className="guest-access-header">
        <BrandMark />
        <div>
          <span className="overline">{PRODUCT_FULL_NAME}</span>
          <h2>{PRODUCT_NAME}</h2>
          <p>Diagnóstico contable, financiero y tributario para estudiantes y empresas.</p>
          <small>Elige estudiante o empresa para iniciar con el flujo correcto.</small>
        </div>
      </div>

      {accessMode !== "admin" ? (
        <div className="access-mode-grid" aria-label="Elegir modo de acceso">
          <button className={`access-mode-card ${accessMode === "student" ? "active" : ""}`} type="button" onClick={() => chooseAccessMode("student")}>
            <UserPlus size={20} />
            <strong>Entrar como estudiante</strong>
            <span>Correo y contraseña. No necesitas RUC.</span>
          </button>
          <button className={`access-mode-card ${accessMode === "business" ? "active" : ""}`} type="button" onClick={() => chooseAccessMode("business")}>
            <Building2 size={20} />
            <strong>Entrar como empresa</strong>
            <span>Acceso empresarial para diagnóstico y reportes seguros.</span>
          </button>
        </div>
      ) : null}

      <div className="access-flow-grid">
        <article className="access-form-card">
          <span className="overline">Acceso</span>
          <h3>{accessMode === "student" ? "Entrar como estudiante" : accessMode === "business" ? "Entrar como empresa" : "Admin CEO"}</h3>
          <p>{accessMode === "admin" ? "Acceso protegido para activar pruebas, revisar cuentas y administrar usuarios." : accessMode === "business" ? "Entra con RUC, Usuario SOL, Clave SOL, consentimiento y plan." : "Como estudiante puedes entrar con tu correo y contraseña. No necesitas RUC."}</p>
          {renderAccessForm(accessMode, false)}
          {accessMode === "student" ? (
            <button className="secondary-link compact-create-link" type="button" onClick={() => openPanel("onboarding")}>
              Crear cuenta estudiante
            </button>
          ) : null}
        </article>

        {accessMode === "admin" ? (
          <article className="access-form-card protected">
            <span className="overline">Protegido</span>
            <h3>Admin CEO</h3>
            <p>Acceso interno habilitado solo por ruta protegida para usuarios autorizados.</p>
            <button className="secondary-link" type="button" onClick={() => openPanel("admin")}>
              Ver panel protegido
            </button>
          </article>
        ) : null}
      </div>

      {accessMode === "business" ? (
        <>
          {renderBusinessSafetyBlock("compact")}
          {renderBusinessGuidePreview("compact")}
        </>
      ) : null}
      {accessMode === "student" ? (
        <>
          {renderStudentBenefitsPreview("compact")}
          {renderStudentCommercialPath()}
        </>
      ) : renderGuestValuePreview("compact")}
    </section>
  );

  const renderAdminUserGrid = () => {
    if (!adminUsers.length) {
      return (
        <div className="empty-state">
          <Lock size={18} />
          <div>
            <strong>Acceso protegido</strong>
            <span>Inicia sesión con un usuario autorizado para operar Admin CEO.</span>
          </div>
        </div>
      );
    }

    return (
      <>
        <input
          className="admin-search"
          value={adminSearch}
          onChange={(event) => setAdminSearch(event.target.value)}
          aria-label="Buscar usuario"
          placeholder="Buscar usuario, empresa o plan"
        />
        {filteredAdminUsers.length ? (
          <div className="admin-user-grid">
            {filteredAdminUsers.slice(0, 8).map((user) => (
              <article className="admin-user-card" key={user.user_id}>
                <div>
                  <span>{user.role}</span>
                  <h3>{user.username}</h3>
                  <p>{user.company?.razon_social || user.tenant_name} / {user.workspace?.nombre || "Sin espacio"}</p>
                </div>
                <div className="admin-user-meta">
                  <StatusPill tone={user.trial?.active ? "yellow" : "neutral"}>
                    {user.trial?.active ? "Premium prueba" : "Prueba inactiva"}
                  </StatusPill>
                  <small>Base {featureLabel(user.plan)} / efectivo {featureLabel(user.plan_effective)}</small>
                  <small>Inicio {recordDate(user.trial?.started_at || undefined)} / fin {recordDate(user.trial?.ends_at || undefined)}</small>
                  <small>{user.trial?.active ? `${user.trial.days_remaining} días restantes` : "Puede activarse por 7 días"}</small>
                  <small>Desbloquea diagnóstico avanzado, Médico de cabecera empresarial y auditoría inteligente. Al vencer vuelve al plan base y conserva historial.</small>
                </div>
                <div className="admin-actions">
                  <button className="primary-button" type="button" onClick={() => setAdminTrial(user.user_id, true)} disabled={loading}>
                    Activar Premium 7 días
                  </button>
                  <button className="secondary-link" type="button" onClick={() => setAdminTrial(user.user_id, false)} disabled={loading}>
                    Desactivar prueba
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
          <EmptyState title="Sin resultados" text="No hay usuarios que coincidan con la búsqueda actual." />
        )}
      </>
    );
  };

  const renderPanelContent = () => {
    if (activePanel === "beneficios") {
      return (
        <div className="drawer-stack">
          {renderStudentBenefitsPreview("full")}
        </div>
      );
    }

    if (!authorized && activePanel === "ejercicios") {
      return renderStudentAccessGate(
        "Ejercicios protegidos",
        "Los ejercicios completos, el enunciado detallado y la solucion guiada se muestran despues de crear o iniciar una cuenta estudiante."
      );
    }

    if (activePanel === "onboarding") {
      const onboardingIsStudent = onboardingForm.account_type === "student" || onboardingForm.plan === "student";
      return (
        <div className="drawer-stack">
          {renderOnboardingForm()}
          {onboardingIsStudent ? (
            <>
              <div className="empty-state student-only-note">
                <ClipboardList size={18} />
                <div>
                  <strong>Beneficios preparados</strong>
                  <span>Tu cuenta estudiante entra con correo y contraseña.</span>
                </div>
              </div>
              {authorized ? renderStudentExerciseSpotlight() : renderStudentBenefitsPreview("compact")}
            </>
          ) : (
            <>
              <div className="empty-state">
                <Landmark size={18} />
                <div>
                  <strong>SUNAT seguro</strong>
                  <span>DCFT no declara. DCFT no paga. DCFT no modifica información. Solo lee información consultable autorizada.</span>
                </div>
              </div>
              {renderBusinessGuidePreview()}
            </>
          )}
        </div>
      );
    }

    if (activePanel === "diagnostico") {
      if (isStudentAccount) {
        return (
          <div className="drawer-stack">
            <div className="protected-lock-card muted">
              <Gauge size={20} />
              <div>
                <strong>Semaforo empresarial</strong>
                <p>Disponible para empresas. Tu cuenta estudiante no necesita RUC, empresa ni espacio de trabajo para estudiar.</p>
              </div>
            </div>
            <div className="protected-lock-card muted">
              <Search size={20} />
              <div>
                <strong>Diagnostico empresarial</strong>
                <p>Disponible para empresas. Cuando uses una cuenta empresa, DCFT podra mostrar salud tributaria, financiera y contable.</p>
              </div>
            </div>
          </div>
        );
      }
      return (
        <div className="drawer-stack">
          <div className="human-copy-card">
            <strong>Diagnóstico empresarial</strong>
            <p>Revisa la salud tributaria, financiera y contable. La conexión SUNAT con Clave SOL vive aquí como preparación segura y autorizada. DCFT no declara. DCFT no paga. DCFT no modifica información.</p>
          </div>
          <div className="diagnostic-simulator">
            <div>
              <span className="overline">Prueba local</span>
              <strong>Estado del semáforo</strong>
              <small>{trafficPendingCause} Estado visible: {trafficStatus}. Color: {trafficColor}.</small>
            </div>
            <div className="segmented-control" aria-label="Simular diagnóstico">
              {[
                { id: "pending", label: "Pendiente" },
                { id: "green", label: "Verde / En orden" },
                { id: "yellow", label: "Ámbar / Atención" },
                { id: "red", label: "Rojo / Riesgo" }
              ].map((item) => (
                <button
                  className={diagnosticScenario === item.id ? "active" : ""}
                  type="button"
                  key={item.id}
                  onClick={() => setDiagnosticScenario(item.id as DiagnosticScenario)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
          <div className="drawer-grid">
            {operationalCards.map((card) => (
              <InfoCard key={card.eyebrow} {...card} />
            ))}
          </div>
          <div className="context-card">
            <span className="overline">Conexión segura</span>
            <strong>Usuario SOL</strong>
            <small>Preparado para consulta. DCFT no declara. DCFT no paga. DCFT no modifica información.</small>
            <button className="alert-button" type="button" onClick={() => openPanel("sunat")}>
              Preparar conexión
              <ArrowRight size={16} />
            </button>
          </div>
          <RecordList records={alerts} kind="alert" emptyText="No existen alertas abiertas en este espacio de trabajo." />
          <RecordList records={recommendations} kind="recommendation" emptyText="No existen recomendaciones registradas para esta empresa." />
        </div>
      );
    }

    if (activePanel === "reportes") {
      if (isStudentAccount) {
        return (
          <div className="drawer-stack">
            <div className="protected-lock-card muted">
              <FileText size={20} />
              <div>
                <strong>Reportes empresariales</strong>
                <p>Disponible para empresas. En modo estudiante puedes practicar ejercicios; los reportes internos no se muestran como datos reales.</p>
              </div>
            </div>
          </div>
        );
      }
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
      if (isStudentAccount) {
        return (
          <div className="drawer-stack">
            <section className="doctor-card compact-panel-card student-doctor-card">
              <div className="doctor-portrait" aria-hidden="true">
                <img src={DOCTOR_AVATAR_SRC} alt="" />
              </div>
              <div>
                <span>Doctor de estudio</span>
                <h2>{studentDoctorStatus?.doctor_name || "Doctor de estudio contable, financiero y tributario"}</h2>
                <p>Puedes hacer hasta 5 preguntas mensuales sobre contabilidad, finanzas y tributación.</p>
                <div className="daily-diagnosis">
                  <strong>Te quedan {studentDoctorRemaining} de {studentDoctorLimit} preguntas este mes.</strong>
                  <small>{studentDoctorStatus?.ai_provider_missing ? studentDoctorStatus.message : "Guía educativa paso a paso, sin diagnóstico empresarial, sin RUC y sin SUNAT real."}</small>
                </div>
              </div>
            </section>
            <form className="student-doctor-form" onSubmit={askStudentDoctor}>
              <label htmlFor="student-doctor-question">Pregunta de estudio</label>
              <textarea
                id="student-doctor-question"
                value={studentDoctorQuestion}
                onChange={(event) => setStudentDoctorQuestion(event.target.value)}
                placeholder="Escribe una duda de contabilidad, finanzas o tributación."
                rows={4}
                disabled={studentDoctorLoading || studentDoctorRemaining <= 0}
              />
              <div className="student-doctor-suggestions" aria-label="Preguntas sugeridas">
                {STUDENT_DOCTOR_SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => setStudentDoctorQuestion(suggestion)}
                    disabled={studentDoctorLoading || studentDoctorRemaining <= 0}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
              <button className="primary-button" type="submit" disabled={studentDoctorLoading || studentDoctorRemaining <= 0}>
                <MessageCircle size={17} />
                {studentDoctorLoading ? "Consultando..." : "Preguntar al Doctor"}
              </button>
              {studentDoctorRemaining <= 0 ? (
                <p className="student-doctor-error">Has usado tus 5 preguntas del mes. Podrás volver a preguntar el próximo mes o pasar a un plan empresa cuando esté disponible.</p>
              ) : null}
              {studentDoctorError ? <p className="student-doctor-error">{studentDoctorError}</p> : null}
            </form>
            {studentDoctorAnswer ? (
              <section className="student-doctor-answer">
                <span>Respuesta del Doctor</span>
                <p>{studentDoctorAnswer.answer}</p>
                <small>{studentDoctorAnswer.educational_disclaimer}</small>
              </section>
            ) : null}
          </div>
        );
      }
      return (
        <div className="drawer-stack">
          <section className="doctor-card compact-panel-card">
            <div className="doctor-portrait" aria-hidden="true">
              <img src={DOCTOR_AVATAR_SRC} alt="" />
            </div>
            <div>
              <span>Médico de Cabecera Empresarial</span>
              <h2>Doctor DCFT</h2>
              <p>{hasPremiumAccess ? "Consulta contable/tributaria mÃ­nima conectada al proveedor IA configurable de DCFT." : "Disponible para cuentas empresa con suscripciÃ³n activa o Admin CEO interno."}</p>
              <div className="daily-diagnosis">
                <strong>{hasDiagnosticEvidence ? "Diagnóstico basado en datos autorizados" : "Esperando datos autorizados para diagnóstico completo."}</strong>
                <small>{hasDiagnosticEvidence ? `Tributaria: ${businessStatusLabel(taxTone)} / financiera: ${businessStatusLabel(financeTone)} / contable: ${businessStatusLabel(accountingTone)}` : "Esperando lectura autorizada. DCFT no declara, no paga, no emite y no modifica información."}</small>
              </div>
            </div>
          </section>
          <form className="student-doctor-form" onSubmit={askTaxAi}>
            <label htmlFor="tax-ai-question">Consulta contable o tributaria</label>
            <textarea
              id="tax-ai-question"
              value={taxAiQuestion}
              onChange={(event) => setTaxAiQuestion(event.target.value)}
              placeholder="Ejemplo: Â¿quÃ© debo revisar antes de declarar IGV mensual?"
              rows={4}
              disabled={taxAiLoading || !hasPremiumAccess}
            />
            <button className="primary-button" type="submit" disabled={taxAiLoading || !hasPremiumAccess || taxAiQuestion.trim().length < 3}>
              <MessageCircle size={17} />
              {taxAiLoading ? "Consultando..." : "Consultar IA mÃ­nima"}
            </button>
            {!hasPremiumAccess ? <p className="student-doctor-error">Premium bloqueado hasta suscripciÃ³n activa. Admin CEO interno no requiere pago.</p> : null}
            {taxAiError ? <p className="student-doctor-error">{taxAiError}</p> : null}
          </form>
          {taxAiAnswer ? (
            <section className="student-doctor-answer">
              <span>{taxAiAnswer.ai_provider_missing ? "IA configurable" : `Respuesta ${taxAiAnswer.provider || "IA"}`}</span>
              <p>{taxAiAnswer.answer}</p>
              <small>{taxAiAnswer.educational_disclaimer}</small>
            </section>
          ) : null}
          <RecordList records={recommendations} kind="recommendation" emptyText="El Doctor no tiene recomendaciones pendientes para este espacio de trabajo." />
        </div>
      );
    }

    if (activePanel === "ejercicios") {
      return (
        <div className="drawer-stack">
          <div className="human-copy-card">
            <strong>Ejercicios para estudiantes</strong>
            <p>Practica contabilidad, finanzas y tributación con casos guiados, solución y explicación clara.</p>
          </div>
          <section className="pdf-exercise-card plan-contable-card">
            <div>
              <span className="overline">Plan Contable</span>
              <h3>Plan Contable</h3>
              <p>Consulta cuentas contables y practica ejercicios con referencia al plan contable.</p>
              <small>Base inicial / en ampliación. No reemplaza un dataset normativo completo.</small>
            </div>
            <div className="plan-contable-search">
              <div className="search-field">
                <Search size={16} />
                <input
                  value={planContableQuery}
                  onChange={(event) => setPlanContableQuery(event.target.value)}
                  placeholder="Buscar cuenta o uso"
                  aria-label="Buscar en Plan Contable"
                />
              </div>
              <div className="plan-contable-results">
                {filteredPlanContable.map((item) => (
                  <article key={item.code}>
                    <span>{item.code}</span>
                    <strong>{item.name}</strong>
                    <small>{item.categoryName} / {item.use}</small>
                  </article>
                ))}
              </div>
            </div>
          </section>
          <div className="exercise-filter-bar" aria-label="Filtrar ejercicios">
            {EXERCISE_CATEGORIES.map((category) => (
              <button
                className={exerciseCategory === category ? "active" : ""}
                type="button"
                key={category}
                onClick={() => {
                  setExerciseCategory(category);
                  const firstExercise = STUDENT_EXERCISES.find((exercise) => category === "Todos" || exercise.category === category);
                  if (firstExercise) setSelectedExerciseId(firstExercise.id);
                  setShowExerciseSolution(false);
                  scrollExerciseDetailIntoView();
                }}
              >
                {category}
              </button>
            ))}
          </div>
          <div className="exercise-workbench">
            <div className="exercise-list" aria-label="Lista de ejercicios">
              {filteredExercises.map((exercise) => (
                <button
                  className={selectedExercise.id === exercise.id ? "active" : ""}
                  type="button"
                  key={exercise.id}
                  onClick={() => {
                    setSelectedExerciseId(exercise.id);
                    setShowExerciseSolution(false);
                    scrollExerciseDetailIntoView();
                  }}
                >
                  <span>{exercise.category} / {exercise.level}</span>
                  <strong>{exercise.title}</strong>
                </button>
              ))}
            </div>
            <article className="exercise-detail" ref={exerciseDetailRef}>
              <div>
                <span className="overline">{selectedExercise.category} / {selectedExercise.level}</span>
                <h3>{selectedExercise.title}</h3>
                <p>{selectedExercise.statement}</p>
              </div>
              <ol>
                {selectedExercise.guidedSteps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
              <div className="exercise-actions">
                <button className="primary-button" type="button" onClick={() => setShowExerciseSolution(!showExerciseSolution)}>
                  {showExerciseSolution ? "Ocultar solucion" : "Ver solucion"}
                </button>
                <button className="secondary-link" type="button" onClick={() => openPanel("doctor")}>
                  <MessageCircle size={16} />
                  Preguntar al Doctor
                </button>
              </div>
              {showExerciseSolution ? (
                <div className="exercise-solution">
                  <strong>Respuesta esperada</strong>
                  <p>{selectedExercise.expectedAnswer}</p>
                  <strong>Explicacion</strong>
                  <p>{selectedExercise.explanation}</p>
                </div>
              ) : null}
            </article>
          </div>
          <div className="exercise-summary-row">
            <span>Contabilidad: 10</span>
            <span>Finanzas: 10</span>
            <span>Tributación: 10</span>
          </div>
          <section className="pdf-exercise-card">
            <div>
              <span className="overline">Subir ejercicio en PDF - Próximamente</span>
              <h3>Subir ejercicio en PDF</h3>
              <p>Podrás subir un ejercicio en PDF y recibir una solución guiada.</p>
              <small>Pendiente técnico: carga, almacenamiento seguro, análisis controlado y PDF de respuesta. No hay resolver falso activo.</small>
            </div>
            <button className="primary-button" type="button" disabled>
              <FileText size={17} />
              Subir ejercicio en PDF — Próximamente
            </button>
          </section>
        </div>
      );
    }

    if (activePanel === "premium") {
      return (
        <div className="drawer-stack">
          <section className="guest-value-preview" aria-label="Beneficios de DCFT">
            <div className="official-section-title">
              <span>Beneficios</span>
              <h2>Lo que encontraras en DCFT</h2>
            </div>
            <div className="guest-value-grid">
              {(isStudentAccount ? studentValueItems : guestValueItems).map((item) => (
                <article className="guest-value-card" key={item.title}>
                  <span>{item.icon}</span>
                  <strong>{item.title}</strong>
                  <p>{item.text}</p>
                </article>
              ))}
            </div>
          </section>
          {authorized ? (
            <section className={`trial-banner ${trialExpired ? "expired" : trialActive ? "active" : ""}`}>
              <span>{trialActive ? "Premium prueba" : trialExpired ? "Prueba vencida" : "Prueba disponible"}</span>
              <strong>{trialActive ? `${trialDaysRemaining} días restantes` : `Plan base ${featureLabel(basePlanId)}`}</strong>
              <small>{isStudentAccount ? "Premium muestra que modulos se desbloquean al pasar a una cuenta empresa o a un plan superior." : `Plan efectivo: ${featureLabel(effectivePlanId)}. Desbloquea diagnóstico avanzado, Médico de cabecera empresarial y auditoría inteligente.`}</small>
              <small>Al vencer, vuelve al plan base {featureLabel(basePlanId)} y conserva historial; los módulos Premium se bloquean.</small>
              {!trialActive ? (
                <button className="alert-button" type="button" onClick={() => openPanel("admin")}>
                  Solicitar prueba
                  <ArrowRight size={16} />
                </button>
              ) : null}
            </section>
          ) : null}
          {renderSubscriptionNotice()}
          {isInternalAccount ? (
            <section className="trial-banner active" aria-label="Admin CEO premium interno">
              <span>Admin CEO interno</span>
              <strong>Premium operativo sin pago</strong>
              <small>Mercado Pago no requerido para esta cuenta interna protegida.</small>
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
                  Ver activación
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
                {renderPlanPriceLabels(plan)}
                <small>{planDisplayDescription(plan.id)}</small>
                {plan.trial_days ? <small>Prueba Premium {plan.trial_days} días</small> : null}
                {renderCheckoutActions(plan)}
              </article>
            ))}
          </div>
        </div>
      );
    }

    if (activePanel === "sunat") {
      if (isStudentAccount) {
        return (
          <div className="drawer-stack">
            <div className="protected-lock-card muted">
              <Landmark size={20} />
              <div>
                <strong>SUNAT es solo para empresas</strong>
                <p>Tu cuenta estudiante no requiere RUC, Usuario SOL ni Clave SOL.</p>
              </div>
            </div>
          </div>
        );
      }
      return (
        <div className="drawer-stack">
          {renderBusinessSafetyBlock()}
          {renderSunatCredentialState()}
          {renderSunatReadonlyIntelligence()}
          {renderSunatApiAutomation()}
          <form className="sunat-prep-form" onSubmit={storeSunatAuxiliaryCredentials}>
            <p>{SUNAT_SAFE_COPY}</p>
            <input
              value={sunatAuxForm.ruc || activeCompany?.ruc || ""}
              onChange={(event) => setSunatAuxForm({ ...sunatAuxForm, ruc: event.target.value })}
              aria-label="RUC SUNAT"
              placeholder="RUC"
              disabled={!authorized || !activeCompany || loading}
              inputMode="numeric"
            />
            <input
              value={sunatAuxForm.auxiliary_user_alias}
              onChange={(event) => setSunatAuxForm({ ...sunatAuxForm, auxiliary_user_alias: event.target.value })}
              aria-label="Usuario SOL"
              placeholder="Usuario SOL"
              disabled={!authorized || !activeCompany || loading}
              autoComplete="off"
            />
            <PasswordField
              value={sunatAuxForm.sunat_password}
              onChange={(value) => setSunatAuxForm({ ...sunatAuxForm, sunat_password: value })}
              visible={sunatPasswordVisible}
              onToggle={() => setSunatPasswordVisible((visible) => !visible)}
              ariaLabel="Clave SOL"
              placeholder="Clave SOL"
              disabled={!authorized || !activeCompany || loading}
              autoComplete="new-password"
            />
            <input
              value={compactStatus(sunatCredentialStatus?.status || sunatStatus?.status || "NOT_CONNECTED")}
              aria-label="Estado conexión SUNAT"
              placeholder="Preparado para piloto controlado"
              disabled
              readOnly
            />
            <label className="check-row">
              <input
                type="checkbox"
                checked={sunatAuxForm.consent_accepted}
                onChange={(event) => setSunatAuxForm({ ...sunatAuxForm, consent_accepted: event.target.checked })}
                disabled={!authorized || loading}
              />
              <span>Autorizo a DCFT a usar mi RUC, Usuario SOL y Clave SOL para consultar información tributaria disponible en SUNAT, guardar evidencia, generar diagnósticos y mostrar recomendaciones. DCFT no realizará pagos, declaraciones, emisiones, modificaciones ni acciones irreversibles sin autorización expresa.</span>
            </label>
            <div className="sunat-guide-box">
              <strong>Guía</strong>
              <span>{sunatCredentialStatus?.sunat_username_masked ? `Usuario SOL seguro: ${sunatCredentialStatus.sunat_username_masked}` : "Ingresa Usuario SOL y Clave SOL solo si autorizas la consulta automática."}</span>
            </div>
            <button className="secondary-link" type="button" onClick={disconnectSunatAuxiliaryCredentials} disabled={!authorized || !activeCompany || loading || !sunatCredentialStatus?.id}>
              Desconectar SUNAT
            </button>
            <button className="primary-button" type="submit" disabled={!canAttemptSunatAux || loading}>
              <ShieldCheck size={17} />
              Guardar acceso seguro
            </button>
            <small>La Clave SOL se cifra y no se muestra después de guardar. Puedes desconectar SUNAT cuando quieras.</small>
          </form>
        </div>
      );
    }

    if (activePanel === "empresa") {
      if (isStudentAccount) {
        return (
          <div className="drawer-stack">
            <div className="protected-lock-card muted">
              <Building2 size={20} />
              <div>
                <strong>No necesitas empresa para estudiar</strong>
                <p>La cuenta estudiante funciona con correo y contraseña. Empresa, RUC, espacio de trabajo y conexión SUNAT quedan disponibles solo para cuentas empresa.</p>
              </div>
            </div>
          </div>
        );
      }
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
            <small>{activeCompany ? `RUC ${activeCompany.ruc} / ${activeCompany.regimen_tributario}` : "Crea tu empresa desde Primeros pasos."}</small>
          </div>
          <div className="context-card">
            <span className="overline">Espacio activo</span>
            <select
              value={activeContext?.active_workspace_id || activeWorkspace?.id || ""}
              onChange={(event) => selectWorkspace(event.currentTarget.value)}
              disabled={!authorized || !workspaces.length || loading}
              aria-label="Espacio de trabajo activo"
            >
              <option value="">{workspaces.length ? "Seleccionar espacio" : "Sin espacios"}</option>
              {workspaces.map((workspace) => (
                <option key={workspace.id} value={workspace.id}>{workspace.nombre}</option>
              ))}
            </select>
            <strong>{activeWorkspace?.nombre || "Pendiente"}</strong>
            <small>{activeWorkspace ? `${activeWorkspace.estado} / plan ${activeWorkspace.plan_id}` : "Crea un espacio ligado a empresa."}</small>
          </div>
          <button className="primary-button" type="button" onClick={() => openPanel("onboarding")}>
            Crear empresa o espacio
            <ArrowRight size={16} />
          </button>
          <button className="secondary-link" type="button" onClick={() => openPanel("sunat")}>
            <ShieldCheck size={16} />
            Ver seguridad SUNAT
          </button>
        </div>
      );
    }

    if (activePanel === "admin") {
      if (!canUseAdminPanel) {
        return (
          <div className="drawer-stack">
            <div className="protected-lock-card muted">
              <Lock size={20} />
              <div>
                <strong>Panel protegido</strong>
                <p>Disponible solo para usuarios CEO o administradores autorizados.</p>
              </div>
            </div>
          </div>
        );
      }
      return (
        <div className="drawer-stack">
          <div className="human-copy-card">
            <strong>Panel protegido</strong>
            <p>Admin CEO permite activar pruebas, revisar usuarios y consultar el estado tecnico sin mostrarlo en la Home.</p>
          </div>
          {renderAdminUserGrid()}
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
              Cerrar sesión
            </button>
          </div>
        ) : (
          <>
            <div className="human-copy-card">
              <strong>Acceso seguro</strong>
              <p>{accessMode === "student" ? "Entra con tu correo y contraseña para practicar ejercicios." : "Inicia sesión con tu cuenta DCFT. La conexión SUNAT se gestiona cifrada desde empresa."}</p>
            </div>
            <div className="drawer-grid access-choice-grid" aria-label="Opciones de acceso">
              <article className="context-card">
                <span className="overline">Estudiante</span>
                <strong>Entrar como estudiante</strong>
                <small>Correo, contraseña y cuenta gratis.</small>
              </article>
              {accessMode === "business" ? (
                <article className="context-card">
                  <span className="overline">Empresa</span>
                  <strong>Entrar como empresa</strong>
                  <small>RUC, Usuario SOL, Clave SOL, consentimiento y plan.</small>
                </article>
              ) : null}
              {accessMode === "admin" ? (
                <article className="context-card">
                  <span className="overline">Admin CEO</span>
                  <strong>Acceso protegido</strong>
                  <small>Solo administradores autorizados pueden activar pruebas Premium.</small>
                </article>
              ) : null}
            </div>
            {renderAccessForm()}
            {accessMode === "business" ? (
              <div className="empty-state">
                <ShieldCheck size={18} />
                <div>
                  <strong>Conexión empresarial segura</strong>
                  <span>{SUNAT_SAFE_COPY}</span>
                </div>
              </div>
            ) : null}
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
          {publicNavItems.map((item) => {
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
          <small>{authorized ? currentUser?.username || "Sesión activa" : "Inicia sesión para datos reales"}</small>
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
              <button className="icon-button" onClick={() => logout()} disabled={loading} title="Cerrar sesión">
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
        {publicSuccess ? <section className="calm-success" role="status">{publicSuccess}</section> : null}

        {!authorized ? renderGuestAccessPortal() : null}

        <section className={`official-home ${isStudentAccount ? "student-business-locked" : ""} ${accessMode === "student" || isStudentAccount ? "student-entry-active" : ""}`} id="dashboard" data-screen="dashboard">
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
              <span><Stethoscope size={17} /> Diagnóstico</span>
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
                    <StatusPill tone={signalItem.tone}>{signalItem.status}</StatusPill>
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
              <button className="alert-button" type="button" onClick={() => openPanel(isStudentAccount ? "ejercicios" : "diagnostico")}>
                {isStudentAccount ? "Ver ejercicios" : "Ver recomendación"}
                <ArrowRight size={17} />
              </button>
            </div>
          </section>

          <section className="health-card" id="diagnostic" data-screen="diagnostic" aria-label="Salud Empresarial">
            <div className="official-section-title">
              <span>Diagnóstico</span>
              <h2>Salud Empresarial</h2>
            </div>
            <div className="health-card__body">
              <div className={`score-ring ${businessScoreTone}`} style={{ "--score": `${businessScore}%` } as CSSProperties}>
                <strong>{businessScore}</strong>
                <span>de 100</span>
              </div>
              <div className="health-summary">
                <strong>{healthTitle}</strong>
                <p>{healthText}</p>
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

          <section className="quick-actions-panel" aria-label="Acciones rápidas">
            <div className="official-section-title">
              <span>Accesos</span>
              <h2>Acciones rápidas</h2>
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

          <section className={`doctor-card ${isStudentAccount ? "student-doctor-card" : ""}`} id="doctor" data-screen="doctor" aria-label={isStudentAccount ? "Doctor de estudio contable financiero tributario" : "Médico de Cabecera Empresarial"}>
            <div className="doctor-portrait" aria-hidden="true">
              <img src={DOCTOR_AVATAR_SRC} alt="" />
            </div>
            <div>
              <span>{isStudentAccount ? "Doctor de estudio" : "Médico de Cabecera Empresarial"}</span>
              <h2>{isStudentAccount ? "Doctor de estudio contable, financiero y tributario" : "Doctor DCFT"}</h2>
              <p>{isStudentAccount ? "Puedes hacer hasta 5 preguntas mensuales sobre contabilidad, finanzas y tributación." : "Doctor empresa IA pendiente de proveedor IA y autorizacion CEO. MYPE: 10 preguntas/mes. Premium: 30 preguntas/mes."}</p>
              <div className="daily-diagnosis">
                <strong>{isStudentAccount ? `Te quedan ${studentDoctorRemaining} de ${studentDoctorLimit} preguntas este mes.` : hasDiagnosticEvidence ? "Diagnóstico basado en datos autorizados" : "Esperando datos autorizados para diagnóstico completo."}</strong>
                <small>{isStudentAccount ? "Guía educativa paso a paso, sin diagnóstico empresarial, sin RUC y sin SUNAT real." : hasDiagnosticEvidence ? `Estado tributario: ${businessStatusLabel(taxTone)} / financiero: ${businessStatusLabel(financeTone)} / contable: ${businessStatusLabel(accountingTone)}` : "Esperando lectura autorizada. DCFT no declara, no paga, no emite y no modifica información."}</small>
              </div>
              <button className="primary-button" type="button" onClick={() => openPanel("doctor")}>
                {isStudentAccount ? "Preguntar al Doctor" : "Ver estado Doctor"}
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
              <p>{authorized ? `${currentUser?.role || "Rol"} / ${planName}` : "Inicia sesión para activar datos reales de empresa, espacio de trabajo y permisos."}</p>
            </div>
            {!authorized ? (
              <form className="mini-login" onSubmit={login}>
                <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label="Usuario mobile" placeholder="Usuario" autoComplete="username" />
                <PasswordField
                  value={password}
                  onChange={setPassword}
                  visible={loginPasswordVisible}
                  onToggle={() => setLoginPasswordVisible((visible) => !visible)}
                  ariaLabel="Contraseña mobile"
                  placeholder="Contraseña"
                  autoComplete="current-password"
                />
                <button className="primary-button" type="submit" disabled={loading || !username || !password}>
                  <Lock size={16} />
                  Entrar
                </button>
                {renderResendVerificationAction()}
                <a className="secondary-link" href="#onboarding">Crear cuenta</a>
              </form>
            ) : (
              <StatusPill tone="green">Sesión activa</StatusPill>
            )}
          </section>

          {authorized ? (
            <section className={`trial-banner ${trialExpired ? "expired" : trialActive ? "active" : ""}`} aria-label="Estado de la prueba">
              <span>{trialActive ? "Premium prueba" : trialExpired ? "Prueba vencida" : "Prueba Premium 7 días disponible"}</span>
              <strong>{trialActive ? `${trialDaysRemaining} días restantes` : `Plan base ${featureLabel(basePlanId)}`}</strong>
              <small>Plan efectivo: {featureLabel(effectivePlanId)}. Al vencer, vuelve al plan base y conserva historial; los módulos Premium se bloquean.</small>
              {!trialActive ? (
                <button className="alert-button" type="button" onClick={() => openPanel("admin")}>
                  Solicitar prueba
                  <ArrowRight size={16} />
                </button>
              ) : null}
            </section>
          ) : null}
          {renderSubscriptionNotice()}
          {isInternalAccount ? (
            <section className="trial-banner active" aria-label="Admin CEO premium interno">
              <span>Admin CEO interno</span>
              <strong>Premium operativo sin pago</strong>
              <small>Mercado Pago no requerido para esta cuenta interna protegida.</small>
            </section>
          ) : null}

          <section className="plans-preview" aria-label="Niveles de acceso">
            {accessPlans.map((plan) => (
              <article className={`plan-preview-card ${plan.id === effectivePlanId ? "active" : ""}`} key={plan.id}>
                <span>{plan.id === effectivePlanId ? "Plan efectivo" : "Plan disponible"}</span>
                <strong>{plan.name}</strong>
                {renderPlanPriceLabels(plan)}
                <small>{planDisplayDescription(plan.id)}</small>
                {plan.trial_days ? <small>Prueba Premium {plan.trial_days} días</small> : null}
                {renderCheckoutActions(plan)}
              </article>
            ))}
            {isStudentAccount || (!authorized && accessMode === "student") ? (
              <button className="secondary-link plans-action" type="button" onClick={() => (authorized ? openPanel("premium") : chooseAccessMode("business"))}>
                Ver planes empresa
              </button>
            ) : null}
          </section>
        </section>

        <section className="executive-hero technical-zone" id="legacy-dashboard" data-screen="dashboard-legacy">
          <div className="hero-primary">
            <div className="hero-copy">
              <span className="overline">Panel ejecutivo</span>
              <h2>{summary?.tenant_id || currentUser?.tenant_id || "Espacio empresarial"}</h2>
              <p>{authorized ? "Lectura operativa de la empresa activa." : "Acceso seguro para operar empresas, espacios de trabajo y gobierno tributario."}</p>
            </div>
            <div className="signal-panel">
              <span>Semaforo empresarial</span>
              <strong>{toneLabel(signal)}</strong>
              <StatusPill tone={signal}>{authorized ? "Datos reales" : "Pendiente"}</StatusPill>
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
              <span className="overline">Espacio activo</span>
              <select
                value={activeContext?.active_workspace_id || activeWorkspace?.id || ""}
                onChange={(event) => selectWorkspace(event.currentTarget.value)}
                disabled={!authorized || !workspaces.length || loading}
                aria-label="Espacio de trabajo activo"
              >
                <option value="">{workspaces.length ? "Seleccionar espacio" : "Sin espacios"}</option>
                {workspaces.map((workspace) => (
                  <option key={workspace.id} value={workspace.id}>{workspace.nombre}</option>
                ))}
              </select>
              <strong>{activeWorkspace?.nombre || "Pendiente"}</strong>
              <small>{activeWorkspace ? `${activeWorkspace.estado} / plan ${activeWorkspace.plan_id}` : "Crea un espacio ligado a empresa."}</small>
            </article>

            <article className="context-card">
              <span className="overline">Sesión</span>
              {!authorized ? (
                <form className="compact-login" onSubmit={login}>
                  <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label="Usuario" placeholder="Usuario" autoComplete="username" />
                  <PasswordField
                    value={password}
                    onChange={setPassword}
                    visible={loginPasswordVisible}
                    onToggle={() => setLoginPasswordVisible((visible) => !visible)}
                    ariaLabel="Contraseña"
                    placeholder="Contraseña"
                    autoComplete="current-password"
                  />
                  <button className="primary-button" type="submit" disabled={loading || !username || !password}>
                    <Lock size={16} />
                    Entrar
                  </button>
                  {renderResendVerificationAction()}
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
            <SectionHeader eyebrow="Centro de navegación" title="Identidad operacional">
              Roles, planes, empresa y espacio de trabajo quedan gobernados por backend.
            </SectionHeader>
            <div className="identity-grid">
              <InfoCard icon={<Building2 size={22} />} eyebrow="Empresas" title={formatNumber(companies.length)} detail={activeCompany?.razon_social || "Sin empresa activa"} tone={companies.length ? "green" : "yellow"} meta="RUC único por empresa" />
              <InfoCard icon={<Gauge size={22} />} eyebrow="Espacios" title={formatNumber(workspaces.length)} detail={activeWorkspace?.nombre || "Sin espacio activo"} tone={workspaces.length ? "green" : "yellow"} meta="Permiso requerido" />
              <InfoCard icon={<ShieldCheck size={22} />} eyebrow="Permisos" title={permissions?.enforced_by_backend ? "Backend" : "Pendiente"} detail={`${formatNumber(rolePermissions.length)} permisos visibles para el usuario.`} tone={permissions?.enforced_by_backend ? "green" : "yellow"} meta={currentUser?.role || "Sin rol"} />
            </div>
          </article>

          <article className="command-panel" id="sunat" data-screen="sunat">
            <SectionHeader eyebrow="SUNAT seguro" title="Conexión SUNAT con Clave SOL" action={<StatusPill tone={currentSunatTone}>{compactStatus(sunatCredentialStatus?.status || sunatStatus?.status || "NOT_CONNECTED")}</StatusPill>}>
              DCFT no declara. DCFT no paga. DCFT no modifica información. Solo lee información consultable autorizada.
            </SectionHeader>
            {renderSunatCredentialState()}
            {renderSunatReadonlyIntelligence()}
            {renderSunatApiAutomation()}
            <form className="sunat-prep-form" onSubmit={storeSunatAuxiliaryCredentials}>
              <p>{SUNAT_SAFE_COPY}</p>
              <input
                value={sunatAuxForm.ruc || activeCompany?.ruc || ""}
                onChange={(event) => setSunatAuxForm({ ...sunatAuxForm, ruc: event.target.value })}
                aria-label="RUC SUNAT"
                placeholder="RUC"
                disabled={!authorized || !activeCompany || loading}
                inputMode="numeric"
              />
              <input
                value={sunatAuxForm.auxiliary_user_alias}
                onChange={(event) => setSunatAuxForm({ ...sunatAuxForm, auxiliary_user_alias: event.target.value })}
                aria-label="Usuario SOL"
                placeholder="Usuario SOL"
                disabled={!authorized || !activeCompany || loading}
                autoComplete="off"
              />
              <PasswordField
                value={sunatAuxForm.sunat_password}
                onChange={(value) => setSunatAuxForm({ ...sunatAuxForm, sunat_password: value })}
                visible={sunatPasswordVisible}
                onToggle={() => setSunatPasswordVisible((visible) => !visible)}
                ariaLabel="Clave SOL"
                placeholder="Clave SOL"
                disabled={!authorized || !activeCompany || loading}
                autoComplete="new-password"
              />
              <input
                value={compactStatus(sunatCredentialStatus?.status || sunatStatus?.status || "NOT_CONNECTED")}
                aria-label="Estado conexión SUNAT"
                placeholder="Preparado para piloto controlado"
                disabled
                readOnly
              />
              <label className="check-row">
                <input
                  type="checkbox"
                  checked={sunatAuxForm.consent_accepted}
                  onChange={(event) => setSunatAuxForm({ ...sunatAuxForm, consent_accepted: event.target.checked })}
                  disabled={!authorized || loading}
                />
                <span>Autorizo a DCFT a usar mi RUC, Usuario SOL y Clave SOL para consultar información tributaria disponible en SUNAT, guardar evidencia, generar diagnósticos y mostrar recomendaciones. DCFT no realizará pagos, declaraciones, emisiones, modificaciones ni acciones irreversibles sin autorización expresa.</span>
              </label>
              <div className="sunat-guide-box">
                <strong>Guía</strong>
                <span>{sunatCredentialStatus?.sunat_username_masked ? `Usuario SOL seguro: ${sunatCredentialStatus.sunat_username_masked}` : "Ingresa Usuario SOL y Clave SOL solo si autorizas la consulta automática."}</span>
              </div>
              <button className="secondary-link" type="button" onClick={disconnectSunatAuxiliaryCredentials} disabled={!authorized || !activeCompany || loading || !sunatCredentialStatus?.id}>
                Desconectar SUNAT
              </button>
            <button className="primary-button" type="submit" disabled={!canAttemptSunatAux || loading}>
                <ShieldCheck size={17} />
                Guardar acceso seguro
              </button>
              <small>La Clave SOL se cifra y no se muestra después de guardar. Puedes desconectar SUNAT cuando quieras.</small>
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
            <RecordList records={alerts} kind="alert" emptyText="No existen alertas abiertas en este espacio de trabajo." />
          </article>

          <article className="command-panel" id="recommendations" data-screen="recommendations">
            <SectionHeader eyebrow="Recomendaciones" title="Revision profesional" />
            <RecordList records={recommendations} kind="recommendation" emptyText="No existen recomendaciones registradas para esta empresa." />
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
          <SectionHeader eyebrow="Estado del plan" title="Planes y límites">
            Plan comercial activo y límites leídos desde backend.
          </SectionHeader>
          <div className="plans-grid">
            {accessPlans.map((plan) => (
              <article className={`plan-card ${plan.id === effectivePlanId ? "active" : ""}`} key={plan.id}>
              <div className="plan-card__top">
                <span>{plan.id === effectivePlanId ? "Plan efectivo" : "Plan disponible"}</span>
                <StatusPill tone={plan.id.includes("premium") ? "yellow" : "neutral"}>{plan.name}</StatusPill>
              </div>
              <h3>{plan.name}</h3>
              <p>{planDisplayDescription(plan.id)}</p>
              {renderPlanPriceLabels(plan)}
              {plan.trial_days ? <small>Prueba inicial: {plan.trial_days} días.</small> : null}
              {renderCheckoutActions(plan)}
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
            <SectionHeader eyebrow="Admin CEO" title="Usuarios y pruebas">
              Panel protegido por backend para pruebas controladas.
            </SectionHeader>
            {renderAdminUserGrid()}
          </section>
        ) : null}

        <section className="workspace-grid">
          <article className="command-panel" id="onboarding" data-screen="onboarding">
            <SectionHeader eyebrow="Primeros pasos" title={onboardingForm.account_type === "student" || onboardingForm.plan === "student" ? "Crear cuenta estudiante" : "Alta de empresa"} />
            {renderOnboardingForm()}
            {onboardingForm.account_type === "student" || onboardingForm.plan === "student" ? (
              <>
                <div className="empty-state student-only-note">
                  <ClipboardList size={18} />
                  <div>
                    <strong>Beneficios preparados</strong>
                    <span>Tu cuenta estudiante entra con correo y contraseña.</span>
                  </div>
                </div>
                {authorized ? renderStudentExerciseSpotlight() : renderStudentBenefitsPreview("compact")}
              </>
            ) : (
              <>
                <div className="empty-state">
                  <Landmark size={18} />
                  <div>
                    <strong>SUNAT seguro</strong>
                    <span>DCFT no declara. DCFT no paga. DCFT no modifica información. Solo lee información consultable autorizada.</span>
                  </div>
                </div>
                {renderBusinessGuidePreview()}
              </>
            )}
            {onboardingProgress ? (
              <div className="checklist-grid" aria-label="Checklist de primeros pasos">
                {Object.entries(onboardingProgress.checklist).map(([key, value]) => (
                  <span className={value ? "done" : "pending"} key={key}>
                    <CheckCircle2 size={15} />
                    {featureLabel(key)}
                  </span>
                ))}
              </div>
            ) : null}
            <div className="video-slot-list" aria-label="Guías de primeros pasos">
              {onboardingVideos.map((video) => (
                <article className={`video-card ${video.seen ? "seen" : ""}`} key={video.id}>
                  <span>{video.duration_hint} / {video.status === "available" ? "Disponible" : "Pendiente"}</span>
                  <strong>{video.title}</strong>
                  <p>{video.description}</p>
                  {openGuideId === video.id ? <p className="written-guide">{video.written_guide || "Guía escrita preparada para piloto controlado."}</p> : null}
                  <button className="secondary-link" type="button" onClick={() => setOpenGuideId(openGuideId === video.id ? "" : video.id)}>
                    {openGuideId === video.id ? "Ocultar guía" : video.button_label}
                  </button>
                </article>
              ))}
            </div>
          </article>

          <article className="command-panel" id="analytics" data-screen="analytics">
            <SectionHeader eyebrow="Adopcion" title="Analitica de producto" />
            <div className="analytics-grid">
              <MetricTile label="Eventos" value={formatNumber(analytics?.events_total)} tone="green" icon={<BarChart3 size={20} />} />
              <MetricTile label="Fallos" value={formatNumber(analytics?.failures_total)} tone={(analytics?.failures_total ?? 0) > 0 ? "red" : "green"} icon={<AlertTriangle size={20} />} />
              <MetricTile label="Primeros pasos" value={analytics?.activation.onboarding_completed ? "Completo" : "Pendiente"} tone={analytics?.activation.onboarding_completed ? "green" : "yellow"} icon={<CheckCircle2 size={20} />} />
            </div>
          </article>
        </section>

        <section className="command-panel" id="runtime" data-screen="runtime">
          <SectionHeader eyebrow="Runtime" title="Postura técnica">
            Health, database, IA, OCR y observabilidad.
          </SectionHeader>
          <div className="runtime-grid">
            <InfoCard icon={<Activity size={22} />} eyebrow="Backend" title={health?.status || "checking"} detail={`DB ${compactStatus(runtime?.database?.backend)} / ${compactStatus(runtime?.database?.status)}`} tone={backendOk ? "green" : "yellow"} />
            <InfoCard icon={<Lock size={22} />} eyebrow="IA" title={compactStatus(runtime?.ai_pipeline)} detail="Proveedor gobernado por runtime." tone={aiTone} />
            <InfoCard icon={<ClipboardList size={22} />} eyebrow="OCR" title={compactStatus(runtime?.ocr_pipeline)} detail="Documentos con metadata verificable." tone={ocrTone} />
            <InfoCard icon={<Clock3 size={22} />} eyebrow="Observabilidad" title={`${formatNumber(runtime?.persistent_observability?.events_total)} eventos`} detail={`${runtime?.persistent_observability?.avg_latency_ms ?? 0} ms promedio.`} tone={databaseTone} />
          </div>
        </section>

        <footer className="quiet-footer">
          <span>API: {API_URL || "sin configurar"}</span>
          <span>{authorized ? `Cuenta: ${summary?.tenant_id || currentUser?.tenant_id || "activa"}` : "Sesión no iniciada"}</span>
        </footer>
      </div>

      {authorized ? (
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
            const panel = item.label === "Diagnóstico" ? "diagnostico" : item.label === "Reportes" ? "reportes" : item.label === "Ejercicios" ? "ejercicios" : "perfil";
            return (
              <button type="button" onClick={() => openPanel(panel as PanelKey)} key={item.href}>
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      ) : null}

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
              {publicSuccess ? <section className="calm-success" role="status">{publicSuccess}</section> : null}
              {renderPanelContent()}
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}

export default App;
