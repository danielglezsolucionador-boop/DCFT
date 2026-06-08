from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import CurrentUser, StudentDoctorAnswerOut, StudentDoctorAskIn, StudentDoctorStatusOut
from app.services.student_doctor_service import student_doctor_service


router = APIRouter(prefix="/student", tags=["student"])


@router.get("/doctor/status", response_model=StudentDoctorStatusOut)
async def student_doctor_status(user: CurrentUser = Depends(get_current_user)) -> dict:
    return await student_doctor_service.status(user)


@router.post("/doctor/ask", response_model=StudentDoctorAnswerOut)
async def student_doctor_ask(payload: StudentDoctorAskIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    return await student_doctor_service.ask(user, payload.question)
