from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from html import escape
import hashlib
import json
import secrets
import smtplib
import urllib.request as urlrequest

from app.core.config import settings
from app.db import repositories


EMAIL_PROVIDER_MISSING_MESSAGE = "Falta configurar proveedor de correo para activar cuentas."
EMAIL_NOT_VERIFIED_MESSAGE = "Confirma tu correo para activar tu cuenta."


def hash_verification_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class EmailService:
    def provider_status(self) -> dict:
        provider = settings.email_provider.strip().lower()
        return {
            "provider": provider or None,
            "email_provider_missing": settings.email_provider_missing,
            "message": EMAIL_PROVIDER_MISSING_MESSAGE if settings.email_provider_missing else "Proveedor de correo configurado.",
        }

    async def issue_verification_email(self, *, user_id: str, tenant_id: str, email: str) -> dict:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        token_record = await repositories.create_email_verification_token(
            user_id=user_id,
            tenant_id=tenant_id,
            token_hash=hash_verification_token(token),
            expires_at=expires_at,
        )
        send_result = self.send_verification_email(email=email, token=token)
        return {
            "required": True,
            "email_verified": False,
            "expires_at": token_record["expires_at"],
            **send_result,
        }

    def send_verification_email(self, *, email: str, token: str) -> dict:
        if settings.email_provider_missing:
            return {
                "sent": False,
                "email_provider_missing": True,
                "message": EMAIL_PROVIDER_MISSING_MESSAGE,
            }
        provider = settings.email_provider.strip().lower()
        verify_url = f"{settings.app_public_url.rstrip('/')}/?verify_email_token={token}"
        subject = "Confirma tu correo DCFT"
        text_body = (
            "Confirma tu correo para activar tu cuenta DCFT.\n\n"
            f"Abre este enlace: {verify_url}\n\n"
            "Si no creaste esta cuenta, ignora este mensaje."
        )
        html_body = (
            "<p>Confirma tu correo para activar tu cuenta DCFT.</p>"
            f'<p><a href="{escape(verify_url, quote=True)}">Confirmar correo</a></p>'
            "<p>Si no creaste esta cuenta, ignora este mensaje.</p>"
        )
        try:
            if provider == "smtp":
                self._send_smtp(email=email, subject=subject, text_body=text_body, html_body=html_body)
            elif provider == "resend":
                self._send_resend(email=email, subject=subject, text_body=text_body, html_body=html_body)
            else:
                return {
                    "sent": False,
                    "email_provider_missing": True,
                    "message": EMAIL_PROVIDER_MISSING_MESSAGE,
                }
        except Exception:
            return {
                "sent": False,
                "email_provider_missing": False,
                "email_delivery_error": True,
                "message": "No se pudo enviar el correo de verificacion.",
            }
        return {
            "sent": True,
            "email_provider_missing": False,
            "message": EMAIL_NOT_VERIFIED_MESSAGE,
        }

    def _send_smtp(self, *, email: str, subject: str, text_body: str, html_body: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.email_from
        message["To"] = email
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.starttls()
            if settings.smtp_user and settings.smtp_password:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)

    def _send_resend(self, *, email: str, subject: str, text_body: str, html_body: str) -> None:
        payload = json.dumps(
            {
                "from": settings.email_from,
                "to": [email],
                "subject": subject,
                "text": text_body,
                "html": html_body,
            }
        ).encode("utf-8")
        request = urlrequest.Request(
            "https://api.resend.com/emails",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {settings.email_api_key}",
                "Content-Type": "application/json",
            },
        )
        with urlrequest.urlopen(request, timeout=10) as response:
            if response.status >= 400:
                raise RuntimeError("email_provider_error")


email_service = EmailService()
