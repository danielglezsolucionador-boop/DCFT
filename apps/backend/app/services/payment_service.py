from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request as urlrequest

from fastapi import HTTPException, status

from app.core.config import settings
from app.db import repositories
from app.schemas.common import CurrentUser


PAYMENT_PROVIDER_MISSING_MESSAGE = "Falta configurar proveedor de pago para activar checkout real."
PAYMENT_WEBHOOK_MISSING_MESSAGE = "Falta configurar webhook Stripe para activar pagos reales."
STRIPE_SIGNATURE_TOLERANCE_SECONDS = 300

PLAN_PRICES = {
    "student": {
        "currency": "PEN",
        "monthly": {"amount_cents": 0, "label": "S/ 0"},
        "annual": {"amount_cents": 0, "label": "S/ 0"},
    },
    "mype": {
        "currency": "PEN",
        "monthly": {"amount_cents": 8900, "label": "S/ 89 / mes"},
        "annual": {"amount_cents": 89000, "label": "S/ 890 / año"},
    },
    "premium": {
        "currency": "PEN",
        "monthly": {"amount_cents": 19900, "label": "S/ 199 / mes"},
        "annual": {"amount_cents": 199000, "label": "S/ 1,990 / año"},
    },
}


class PaymentService:
    def provider_status(self) -> dict:
        provider = settings.payment_provider.strip().lower()
        payment_public_key_missing = provider == "stripe" and not settings.payment_public_key.strip()
        payment_webhook_missing = provider == "stripe" and not settings.payment_webhook_secret.strip()
        return {
            "provider": provider or None,
            "payment_provider_missing": settings.payment_provider_missing,
            "payment_public_key_missing": payment_public_key_missing,
            "payment_webhook_missing": payment_webhook_missing,
            "provider_supported": provider in {"", "stripe"},
            "message": self._provider_status_message(provider, payment_public_key_missing, payment_webhook_missing),
            "plans": PLAN_PRICES,
        }

    def _provider_status_message(self, provider: str, payment_public_key_missing: bool, payment_webhook_missing: bool) -> str:
        if provider and provider != "stripe":
            return "Proveedor de pago configurado no soportado por este backend."
        if payment_public_key_missing:
            return "Falta configurar clave publica Stripe para activar checkout real."
        if settings.payment_provider_missing:
            return PAYMENT_WEBHOOK_MISSING_MESSAGE if payment_webhook_missing else PAYMENT_PROVIDER_MISSING_MESSAGE
        return "Proveedor de pago Stripe configurado con webhook."

    async def create_checkout(self, user: CurrentUser, plan: str, billing_cycle: str) -> dict:
        normalized_plan = {"business_basic": "mype", "business_premium": "premium"}.get(plan, plan)
        if normalized_plan == "student":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "student_plan_has_no_checkout", "message": "El plan estudiante es S/ 0 y no requiere checkout."},
            )
        if normalized_plan not in {"mype", "premium"}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "invalid_plan"})
        if billing_cycle not in {"monthly", "annual"}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "invalid_billing_cycle"})
        if settings.payment_provider_missing:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "payment_provider_missing",
                    "payment_provider_missing": True,
                    "message": PAYMENT_PROVIDER_MISSING_MESSAGE,
                },
            )

        provider = settings.payment_provider.strip().lower()
        price = PLAN_PRICES[normalized_plan][billing_cycle]
        currency = PLAN_PRICES[normalized_plan]["currency"]
        if provider == "stripe":
            session = self._create_stripe_checkout(user, normalized_plan, billing_cycle, int(price["amount_cents"]), currency)
            record = await repositories.create_checkout_session_record(
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                plan=normalized_plan,
                billing_cycle=billing_cycle,
                provider=provider,
                provider_session_id=session.get("id"),
                checkout_url=session.get("url"),
                amount_cents=int(price["amount_cents"]),
                currency=currency,
                status="pending",
                metadata={"provider_status": "created"},
            )
            return {
                **record,
                "payment_provider_missing": False,
                "message": "Checkout real creado por proveedor. El plan no se activa hasta confirmacion de pago.",
            }

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"error": "payment_provider_not_supported", "message": "Proveedor de pago configurado no soportado por este backend."},
        )

    async def handle_stripe_webhook(self, raw_body: bytes, signature_header: str | None) -> dict:
        if not settings.payment_webhook_secret.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "payment_webhook_missing", "payment_webhook_missing": True, "message": PAYMENT_WEBHOOK_MISSING_MESSAGE},
            )
        self._verify_stripe_signature(raw_body, signature_header)
        try:
            event = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invalid_webhook_payload"}) from exc

        event_id = str(event.get("id") or "")
        event_type = str(event.get("type") or "")
        if not event_id or not event_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invalid_webhook_event"})

        event_record = await repositories.record_stripe_webhook_event(event_id, event_type, event)
        if event_record["already_processed"]:
            return {"received": True, "status": "duplicate", "event_id": event_id, "event_type": event_type}

        if event_type != "checkout.session.completed":
            await repositories.mark_stripe_webhook_event(event_id, "ignored")
            return {"received": True, "status": "ignored", "event_id": event_id, "event_type": event_type}

        session_object = ((event.get("data") or {}).get("object") or {})
        if not isinstance(session_object, dict):
            await repositories.mark_stripe_webhook_event(event_id, "error", error="invalid_checkout_session_object")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invalid_checkout_session_object"})

        activation = await self._activate_checkout_session(event_id, event, session_object)
        if not activation.get("activated"):
            reason = str(activation.get("reason") or "checkout_activation_failed")
            await repositories.mark_stripe_webhook_event(event_id, "error", checkout_session_id=activation.get("checkout_session_id"), error=reason)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": reason, "activation": activation})

        await repositories.mark_stripe_webhook_event(event_id, "processed", checkout_session_id=activation.get("checkout_session_id"))
        return {"received": True, "status": "processed", "event_id": event_id, "event_type": event_type, "activation": activation}

    def _verify_stripe_signature(self, raw_body: bytes, signature_header: str | None) -> None:
        if not signature_header:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "stripe_signature_missing"})
        timestamp = None
        signatures: list[str] = []
        for part in signature_header.split(","):
            key, _, value = part.partition("=")
            if key == "t":
                timestamp = value
            elif key == "v1":
                signatures.append(value)
        if not timestamp or not signatures:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "stripe_signature_invalid"})
        try:
            timestamp_int = int(timestamp)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "stripe_signature_invalid"}) from exc
        if abs(int(time.time()) - timestamp_int) > STRIPE_SIGNATURE_TOLERANCE_SECONDS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "stripe_signature_expired"})
        signed_payload = f"{timestamp}.".encode("utf-8") + raw_body
        expected = hmac.new(settings.payment_webhook_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        if not any(hmac.compare_digest(expected, signature) for signature in signatures):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "stripe_signature_invalid"})

    async def _activate_checkout_session(self, event_id: str, event: dict, session_object: dict) -> dict:
        provider_session_id = str(session_object.get("id") or "")
        if not provider_session_id:
            return {"activated": False, "reason": "stripe_session_id_missing"}
        metadata = session_object.get("metadata") if isinstance(session_object.get("metadata"), dict) else {}
        billing_cycle = str(metadata.get("billing_cycle") or "monthly")
        current_period_start = self._timestamp_to_datetime(session_object.get("current_period_start"))
        current_period_end = self._timestamp_to_datetime(session_object.get("current_period_end"))
        paid_at = (
            self._timestamp_to_datetime(session_object.get("created"))
            or self._timestamp_to_datetime(event.get("created"))
            or datetime.now(timezone.utc)
        )
        if current_period_end is None:
            current_period_end = paid_at + (timedelta(days=365) if billing_cycle == "annual" else timedelta(days=30))
        plan = str(metadata.get("plan") or "")
        from app.services.subscription_service import subscription_service

        limits = subscription_service.limits_for(plan) if plan else {}
        return await repositories.activate_checkout_session_from_webhook(
            provider_session_id=provider_session_id,
            event_id=event_id,
            provider_customer_id=self._string_or_none(session_object.get("customer")),
            provider_subscription_id=self._string_or_none(session_object.get("subscription")),
            amount_cents=self._int_or_none(session_object.get("amount_total")),
            currency=self._string_or_none(session_object.get("currency")),
            paid_at=paid_at,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            limits=limits,
            metadata=metadata,
        )

    def _timestamp_to_datetime(self, value: object) -> datetime | None:
        if value is None:
            return None
        try:
            return datetime.fromtimestamp(int(value), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            return None

    def _int_or_none(self, value: object) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _string_or_none(self, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _create_stripe_checkout(self, user: CurrentUser, plan: str, billing_cycle: str, amount_cents: int, currency: str) -> dict:
        interval = "year" if billing_cycle == "annual" else "month"
        public_url = settings.app_public_url.rstrip("/")
        form = {
            "mode": "subscription",
            "success_url": f"{public_url}/?checkout=success&session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{public_url}/?checkout=cancelled",
            "client_reference_id": user.tenant_id,
            "customer_email": user.username,
            "line_items[0][price_data][currency]": currency.lower(),
            "line_items[0][price_data][product_data][name]": f"DCFT {plan.upper()} {billing_cycle}",
            "line_items[0][price_data][unit_amount]": str(amount_cents),
            "line_items[0][price_data][recurring][interval]": interval,
            "line_items[0][quantity]": "1",
            "metadata[tenant_id]": user.tenant_id,
            "metadata[user_id]": user.user_id,
            "metadata[plan]": plan,
            "metadata[billing_cycle]": billing_cycle,
        }
        payload = urllib.parse.urlencode(form).encode("utf-8")
        request = urlrequest.Request(
            "https://api.stripe.com/v1/checkout/sessions",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {settings.payment_secret_key}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urlrequest.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
            if response.status >= 400:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail={"error": "payment_provider_error", "message": "El proveedor de pago rechazo la creacion de checkout."},
                )
        data = json.loads(body)
        if not data.get("url"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": "payment_provider_error", "message": "El proveedor de pago no devolvio URL de checkout."},
            )
        return data


payment_service = PaymentService()
