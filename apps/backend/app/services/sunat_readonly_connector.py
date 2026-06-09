from __future__ import annotations

from dataclasses import dataclass, field
import html
import re
from urllib.parse import urljoin

import httpx

from app.core.config import settings


SUNAT_SOL_ENTRY_URL = "https://www.sunat.gob.pe/sol.html"
SUNAT_LOGIN_URL = (
    "https://ww1.sunat.gob.pe/xssecurity/SignOnVerification.htm"
    "?signonForwardAction=https%3A%2F%2Fwww.sunat.gob.pe%2Fol-ti-itlige%2Flige.do"
)
SUNAT_SIGNON_FALLBACK_URL = "https://ww1.sunat.gob.pe/xssecurity/signon.htm"
READ_ONLY_KEYWORDS = ("consulta", "consulto", "reporte", "reportes", "ficha", "validez", "captura", "acuse", "estado")
SENSITIVE_ACTION_KEYWORDS = (
    "declarar",
    "declaracion y pago",
    "declaración y pago",
    "pagar",
    "pago",
    "emitir",
    "emision",
    "emisión",
    "modificar",
    "administracion de usuarios",
    "administración de usuarios",
    "crear usuario",
    "dar de baja",
    "fraccionamiento",
    "aplazamiento",
    "recurso",
    "impugnatorio",
    "solicitud",
    "aceptar",
)


@dataclass(frozen=True)
class SunatReadOnlyConnectorResult:
    status: str
    real_connector_enabled: bool
    real_sunat_session: bool
    read_only: bool
    remote_actions_enabled: bool
    reason: str
    http_status: int | None = None
    captcha_required: bool = False
    available_permissions: list[dict] = field(default_factory=list)
    snapshots: list[dict] = field(default_factory=list)
    normalized_facts: list[dict] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


def _clean_text(value: str) -> str:
    decoded = html.unescape(value)
    decoded = re.sub(r"<script\b.*?</script>", " ", decoded, flags=re.IGNORECASE | re.DOTALL)
    decoded = re.sub(r"<style\b.*?</style>", " ", decoded, flags=re.IGNORECASE | re.DOTALL)
    decoded = re.sub(r"<[^>]+>", " ", decoded)
    decoded = re.sub(r"\s+", " ", decoded)
    return decoded.strip()


def _title_from_html(body: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.IGNORECASE | re.DOTALL)
    return _clean_text(match.group(1)) if match else ""


def _form_action(body: str, base_url: str) -> str:
    match = re.search(r"<form[^>]+action=[\"']([^\"']+)[\"']", body, flags=re.IGNORECASE)
    if not match:
        return SUNAT_SIGNON_FALLBACK_URL
    return urljoin(base_url, html.unescape(match.group(1)))


def _input_names(body: str) -> list[str]:
    names = re.findall(r"<input[^>]+name=[\"']([^\"']+)[\"']", body, flags=re.IGNORECASE)
    return sorted({html.unescape(name) for name in names if name})


def _hidden_form_values(body: str) -> dict[str, str]:
    values: dict[str, str] = {}
    input_re = re.compile(r"<input\b([^>]+)>", flags=re.IGNORECASE)
    for input_match in input_re.finditer(body):
        attrs = input_match.group(1)
        type_match = re.search(r"type=[\"']([^\"']+)[\"']", attrs, flags=re.IGNORECASE)
        if type_match and type_match.group(1).lower() != "hidden":
            continue
        name_match = re.search(r"name=[\"']([^\"']+)[\"']", attrs, flags=re.IGNORECASE)
        if not name_match:
            continue
        value_match = re.search(r"value=[\"']([^\"']*)[\"']", attrs, flags=re.IGNORECASE)
        values[html.unescape(name_match.group(1))] = html.unescape(value_match.group(1)) if value_match else ""
    return values


def _extract_permission_candidates(body: str) -> list[dict]:
    cleaned = _clean_text(body)
    chunks = [
        item.strip(" -:|")
        for item in re.split(r"(?:\s{2,}|[>\n\r\t]+|•|\\u2022)", cleaned)
        if 4 <= len(item.strip()) <= 180
    ]
    seen: set[str] = set()
    permissions: list[dict] = []
    for chunk in chunks:
        normalized = chunk.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        is_read = any(keyword in normalized for keyword in READ_ONLY_KEYWORDS)
        is_sensitive = any(keyword in normalized for keyword in SENSITIVE_ACTION_KEYWORDS) and not is_read
        if not is_read and not is_sensitive:
            continue
        permissions.append(
            {
                "permission_name": chunk,
                "permission_path": chunk,
                "permission_type": "consulta" if is_read else "sensitive_action",
                "is_available": True,
                "is_sensitive": is_sensitive,
                "can_read": is_read and not is_sensitive,
                "can_execute": False,
                "status": "available_readonly" if is_read and not is_sensitive else "sensitive_detected_blocked",
                "source": "sunat_menu",
            }
        )
    return permissions[:120]


class SunatReadOnlyConnector:
    read_only = True
    remote_actions_enabled = False

    def _blocked(self, reason: str = "real_sunat_connector_not_configured") -> SunatReadOnlyConnectorResult:
        return SunatReadOnlyConnectorResult(
            status="NOT_EXECUTED_FOUNDATION_ONLY",
            real_connector_enabled=False,
            real_sunat_session=False,
            read_only=True,
            remote_actions_enabled=False,
            reason=reason,
        )

    async def validate_credentials(self, *, ruc: str, username: str, password: str) -> SunatReadOnlyConnectorResult:
        _ = (ruc, username, password)
        if not settings.sunat_readonly_enabled:
            return self._blocked()
        return SunatReadOnlyConnectorResult(
            status="CREDENTIAL_RECEIVED_PENDING_READONLY_RUN",
            real_connector_enabled=True,
            real_sunat_session=False,
            read_only=True,
            remote_actions_enabled=False,
            reason="credentials_encrypted_run_required",
        )

    async def run_readonly_session(self, *, ruc: str, username: str, password: str) -> SunatReadOnlyConnectorResult:
        if not settings.sunat_readonly_enabled:
            return self._blocked()
        if settings.sunat_allow_sensitive_actions:
            return SunatReadOnlyConnectorResult(
                status="CONFIGURATION_BLOCKED",
                real_connector_enabled=False,
                real_sunat_session=False,
                read_only=True,
                remote_actions_enabled=False,
                reason="sunat_sensitive_actions_must_remain_disabled",
                findings=[
                    {
                        "severity": "critical",
                        "category": "security",
                        "title": "Acciones sensibles SUNAT bloqueadas",
                        "message": "SUNAT_ALLOW_SENSITIVE_ACTIONS debe permanecer false. DCFT no ejecuta acciones sensibles.",
                        "source": "sunat_readonly_connector",
                        "status": "open",
                    }
                ],
            )

        timeout = httpx.Timeout(18.0, connect=8.0)
        headers = {
            "User-Agent": "DCFT-ReadOnly-Connector/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            try:
                login_response = await client.get(SUNAT_LOGIN_URL)
            except httpx.HTTPError as exc:
                return SunatReadOnlyConnectorResult(
                    status="ERROR",
                    real_connector_enabled=True,
                    real_sunat_session=False,
                    read_only=True,
                    remote_actions_enabled=False,
                    reason="sunat_login_page_unreachable",
                    findings=[
                        {
                            "severity": "high",
                            "category": "connectivity",
                            "title": "No se pudo abrir SUNAT SOL",
                            "message": "SUNAT no respondió al punto de autenticación SOL en el tiempo esperado.",
                            "source": "sunat_readonly_connector",
                            "status": "open",
                            "metadata": {"error_type": type(exc).__name__},
                        }
                    ],
                )

            login_body = login_response.text
            captcha_required = "sunatcaptcha" in login_body.lower() or "divcaptcha" in login_body.lower()
            login_snapshot = {
                "url": str(login_response.url),
                "http_status": login_response.status_code,
                "title": _title_from_html(login_body),
                "captcha_required": captcha_required,
                "form_action": _form_action(login_body, str(login_response.url)),
                "input_names": _input_names(login_body),
                "body_text_excerpt": _clean_text(login_body)[:1000],
            }
            if captcha_required:
                return SunatReadOnlyConnectorResult(
                    status="BLOCKED_MANUAL_CHALLENGE",
                    real_connector_enabled=True,
                    real_sunat_session=False,
                    read_only=True,
                    remote_actions_enabled=False,
                    reason="sunat_captcha_or_manual_challenge_detected",
                    http_status=login_response.status_code,
                    captcha_required=True,
                    snapshots=[
                        {
                            "source": "sunat_login",
                            "snapshot_type": "login_preflight",
                            "content": login_snapshot,
                            "metadata": {"credentials_submitted": False, "password_logged": False},
                        }
                    ],
                    normalized_facts=[
                        {
                            "fact_type": "connector",
                            "fact_key": "sunat_manual_challenge",
                            "fact_value": {"captcha_required": True, "real_sunat_session": False},
                            "confidence": 100,
                            "status": "blocked",
                        }
                    ],
                    findings=[
                        {
                            "severity": "high",
                            "category": "sunat_access",
                            "title": "SUNAT exige validación humana",
                            "message": "El portal oficial muestra captcha o validación manual. DCFT no puede completar una sesión automática sin intervención autorizada.",
                            "source": "sunat_readonly_connector",
                            "status": "open",
                            "metadata": {"http_status": login_response.status_code, "captcha_required": True},
                        }
                    ],
                    metadata={"credentials_submitted": False, "password_logged": False},
                )

            form_data = _hidden_form_values(login_body)
            form_data.update(
                {
                    "action": form_data.get("action") or "login",
                    "tipo": form_data.get("tipo") or "2",
                    "ruc": ruc,
                    "usuario": username.upper(),
                    "clave": password,
                    "username": username.upper(),
                    "password": password,
                }
            )
            action_url = _form_action(login_body, str(login_response.url))
            try:
                signon_response = await client.post(action_url, data=form_data)
            except httpx.HTTPError as exc:
                return SunatReadOnlyConnectorResult(
                    status="ERROR",
                    real_connector_enabled=True,
                    real_sunat_session=False,
                    read_only=True,
                    remote_actions_enabled=False,
                    reason="sunat_signon_request_failed",
                    findings=[
                        {
                            "severity": "high",
                            "category": "connectivity",
                            "title": "SUNAT no aceptó la solicitud de inicio",
                            "message": "No se pudo completar la solicitud HTTP hacia SUNAT SOL.",
                            "source": "sunat_readonly_connector",
                            "status": "open",
                            "metadata": {"error_type": type(exc).__name__},
                        }
                    ],
                )

        body = signon_response.text
        body_text = _clean_text(body).lower()
        invalid_login = any(marker in body_text for marker in ("incorrect", "inválid", "invalid", "no es válido", "error"))
        session_ok = signon_response.status_code < 400 and not invalid_login and "sunat operaciones" in body_text
        permissions = _extract_permission_candidates(body) if session_ok else []
        snapshots = [
            {
                "source": "sunat_login",
                "snapshot_type": "login_preflight",
                "content": login_snapshot,
                "metadata": {"credentials_submitted": False, "password_logged": False},
            },
            {
                "source": "sunat_session",
                "snapshot_type": "authenticated_menu" if session_ok else "signon_response",
                "content": {
                    "url": str(signon_response.url),
                    "http_status": signon_response.status_code,
                    "title": _title_from_html(body),
                    "permission_candidates_count": len(permissions),
                    "body_text_excerpt": _clean_text(body)[:1000],
                },
                "metadata": {"credentials_submitted": True, "password_logged": False},
            },
        ]
        if not session_ok:
            return SunatReadOnlyConnectorResult(
                status="ERROR",
                real_connector_enabled=True,
                real_sunat_session=False,
                read_only=True,
                remote_actions_enabled=False,
                reason="sunat_session_not_established",
                http_status=signon_response.status_code,
                snapshots=snapshots,
                findings=[
                    {
                        "severity": "high",
                        "category": "sunat_access",
                        "title": "No se confirmó sesión SUNAT",
                        "message": "SUNAT respondió, pero DCFT no confirmó una sesión autenticada de solo lectura.",
                        "source": "sunat_readonly_connector",
                        "status": "open",
                        "metadata": {"http_status": signon_response.status_code},
                    }
                ],
                metadata={"credentials_submitted": True, "password_logged": False},
            )
        return SunatReadOnlyConnectorResult(
            status="CONNECTED_READ_ONLY",
            real_connector_enabled=True,
            real_sunat_session=True,
            read_only=True,
            remote_actions_enabled=False,
            reason="sunat_readonly_session_established",
            http_status=signon_response.status_code,
            available_permissions=permissions,
            snapshots=snapshots,
            normalized_facts=[
                {
                    "fact_type": "identity_tax",
                    "fact_key": "ruc",
                    "fact_value": {"ruc": ruc, "source": "credential_context"},
                    "confidence": 100,
                    "status": "normalized",
                },
                {
                    "fact_type": "permissions",
                    "fact_key": "available_menu_items",
                    "fact_value": {"count": len(permissions)},
                    "confidence": 80,
                    "status": "normalized",
                },
            ],
            findings=[],
            metadata={"credentials_submitted": True, "password_logged": False},
        )

    async def get_ruc_status(self, *, ruc: str) -> SunatReadOnlyConnectorResult:
        _ = ruc
        return self._blocked("use_sunat_readonly_run")

    async def get_tax_obligations(self, *, ruc: str) -> SunatReadOnlyConnectorResult:
        _ = ruc
        return self._blocked("use_sunat_readonly_run")

    async def get_basic_alerts(self, *, ruc: str) -> SunatReadOnlyConnectorResult:
        _ = ruc
        return self._blocked("use_sunat_readonly_run")

    async def disconnect(self, *, ruc: str) -> SunatReadOnlyConnectorResult:
        _ = ruc
        return self._blocked("local_disconnect_only")


sunat_readonly_connector = SunatReadOnlyConnector()
