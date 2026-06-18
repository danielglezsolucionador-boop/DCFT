from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import require_permission
from app.schemas.common import CheckoutRequestIn, CurrentUser, SubscriptionUpdateIn
from app.services.payment_service import payment_service
from app.services.subscription_service import subscription_service


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def _payment_status(subscription: dict, checkout: dict | None) -> str:
    checkout_status = str((checkout or {}).get("status") or "").lower()
    if checkout_status in {"paid", "completed"}:
        return "paid"
    if checkout_status in {"rejected", "cancelled", "canceled"}:
        return "rejected"
    if subscription.get("provider") in {"stripe", "mercadopago"} and subscription.get("status") == "active":
        return "paid"
    return "pending"


@router.get("/plans")
def plans() -> list[dict]:
    return subscription_service.plans()


@router.get("/current")
async def current(user: CurrentUser = Depends(require_permission("subscriptions:read"))) -> dict:
    return await subscription_service.current_for_tenant(user.tenant_id, user.plan)


@router.get("/checkout/status")
async def checkout_status(user: CurrentUser = Depends(require_permission("subscriptions:read"))) -> dict:
    subscription = await subscription_service.current_for_tenant(user.tenant_id, user.plan)
    checkout = await subscription_service.latest_checkout_for_tenant(user.tenant_id)
    return {
        **payment_service.provider_status(),
        "current_plan": user.plan,
        "tenant_id": user.tenant_id,
        "payment_status": _payment_status(subscription, checkout),
        "checkout": checkout,
        "subscription": subscription,
    }


@router.get("/status")
async def subscription_status(user: CurrentUser = Depends(require_permission("subscriptions:read"))) -> dict:
    subscription = await subscription_service.current_for_tenant(user.tenant_id, user.plan)
    checkout = await subscription_service.latest_checkout_for_tenant(user.tenant_id)
    return {
        "tenant_id": user.tenant_id,
        "user_id": user.user_id,
        "plan": subscription.get("plan") or user.plan,
        "plan_effective": subscription.get("plan_effective") or subscription.get("plan") or user.plan,
        "status": subscription.get("status") or "pending",
        "trial": subscription.get("trial"),
        "started_at": subscription.get("started_at"),
        "ends_at": subscription.get("ends_at"),
        "billing_cycle": subscription.get("billing_cycle"),
        "interval": subscription.get("interval"),
        "provider": subscription.get("provider"),
        "payment_status": _payment_status(subscription, checkout),
        "checkout": checkout,
        "subscription": subscription.get("subscription"),
    }


@router.post("/checkout")
async def create_checkout(payload: CheckoutRequestIn, user: CurrentUser = Depends(require_permission("subscriptions:manage"))) -> dict:
    return await payment_service.create_checkout(user, payload.plan, payload.billing_cycle)


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request) -> dict:
    return await payment_service.handle_stripe_webhook(await request.body(), request.headers.get("stripe-signature"))


@router.post("/mercadopago/webhook")
async def mercadopago_webhook(request: Request) -> dict:
    return await payment_service.handle_mercadopago_webhook(
        await request.body(),
        request.headers.get("x-signature"),
        request.headers.get("x-request-id"),
        request.query_params.get("data.id"),
        request.query_params.get("type") or request.query_params.get("topic"),
    )


@router.patch("/current")
async def change_current(payload: SubscriptionUpdateIn, user: CurrentUser = Depends(require_permission("subscriptions:manage"))) -> dict:
    return await subscription_service.change_plan(user.tenant_id, user.username, payload.plan)
