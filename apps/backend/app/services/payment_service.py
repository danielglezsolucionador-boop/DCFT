from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request as urlrequest

from fastapi import HTTPException, status

from app.core.config import settings
from app.db import repositories
from app.schemas.common import CurrentUser


PAYMENT_PROVIDER_MISSING_MESSAGE = "Falta configurar proveedor de pago para activar checkout real."
PAYMENT_WEBHOOK_MISSING_MESSAGE = "Falta configurar webhook del proveedor de pago para activar pagos reales."
STRIPE_WEBHOOK_MISSING_MESSAGE = "Falta configurar webhook Stripe para activar pagos reales."
MERCADOPAGO_WEBHOOK_MISSING_MESSAGE = "Falta configurar webhook Mercado Pago para activar pagos reales."
MERCADOPAGO_PROVIDER_ERROR_MESSAGE = "Mercado Pago rechazo la creacion de checkout."
STRIPE_SIGNATURE_TOLERANCE_SECONDS = 300
MERCADOPAGO_SIGNATURE_TOLERANCE_SECONDS = 300

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
        payment_public_key_missing = (
            (provider == "stripe" and not settings.payment_public_key.strip())
            or (provider == "mercadopago" and not settings.mercadopago_public_key.strip())
        )
        payment_webhook_missing = settings.payment_webhook_missing
        return {
            "provider": provider or None,
            "payment_provider_missing": settings.payment_provider_missing,
            "payment_public_key_missing": payment_public_key_missing,
            "payment_webhook_missing": payment_webhook_missing,
            "provider_supported": provider in {"", "stripe", "mercadopago"},
            "provider_primary": "mercadopago",
            "provider_secondary": "stripe",
            "message": self._provider_status_message(provider, payment_public_key_missing, payment_webhook_missing),
            "plans": PLAN_PRICES,
        }

    def _provider_status_message(self, provider: str, payment_public_key_missing: bool, payment_webhook_missing: bool) -> str:
        if provider and provider not in {"stripe", "mercadopago"}:
            return "Proveedor de pago configurado no soportado por este backend."
        if not provider:
            return PAYMENT_PROVIDER_MISSING_MESSAGE
        if provider == "mercadopago":
            if not settings.mercadopago_access_token.strip():
                return "Falta configurar access token Mercado Pago para activar checkout real."
            if payment_public_key_missing:
                return "Falta configurar clave publica Mercado Pago para activar checkout real."
            if payment_webhook_missing:
                return MERCADOPAGO_WEBHOOK_MISSING_MESSAGE
            if not settings.app_public_url.strip():
                return "Falta configurar APP_PUBLIC_URL para retorno de checkout."
            return "Proveedor de pago Mercado Pago configurado con webhook."
        if payment_public_key_missing:
            return "Falta configurar clave publica Stripe para activar checkout real."
        if settings.payment_provider_missing:
            return STRIPE_WEBHOOK_MISSING_MESSAGE if payment_webhook_missing else PAYMENT_PROVIDER_MISSING_MESSAGE
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

        provider = settings.payment_provider.strip().lower()
        if provider not in {"stripe", "mercadopago"}:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "payment_provider_missing",
                    "payment_provider_missing": True,
                    "message": self._provider_status_message(provider, False, False),
                },
            )
        if settings.payment_provider_missing:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "payment_provider_missing",
                    "payment_provider_missing": True,
                    "message": self._provider_status_message(provider, False, settings.payment_webhook_missing),
                },
            )

        price = PLAN_PRICES[normalized_plan][billing_cycle]
        currency = PLAN_PRICES[normalized_plan]["currency"]
        amount_cents = int(price["amount_cents"])
        if provider == "mercadopago":
            return await self._create_mercadopago_checkout_record(user, normalized_plan, billing_cycle, amount_cents, currency)
        if provider == "stripe":
            session = self._create_stripe_checkout(user, normalized_plan, billing_cycle, amount_cents, currency)
            record = await repositories.create_checkout_session_record(
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                plan=normalized_plan,
                billing_cycle=billing_cycle,
                provider=provider,
                provider_session_id=session.get("id"),
                checkout_url=session.get("url"),
                amount_cents=amount_cents,
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

    async def _create_mercadopago_checkout_record(
        self,
        user: CurrentUser,
        plan: str,
        billing_cycle: str,
        amount_cents: int,
        currency: str,
    ) -> dict:
        record = await repositories.create_checkout_session_record(
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            plan=plan,
            billing_cycle=billing_cycle,
            provider="mercadopago",
            provider_session_id=None,
            checkout_url=None,
            amount_cents=amount_cents,
            currency=currency,
            status="creating",
            metadata={"provider_status": "creating", "checkout_mode": "preapproval"},
        )
        checkout = self._create_mercadopago_checkout(user, plan, billing_cycle, amount_cents, currency, record["id"])
        updated = await repositories.update_checkout_session_provider(
            record["id"],
            provider_session_id=checkout.get("id"),
            checkout_url=checkout.get("init_point") or checkout.get("sandbox_init_point"),
            status="pending",
            metadata={
                "provider_status": "created",
                "checkout_mode": "preapproval",
                "mercadopago_preapproval_id": checkout.get("id"),
            },
        )
        if updated is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": "checkout_record_not_found"})
        return {
            **updated,
            "payment_provider_missing": False,
            "message": "Checkout Mercado Pago creado. El plan no se activa hasta confirmacion valida de pago.",
        }

    async def handle_stripe_webhook(self, raw_body: bytes, signature_header: str | None) -> dict:
        if not settings.payment_webhook_secret.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "payment_webhook_missing", "payment_webhook_missing": True, "message": STRIPE_WEBHOOK_MISSING_MESSAGE},
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

        activation = await self._activate_stripe_checkout_session(event_id, event, session_object)
        if not activation.get("activated"):
            reason = str(activation.get("reason") or "checkout_activation_failed")
            await repositories.mark_stripe_webhook_event(event_id, "error", checkout_session_id=activation.get("checkout_session_id"), error=reason)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": reason, "activation": activation})

        await repositories.mark_stripe_webhook_event(event_id, "processed", checkout_session_id=activation.get("checkout_session_id"))
        return {"received": True, "status": "processed", "event_id": event_id, "event_type": event_type, "activation": activation}

    async def handle_mercadopago_webhook(
        self,
        raw_body: bytes,
        signature_header: str | None,
        request_id: str | None,
        query_data_id: str | None,
        query_topic: str | None,
    ) -> dict:
        if not settings.mercadopago_webhook_secret.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "payment_webhook_missing", "payment_webhook_missing": True, "message": MERCADOPAGO_WEBHOOK_MISSING_MESSAGE},
            )
        try:
            event = json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invalid_webhook_payload"}) from exc

        data_id = self._mercadopago_data_id(event, query_data_id)
        event_type = str(query_topic or event.get("type") or event.get("topic") or "")
        action = str(event.get("action") or event_type or "event")
        if not data_id or not event_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invalid_mercadopago_webhook_event"})

        self._verify_mercadopago_signature(signature_header, request_id, query_data_id, event)
        event_id = f"{event_type}:{data_id}:{action}:{event.get('id') or data_id}"
        event_record = await repositories.record_payment_webhook_event("mercadopago", event_id, event_type, event)
        if event_record["already_processed"]:
            return {"received": True, "status": "duplicate", "event_id": event_id, "event_type": event_type}

        if event_type == "subscription_authorized_payment":
            provider_payload = self._fetch_mercadopago_authorized_payment(data_id)
            activation = await self._activate_mercadopago_authorized_payment(event_id, provider_payload)
        elif event_type == "payment":
            provider_payload = self._fetch_mercadopago_payment(data_id)
            activation = await self._activate_mercadopago_payment(event_id, provider_payload)
        else:
            await repositories.mark_payment_webhook_event("mercadopago", event_id, "ignored")
            return {"received": True, "status": "ignored", "event_id": event_id, "event_type": event_type, "reason": "unsupported_event_type"}

        if activation.get("ignored"):
            await repositories.mark_payment_webhook_event("mercadopago", event_id, "ignored", error=activation.get("reason"))
            return {"received": True, "status": "ignored", "event_id": event_id, "event_type": event_type, "activation": activation}
        if not activation.get("activated"):
            reason = str(activation.get("reason") or "checkout_activation_failed")
            await repositories.mark_payment_webhook_event(
                "mercadopago",
                event_id,
                "error",
                checkout_session_id=activation.get("checkout_session_id"),
                error=reason,
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": reason, "activation": activation})

        await repositories.mark_payment_webhook_event(
            "mercadopago",
            event_id,
            "processed",
            checkout_session_id=activation.get("checkout_session_id"),
        )
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

    def _verify_mercadopago_signature(
        self,
        signature_header: str | None,
        request_id: str | None,
        query_data_id: str | None,
        event: dict,
    ) -> None:
        if not signature_header:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "mercadopago_signature_missing"})
        timestamp = None
        signatures: list[str] = []
        for part in signature_header.split(","):
            key, _, value = part.partition("=")
            key = key.strip().lower()
            value = value.strip()
            if key == "ts":
                timestamp = value
            elif key == "v1":
                signatures.append(value)
        if not timestamp or not signatures:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "mercadopago_signature_invalid"})
        try:
            timestamp_number = int(timestamp)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "mercadopago_signature_invalid"}) from exc
        timestamp_seconds = timestamp_number / 1000 if timestamp_number > 10_000_000_000 else timestamp_number
        if abs(time.time() - timestamp_seconds) > MERCADOPAGO_SIGNATURE_TOLERANCE_SECONDS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "mercadopago_signature_expired"})

        data_id = query_data_id or ""
        manifest_parts = []
        if data_id:
            manifest_parts.append(f"id:{data_id};")
        if request_id:
            manifest_parts.append(f"request-id:{request_id};")
        manifest_parts.append(f"ts:{timestamp};")
        manifest = "".join(manifest_parts)
        expected = hmac.new(settings.mercadopago_webhook_secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).hexdigest()
        if not any(hmac.compare_digest(expected, signature) for signature in signatures):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "mercadopago_signature_invalid"})

    async def _activate_stripe_checkout_session(self, event_id: str, event: dict, session_object: dict) -> dict:
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
            provider="stripe",
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

    async def _activate_mercadopago_authorized_payment(self, event_id: str, payload: dict) -> dict:
        payment = payload.get("payment") if isinstance(payload.get("payment"), dict) else {}
        if str(payment.get("status") or "").lower() != "approved":
            return {"activated": False, "ignored": True, "reason": "mercadopago_payment_not_approved"}
        preapproval_id = self._string_or_none(payload.get("preapproval_id"))
        checkout_session_id = self._checkout_id_from_external_reference(payload.get("external_reference"))
        paid_at = self._parse_provider_datetime(payload.get("debit_date")) or self._parse_provider_datetime(payload.get("date_created")) or datetime.now(timezone.utc)
        from app.services.subscription_service import subscription_service

        checkout = await repositories.checkout_session_for_activation(
            provider="mercadopago",
            provider_session_id=preapproval_id,
            checkout_session_id=checkout_session_id,
        )
        plan_hint = str((checkout or {}).get("plan") or "")
        billing_cycle_hint = str((checkout or {}).get("billing_cycle") or "")
        current_period_end = paid_at + (timedelta(days=365) if billing_cycle_hint == "annual" else timedelta(days=30))
        return await repositories.activate_checkout_session_from_webhook(
            provider="mercadopago",
            provider_session_id=preapproval_id,
            checkout_session_id=checkout_session_id,
            event_id=event_id,
            provider_customer_id=self._string_or_none(payload.get("payer_id")),
            provider_subscription_id=preapproval_id,
            amount_cents=self._amount_to_cents(payload.get("transaction_amount")),
            currency=self._string_or_none(payload.get("currency_id")),
            paid_at=paid_at,
            current_period_start=paid_at,
            current_period_end=current_period_end,
            limits=subscription_service.limits_for(plan_hint) if plan_hint else {},
            metadata={"billing_cycle": billing_cycle_hint} if billing_cycle_hint else {},
        )

    async def _activate_mercadopago_payment(self, event_id: str, payload: dict) -> dict:
        if str(payload.get("status") or "").lower() != "approved":
            return {"activated": False, "ignored": True, "reason": "mercadopago_payment_not_approved"}
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        provider_session_id = self._string_or_none(payload.get("preapproval_id")) or self._string_or_none(metadata.get("preapproval_id"))
        checkout_session_id = self._checkout_id_from_external_reference(payload.get("external_reference"))
        transaction_details = payload.get("transaction_details") if isinstance(payload.get("transaction_details"), dict) else {}
        amount_cents = self._amount_to_cents(payload.get("transaction_amount") or transaction_details.get("total_paid_amount"))
        paid_at = self._parse_provider_datetime(payload.get("date_approved")) or self._parse_provider_datetime(payload.get("date_created")) or datetime.now(timezone.utc)
        payer = payload.get("payer") if isinstance(payload.get("payer"), dict) else {}
        from app.services.subscription_service import subscription_service

        checkout = await repositories.checkout_session_for_activation(
            provider="mercadopago",
            provider_session_id=provider_session_id,
            checkout_session_id=checkout_session_id,
        )
        plan_hint = str(metadata.get("plan") or (checkout or {}).get("plan") or "")
        billing_cycle_hint = str(metadata.get("billing_cycle") or (checkout or {}).get("billing_cycle") or "")
        current_period_end = paid_at + (timedelta(days=365) if billing_cycle_hint == "annual" else timedelta(days=30))
        return await repositories.activate_checkout_session_from_webhook(
            provider="mercadopago",
            provider_session_id=provider_session_id,
            checkout_session_id=checkout_session_id,
            event_id=event_id,
            provider_customer_id=self._string_or_none(payer.get("id")),
            provider_subscription_id=provider_session_id,
            amount_cents=amount_cents,
            currency=self._string_or_none(payload.get("currency_id")),
            paid_at=paid_at,
            current_period_start=paid_at,
            current_period_end=current_period_end,
            limits=subscription_service.limits_for(plan_hint) if plan_hint else {},
            metadata=metadata,
        )

    def _timestamp_to_datetime(self, value: object) -> datetime | None:
        if value is None:
            return None
        try:
            return datetime.fromtimestamp(int(value), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            return None

    def _parse_provider_datetime(self, value: object) -> datetime | None:
        if value is None:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

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

    def _checkout_id_from_external_reference(self, value: object) -> str | None:
        text = self._string_or_none(value)
        return text if text and text.startswith("checkout-") else None

    def _amount_to_cents(self, value: object) -> int | None:
        if value is None:
            return None
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
        return int((amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def _amount_from_cents(self, amount_cents: int) -> float:
        amount = (Decimal(amount_cents) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return float(amount)

    def _mercadopago_data_id(self, event: dict, query_data_id: str | None) -> str:
        if query_data_id:
            return str(query_data_id)
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        return str(data.get("id") or "")

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

    def _create_mercadopago_checkout(
        self,
        user: CurrentUser,
        plan: str,
        billing_cycle: str,
        amount_cents: int,
        currency: str,
        checkout_session_id: str,
    ) -> dict:
        public_url = settings.app_public_url.rstrip("/")
        frequency = 12 if billing_cycle == "annual" else 1
        payload = {
            "reason": f"DCFT {plan.upper()} {'anual' if billing_cycle == 'annual' else 'mensual'}",
            "external_reference": checkout_session_id,
            "payer_email": user.username,
            "auto_recurring": {
                "frequency": frequency,
                "frequency_type": "months",
                "transaction_amount": self._amount_from_cents(amount_cents),
                "currency_id": currency,
            },
            "back_url": f"{public_url}/?checkout=mercadopago",
        }
        data = self._mercadopago_request("POST", "/preapproval", payload)
        if not data.get("id") or not (data.get("init_point") or data.get("sandbox_init_point")):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": "payment_provider_error", "message": "Mercado Pago no devolvio identificador y URL de checkout."},
            )
        return data

    def _fetch_mercadopago_authorized_payment(self, authorized_payment_id: str) -> dict:
        return self._mercadopago_request("GET", f"/authorized_payments/{urllib.parse.quote(authorized_payment_id)}")

    def _fetch_mercadopago_payment(self, payment_id: str) -> dict:
        return self._mercadopago_request("GET", f"/v1/payments/{urllib.parse.quote(payment_id)}")

    def _mercadopago_request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urlrequest.Request(
            f"https://api.mercadopago.com{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {settings.mercadopago_access_token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlrequest.urlopen(request, timeout=15) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": "payment_provider_error", "message": MERCADOPAGO_PROVIDER_ERROR_MESSAGE, "provider_status": exc.code},
            ) from exc
        except urllib.error.URLError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": "payment_provider_unreachable", "message": "Mercado Pago no respondio a tiempo."},
            ) from exc
        try:
            return json.loads(body or "{}")
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": "payment_provider_error", "message": "Mercado Pago devolvio una respuesta invalida."},
            ) from exc


payment_service = PaymentService()
