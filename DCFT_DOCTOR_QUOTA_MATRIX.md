# DCFT Doctor Quota Matrix

Fecha local: 2026-06-07

## Estado

Listo para revision CEO.

## Regla CEO

- Estado maximo permitido: `Listo para revision CEO.`
- La decision final solo puede venir del CEO de forma explicita.

## Matriz

| Caso | Resultado API | Descuenta cuota | Mensaje esperado |
| --- | --- | --- | --- |
| `GET /student/doctor/status` con estudiante | 200 | No | Estado, cuota y mensaje educativo |
| `POST /student/doctor/ask` sin login | 401 | No | Token requerido |
| `POST /student/doctor/ask` con plan no estudiante | 403 | No | Disponible solo para cuenta estudiante |
| Pregunta vacia o muy corta | 422 | No | Validacion de payload |
| `DCFT_AI_PROVIDER_ENABLED=false` | 503 | No | `Falta configurar proveedor IA para activar el Doctor de estudio.` |
| Falta key del proveedor | 503 | No | `Falta configurar proveedor IA para activar el Doctor de estudio.` |
| Timeout/error proveedor | 503 | No | `El proveedor IA no respondio correctamente. No se desconto ninguna pregunta.` |
| Respuesta IA vacia | 502 | No | `El proveedor IA no devolvio una respuesta util. No se desconto ninguna pregunta.` |
| Respuesta IA exitosa | 200 | Si | Respuesta educativa + cuota actualizada |
| 5 preguntas usadas en el mes | 429 | No | `Has usado tus 5 preguntas del mes. Podras volver a preguntar el proximo mes o pasar a un plan empresa cuando este disponible.` |
| Nuevo mes calendario UTC | 200 si proveedor ok | Si, en nuevo bucket | Contador mensual reiniciado por `month_key` |

## Persistencia

- Tabla: `student_doctor_usage`.
- Clave logica: usuario + tenant + `month_key`.
- Campos clave: `questions_used`, `questions_limit`, `year`, `month`, `month_key`, `last_question`, `last_answered_at`.

## Invariantes

- La cuota nunca baja.
- La cuota no aumenta en errores.
- El limite por defecto es 5.
- El frontend no calcula autoridad de cuota; solo muestra lo que devuelve backend.
- El backend es la fuente de verdad.
