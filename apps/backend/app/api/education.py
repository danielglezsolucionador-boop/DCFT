from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.services.education_service import education_service


router = APIRouter(prefix="/education", tags=["education"])


class ExerciseAttempt(BaseModel):
    answer: str


@router.get("/exercises")
def exercises(topic: str | None = None) -> list[dict]:
    return education_service.list_exercises(topic)


@router.post("/exercises/{exercise_id}/attempt")
def attempt(exercise_id: str, payload: ExerciseAttempt) -> dict:
    result = education_service.attempt(exercise_id, payload.answer)
    if result is None:
        raise HTTPException(status_code=404, detail="exercise_not_found")
    return result