from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import AdminPlanUpdateIn, AdminTrialUpdateIn, CurrentUser
from app.services.admin_service import admin_service


router = APIRouter(prefix="/admin/ceo", tags=["admin-ceo"])


@router.get("/users")
async def list_users(user: CurrentUser = Depends(get_current_user)) -> dict:
    return await admin_service.list_users(user)


@router.post("/users/{user_id}/trial")
async def set_trial(user_id: str, payload: AdminTrialUpdateIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await admin_service.set_trial(user, user_id, payload.active, payload.days)


@router.patch("/users/{user_id}/plan")
async def change_plan(user_id: str, payload: AdminPlanUpdateIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await admin_service.change_plan(user, user_id, payload.plan)
