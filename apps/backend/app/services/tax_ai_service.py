from __future__ import annotations

import re
from typing import Any

import httpx

from app.core.audit import append_audit_event_async
from app.core.config import settings
from app.db import repositories
from app.schemas.common import CurrentUser


PROVIDER_NOT_CONFIGURED_MESSAGE = "Proveedor IA no configurado"
TAX_AI_DISCLAIMER = "Orientacion contable/tributaria general. Verifica normativa vigente y valida con un profesional antes de tomar decisiones."
STRUCTURED_TAX_AI_HEADINGS = [
    "1. Diagnostico breve",
    "2. Riesgo tributario/contable",
    "3. Accion recomendada",
    "4. Documentos necesarios",
    "5. Proximo paso",
    "6. Advertencia",
]


def _safe_provider_error(value: str) -> str:
    compact = " ".join(str(value or "").split())
    compact = re.sub(r"sk-or-[A-Za-z0-9._-]+", "sk-or-REDACTED", compact)
    compact = re.sub(r"sk-[A-Za-z0-9._-]+", "sk-REDACTED", compact)
    compact = re.sub(r"[A-Za-z0-9_\-]{32,}", "REDACTED", compact)
    return compact[:180]


class TaxAIService:
    async def ask(self, user: CurrentUser, question: str, context: str = "") -> dict:
        normalized_question = " ".join(question.strip().split())
        normalized_context = " ".join(context.strip().split())
        provider = self._provider_config()
        if provider is None:
            await repositories.create_ai_request(
                {
                    "requested_by": user.username,
                    "scope": "tax_ai",
                    "question": normalized_question,
                    "context_provided": bool(normalized_context),
                    "configured": False,
                },
                user.tenant_id,
                "ai.disabled",
                "blocked_provider_disabled",
            )
            await repositories.record_runtime_event(
                "product.tax_ai_provider_missing",
                "warning",
                {"user_id": user.user_id, "provider": settings.ai_provider or "openrouter"},
                tenant_id=user.tenant_id,
            )
            return {
                "answer": PROVIDER_NOT_CONFIGURED_MESSAGE,
                "provider": (settings.ai_provider or "openrouter").strip().lower() or None,
                "model": None,
                "ai_provider_missing": True,
                "configured": False,
                "educational_disclaimer": TAX_AI_DISCLAIMER,
            }

        try:
            provider_response = await self._call_openai_compatible(provider, normalized_question, normalized_context)
        except Exception as exc:
            safe_reason = _safe_provider_error(str(exc))
            await repositories.record_runtime_event(
                "product.tax_ai_provider_error",
                "error",
                {"provider": provider["provider"], "reason": safe_reason},
                tenant_id=user.tenant_id,
            )
            return {
                "answer": "Proveedor IA no respondio correctamente",
                "provider": provider["provider"],
                "model": provider["model"],
                "ai_provider_missing": False,
                "configured": True,
                "educational_disclaimer": TAX_AI_DISCLAIMER,
            }

        answer = self._structured_answer(
            str(provider_response.get("answer") or "").strip(),
            normalized_question,
            normalized_context,
        )
        await repositories.create_ai_request(
            {
                "requested_by": user.username,
                "scope": "tax_ai",
                "question": normalized_question,
                "context_provided": bool(normalized_context),
                "model": provider_response.get("model") or provider["model"],
                "configured": True,
            },
            user.tenant_id,
            provider["provider"],
            "completed",
        )
        await append_audit_event_async(
            "ai.tax_question_answered",
            user.username,
            {"provider": provider["provider"], "model": provider_response.get("model") or provider["model"]},
            risk="medium",
            tenant_id=user.tenant_id,
        )
        return {
            "answer": answer,
            "provider": provider["provider"],
            "model": provider_response.get("model") or provider["model"],
            "ai_provider_missing": False,
            "configured": True,
            "educational_disclaimer": TAX_AI_DISCLAIMER,
        }

    def _provider_config(self) -> dict[str, Any] | None:
        if not settings.ai_provider_enabled:
            return None
        provider = (settings.ai_provider or "openrouter").strip().lower()
        if provider == "openrouter":
            api_key = (settings.ai_api_key or settings.openrouter_api_key).strip()
            if not api_key:
                return None
            return {
                "provider": "openrouter",
                "api_key": api_key,
                "base_url": settings.openrouter_base_url,
                "model": settings.ai_model.strip() or settings.openrouter_model,
                "timeout": settings.ai_request_timeout_seconds,
                "headers": {"HTTP-Referer": settings.openrouter_referer, "X-OpenRouter-Title": settings.openrouter_title},
            }
        if provider == "openai":
            api_key = (settings.ai_api_key or settings.openai_api_key).strip()
            if not api_key:
                return None
            return {
                "provider": "openai",
                "api_key": api_key,
                "base_url": "https://api.openai.com/v1",
                "model": settings.ai_model.strip() or settings.openai_model,
                "timeout": settings.ai_request_timeout_seconds,
                "headers": {},
            }
        return None

    def _system_prompt(self) -> str:
        return (
            "Eres el asistente contable y tributario minimo de DCFT. "
            "Responde en espanol claro, con orientacion general para Peru cuando aplique. "
            "Usa siempre seis secciones numeradas: 1. Diagnostico breve, 2. Riesgo tributario/contable, "
            "3. Accion recomendada, 4. Documentos necesarios, 5. Proximo paso, 6. Advertencia. "
            "Si faltan RUC, periodo, documentos o hechos verificables, dilo y pide esa informacion de forma concreta. "
            "No pidas ni reveles claves SOL, tokens, datos de tarjeta ni secretos. "
            "No indiques que DCFT declara, paga, emite o modifica informacion oficial. "
            "Aclara que la respuesta no reemplaza validacion profesional ni normativa vigente."
        )

    def _structured_answer(self, raw_answer: str, question: str, context: str) -> str:
        if not raw_answer:
            raw_answer = "No hay respuesta util del proveedor IA."
        normalized = raw_answer.lower()
        if all(heading.lower() in normalized for heading in STRUCTURED_TAX_AI_HEADINGS[:5]):
            return raw_answer
        missing_context = (
            "No se recibieron RUC, periodo, documentos contables ni evidencia tributaria suficiente."
            if not context
            else "La orientacion usa solo el contexto autorizado disponible; faltan documentos completos para cerrar diagnostico."
        )
        return "\n".join(
            [
                "1. Diagnostico breve",
                raw_answer,
                "",
                "2. Riesgo tributario/contable",
                f"{missing_context} No corresponde afirmar deudas, infracciones o saldos reales sin soporte verificable.",
                "",
                "3. Accion recomendada",
                "Validar los hechos con documentos fuente y separar diagnostico de cualquier accion oficial.",
                "",
                "4. Documentos necesarios",
                "RUC, periodo, comprobantes, libros o registros contables, constancias SUNAT y comunicaciones relevantes, si existen.",
                "",
                "5. Proximo paso",
                "Sube o registra la evidencia disponible y formula la consulta indicando periodo, operacion y objetivo de revision.",
                "",
                "6. Advertencia",
                "Esta orientacion no sustituye asesoria profesional final ni validacion normativa vigente cuando aplique.",
            ]
        )

    async def _call_openai_compatible(self, provider: dict[str, Any], question: str, context: str) -> dict:
        headers = {"Authorization": f"Bearer {provider['api_key']}", "Content-Type": "application/json"}
        headers.update(provider.get("headers") or {})
        user_content = question if not context else f"Contexto disponible: {context}\n\nPregunta: {question}"
        payload = {
            "model": provider["model"],
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": 900,
            "temperature": 0.2,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=provider["timeout"]) as client:
            response = await client.post(f"{provider['base_url'].rstrip('/')}/chat/completions", headers=headers, json=payload)
            if response.status_code >= 400:
                raise RuntimeError(f"provider_http_error_{response.status_code}:{_safe_provider_error(response.text)}")
            data = response.json()
        choices = data.get("choices") or []
        answer = ""
        if choices:
            answer = str((choices[0].get("message") or {}).get("content") or "").strip()
        return {"answer": answer, "model": data.get("model") or provider["model"]}


tax_ai_service = TaxAIService()
