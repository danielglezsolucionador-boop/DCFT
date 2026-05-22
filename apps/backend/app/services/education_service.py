from __future__ import annotations


EXERCISES = [
    {
        "id": "acc-basic-001",
        "topic": "accounting",
        "level": "student",
        "prompt": "Clasifica una compra de mercaderia pagada al contado.",
        "expected_answer": "activo/inventario y salida de caja",
        "explanation": "Aumenta inventario y disminuye caja. La clasificacion final depende del plan contable aplicable.",
    },
    {
        "id": "fin-basic-001",
        "topic": "finance",
        "level": "student",
        "prompt": "Que indica una liquidez corriente menor a 1?",
        "expected_answer": "riesgo de liquidez",
        "explanation": "Puede indicar dificultad para cubrir obligaciones de corto plazo con activos corrientes.",
    },
    {
        "id": "tax-basic-001",
        "topic": "tax",
        "level": "student",
        "prompt": "Debe DCFT presentar una declaracion SUNAT automaticamente?",
        "expected_answer": "no",
        "explanation": "DCFT no declara impuestos ni ejecuta acciones oficiales. Solo prepara analisis revisable.",
    },
]


class EducationService:
    def list_exercises(self, topic: str | None = None) -> list[dict]:
        if topic:
            return [item for item in EXERCISES if item["topic"] == topic]
        return EXERCISES

    def attempt(self, exercise_id: str, answer: str) -> dict | None:
        exercise = next((item for item in EXERCISES if item["id"] == exercise_id), None)
        if exercise is None:
            return None
        normalized = answer.strip().lower()
        expected = exercise["expected_answer"].lower()
        return {
            "exercise_id": exercise_id,
            "correct": expected in normalized or normalized in expected,
            "expected_answer": exercise["expected_answer"],
            "explanation": exercise["explanation"],
        }


education_service = EducationService()