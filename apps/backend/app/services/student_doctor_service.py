from __future__ import annotations

import re
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.audit import append_audit_event_async
from app.core.config import settings
from app.db import repositories
from app.schemas.common import CurrentUser


DOCTOR_NAME = "Doctor de estudio contable, financiero y tributario"
STUDENT_DOCTOR_LIMIT = 5
QUOTA_EXCEEDED_MESSAGE = "Has usado tus 5 preguntas del mes. Podrás volver a preguntar el próximo mes o pasar a un plan empresa cuando esté disponible."
AI_PROVIDER_MISSING_MESSAGE = "Falta configurar proveedor IA para activar el Doctor."
EDUCATIONAL_DISCLAIMER = "Orientacion educativa. Para decisiones tributarias o legales en Peru, verifica la norma vigente o consulta a un profesional."


def _safe_error_text(value: str) -> str:
    compact = " ".join(str(value or "").split())
    compact = re.sub(r"sk-or-[A-Za-z0-9._-]+", "sk-or-REDACTED", compact)
    compact = re.sub(r"sk-[A-Za-z0-9._-]+", "sk-REDACTED", compact)
    compact = re.sub(r"[A-Za-z0-9_\-]{32,}", "REDACTED", compact)
    return compact[:180]


class StudentDoctorService:
    async def status(self, user: CurrentUser) -> dict:
        self._ensure_student_user(user)
        quota = await repositories.student_doctor_usage_status(user.user_id, user.tenant_id, STUDENT_DOCTOR_LIMIT)
        provider = self._provider_config()
        provider_ready = bool(provider)
        return {
            "doctor_name": DOCTOR_NAME,
            "available": provider_ready,
            "ai_provider_missing": not provider_ready,
            "provider": provider["provider"] if provider else None,
            "model": provider["model"] if provider else None,
            "quota": quota,
            "message": "Puedes hacer hasta 5 preguntas mensuales sobre contabilidad, finanzas y tributacion." if provider_ready else AI_PROVIDER_MISSING_MESSAGE,
        }

    async def ask(self, user: CurrentUser, question: str) -> dict:
        self._ensure_student_user(user)
        normalized_question = " ".join(question.strip().split())
        quota = await repositories.student_doctor_usage_status(user.user_id, user.tenant_id, STUDENT_DOCTOR_LIMIT)
        if quota["questions_used"] >= quota["questions_limit"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": "student_doctor_quota_exceeded", "message": QUOTA_EXCEEDED_MESSAGE, "quota": quota},
            )

        provider = self._provider_config()
        if provider is None:
            await repositories.record_runtime_event(
                "product.student_doctor_provider_missing",
                "warning",
                {"user_id": user.user_id, "ai_provider_missing": True},
                tenant_id=user.tenant_id,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "ai_provider_missing", "ai_provider_missing": True, "message": AI_PROVIDER_MISSING_MESSAGE, "quota": quota},
            )

        try:
            provider_response = await self._call_provider(provider, normalized_question)
        except HTTPException:
            raise
        except Exception as exc:
            safe_reason = _safe_error_text(str(exc.__class__.__name__))
            await repositories.record_runtime_event(
                "product.student_doctor_provider_error",
                "error",
                {"provider": provider["provider"], "reason": safe_reason},
                tenant_id=user.tenant_id,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": "student_doctor_provider_error", "message": "El proveedor IA no respondio correctamente. No se desconto ninguna pregunta.", "quota": quota},
            ) from exc

        answer = str(provider_response.get("answer") or "").strip()
        if not answer:
            await repositories.record_runtime_event(
                "product.student_doctor_empty_response",
                "error",
                {"provider": provider["provider"]},
                tenant_id=user.tenant_id,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": "student_doctor_empty_response", "message": "El proveedor IA no devolvio una respuesta util. No se desconto ninguna pregunta.", "quota": quota},
            )

        updated_quota = await repositories.record_student_doctor_success(user.user_id, user.tenant_id, normalized_question, STUDENT_DOCTOR_LIMIT)
        await repositories.create_ai_request(
            {
                "requested_by": user.username,
                "scope": "student_doctor",
                "question": normalized_question,
                "model": provider_response.get("model") or provider["model"],
                "educational_only": True,
            },
            user.tenant_id,
            provider["provider"],
            "completed",
        )
        await append_audit_event_async(
            "student.doctor.question_answered",
            user.username,
            {"questions_used": updated_quota["questions_used"], "questions_limit": updated_quota["questions_limit"], "provider": provider["provider"]},
            risk="medium",
            tenant_id=user.tenant_id,
        )
        await repositories.record_runtime_event(
            "product.student_doctor_question_answered",
            "ok",
            {"questions_used": updated_quota["questions_used"], "provider": provider["provider"]},
            tenant_id=user.tenant_id,
        )
        return {
            "doctor_name": DOCTOR_NAME,
            "answer": answer,
            "provider": provider["provider"],
            "model": provider_response.get("model") or provider["model"],
            "quota": updated_quota,
            "educational_disclaimer": EDUCATIONAL_DISCLAIMER,
        }

    def _ensure_student_user(self, user: CurrentUser) -> None:
        if user.plan not in {"student", "free_student"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "student_doctor_student_plan_required", "message": "El Doctor de estudio esta disponible solo para cuenta estudiante."},
            )

    def _provider_config(self) -> dict[str, Any] | None:
        if not settings.ai_provider_enabled:
            return None
        provider = (settings.ai_provider or "openrouter").strip().lower()
        if provider == "openrouter":
            api_key = settings.openrouter_api_key.strip()
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
            api_key = settings.openai_api_key.strip()
            if not api_key:
                return None
            return {"provider": "openai", "api_key": api_key, "model": settings.ai_model.strip() or settings.openai_model, "timeout": settings.ai_request_timeout_seconds}
        if provider == "anthropic":
            api_key = settings.anthropic_api_key.strip()
            if not api_key:
                return None
            return {"provider": "anthropic", "api_key": api_key, "model": settings.ai_model.strip() or settings.anthropic_model, "timeout": settings.ai_request_timeout_seconds}
        if provider == "gemini":
            api_key = settings.gemini_api_key.strip()
            if not api_key:
                return None
            return {"provider": "gemini", "api_key": api_key, "model": settings.ai_model.strip() or settings.gemini_model, "timeout": settings.ai_request_timeout_seconds}
        return None

    async def _call_provider(self, provider: dict[str, Any], question: str) -> dict:
        provider_id = provider["provider"]
        if provider_id in {"openrouter", "openai"}:
            return await self._call_openai_compatible(provider, question)
        if provider_id == "anthropic":
            return await self._call_anthropic(provider, question)
        if provider_id == "gemini":
            return await self._call_gemini(provider, question)
        raise RuntimeError("unsupported_provider")

    def _system_prompt(self) -> str:
        return (
            "Eres el Doctor de estudio contable, financiero y tributario de DCFT para estudiantes. "
            "Responde en espanol claro, educativo y paso a paso. "
            "Puedes explicar contabilidad, finanzas y tributacion con ejemplos simples. "
            "No hagas diagnosticos empresariales, no pidas RUC, no uses SUNAT real, no declares, no pagues y no modifiques informacion oficial. "
            "No presentes asesoramiento legal o tributario definitivo; si la pregunta toca impuestos de Peru, indica que la norma vigente debe verificarse."
        )

    async def _call_openai_compatible(self, provider: dict[str, Any], question: str) -> dict:
        base_url = provider.get("base_url") or "https://api.openai.com/v1"
        if provider["provider"] == "openai":
            base_url = "https://api.openai.com/v1"
        headers = {"Authorization": f"Bearer {provider['api_key']}", "Content-Type": "application/json"}
        headers.update(provider.get("headers") or {})
        payload = {
            "model": provider["model"],
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": question},
            ],
            "max_tokens": 900,
            "temperature": 0.3,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=provider["timeout"]) as client:
            response = await client.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
            if response.status_code >= 400:
                raise RuntimeError(f"provider_http_error_{response.status_code}:{_safe_error_text(response.text)}")
            data = response.json()
        choices = data.get("choices") or []
        answer = ""
        if choices:
            answer = str((choices[0].get("message") or {}).get("content") or "").strip()
        return {"answer": answer, "model": data.get("model") or provider["model"]}

    async def _call_anthropic(self, provider: dict[str, Any], question: str) -> dict:
        payload = {
            "model": provider["model"],
            "max_tokens": 900,
            "system": self._system_prompt(),
            "messages": [{"role": "user", "content": question}],
        }
        headers = {"x-api-key": provider["api_key"], "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=provider["timeout"]) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            if response.status_code >= 400:
                raise RuntimeError(f"provider_http_error_{response.status_code}:{_safe_error_text(response.text)}")
            data = response.json()
        parts = [item.get("text", "") for item in data.get("content", []) if item.get("type") == "text"]
        return {"answer": "\n".join(part for part in parts if part).strip(), "model": data.get("model") or provider["model"]}

    async def _call_gemini(self, provider: dict[str, Any], question: str) -> dict:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{provider['model']}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": self._system_prompt()}]},
            "contents": [{"role": "user", "parts": [{"text": question}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 900},
        }
        async with httpx.AsyncClient(timeout=provider["timeout"]) as client:
            response = await client.post(url, params={"key": provider["api_key"]}, json=payload)
            if response.status_code >= 400:
                raise RuntimeError(f"provider_http_error_{response.status_code}:{_safe_error_text(response.text)}")
            data = response.json()
        candidates = data.get("candidates") or []
        parts = (((candidates[0] if candidates else {}).get("content") or {}).get("parts") or [])
        answer = "\n".join(str(part.get("text") or "") for part in parts).strip()
        return {"answer": answer, "model": provider["model"]}


student_doctor_service = StudentDoctorService()
