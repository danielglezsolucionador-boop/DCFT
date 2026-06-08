# DCFT Student Section Implementation Plan

Fecha local: 2026-06-07

## Estado

Listo para revision CEO.

## Regla CEO obligatoria

- Estado maximo permitido: `Listo para revision CEO.`
- La decision final solo puede ser explicita del CEO.
- Ningun reporte tecnico debe elevar el estado por cuenta propia.

## Alcance ejecutado

1. Backup previo en `D:\ECOSYSTEM\BACKUPS`.
2. Lectura de documentos base DCFT/AUDITORIA/cabinas.
3. Descubrimiento de cabina corazon y cabinas humanas/tecnicas disponibles.
4. Auditoria de proveedor IA en DCFT, FORJA y CEREBRO.
5. Propuesta maestra actualizada.
6. Plan de implementacion actualizado.
7. Email verification real preservado.
8. Checkout real preparado preservado.
9. Doctor estudiante real implementado con cuota mensual.
10. Plan Contable base activado en estudiante.
11. Ajustes frontend estudiante quirurgicos.
12. Tests/build locales ejecutados.

## Cambios backend preservados

- `User.email_verified` y `User.email_verified_at`.
- Tabla `email_verification_tokens`.
- Tabla `checkout_sessions`.
- Migracion `0009_email_verification_checkout`.
- Servicio `email_service.py`.
- Servicio `payment_service.py`.
- `/auth/resend-verification`.
- `/auth/verify-email`.
- Login bloquea usuarios no verificados.
- `/subscriptions/checkout/status`.
- `/subscriptions/checkout`.
- Env examples con variables email/payment.

## Cambios backend nuevos

- Configuracion IA en `apps/backend/app/core/config.py`.
- Migracion `0010_student_doctor_usage`.
- Tabla `student_doctor_usage`.
- Repositorios de cuota mensual del Doctor.
- Schemas `StudentDoctorAskIn`, `StudentDoctorQuotaOut`, `StudentDoctorStatusOut`, `StudentDoctorAnswerOut`.
- Servicio `apps/backend/app/services/student_doctor_service.py`.
- Router `apps/backend/app/api/student.py`.
- Inclusiones en `apps/backend/app/main.py`.

## Endpoints estudiante

- `GET /student/doctor/status`
- `POST /student/doctor/ask`

Ambos requieren usuario autenticado. El servicio limita el uso a planes estudiante.

## Cuota Doctor

- Limite: 5 preguntas por mes.
- Alcance de contador: usuario + tenant + anio + mes.
- Se incrementa solo despues de respuesta IA exitosa.
- No se incrementa cuando falta proveedor.
- No se incrementa cuando el proveedor falla.
- No se incrementa cuando la respuesta esta vacia.

Mensaje de limite:

`Has usado tus 5 preguntas del mes. Podras volver a preguntar el proximo mes o pasar a un plan empresa cuando este disponible.`

## Variables IA

- `DCFT_AI_PROVIDER_ENABLED`
- `DCFT_AI_PROVIDER`
- `DCFT_AI_MODEL`
- `DCFT_AI_REQUEST_TIMEOUT_SECONDS`
- `DCFT_OPENROUTER_API_KEY`
- `DCFT_OPENROUTER_MODEL`
- `DCFT_OPENROUTER_BASE_URL`
- `DCFT_OPENROUTER_REFERER`
- `DCFT_OPENROUTER_TITLE`
- `DCFT_OPENAI_API_KEY`
- `DCFT_OPENAI_MODEL`
- `DCFT_ANTHROPIC_API_KEY`
- `DCFT_ANTHROPIC_MODEL`
- `DCFT_GEMINI_API_KEY`
- `DCFT_GEMINI_MODEL`

Los archivos `.env*.example` contienen placeholders, no secretos reales.

## Cambios frontend

- Onboarding ya no guarda token si la cuenta requiere verificacion.
- Mensaje visible para correo pendiente.
- Boton de reenvio.
- Parser de errores JSON estructurados.
- Planes mensual/anual visibles.
- Checkout muestra bloqueo real si falta proveedor.
- Beneficios activos separados de proximamente.
- Doctor estudiante movido a activo con formulario real.
- Contador visible de preguntas restantes.
- Sugerencias educativas visibles.
- Error de proveedor IA visible sin consumir cuota.
- Plan Contable base con busqueda local.
- PDF propio se mantiene como proximamente.
- Modulos empresariales mas tenues en estudiante.
- Selector Estudiante / Empresa intacto.

## Validacion local requerida

- `python -m compileall apps\backend api -q`
- `python -m pytest apps\backend\tests\test_operational_backend.py -q`
- `npm run build` en `apps/frontend`
- Secret scan.
- Mobile local sin overflow.
- Empresa local sin ruptura.
- Console errors 0.

## Validacion produccion requerida

- `https://dcft-frontend.vercel.app`
- `https://dcft-frontend.vercel.app/?access=business`
- `https://dcft.vercel.app/runtime/status`
- `https://dcft.vercel.app/health`

Sin deploy desde esta ejecucion; la validacion produccion verifica el estado publicado actual.

## Riesgos pendientes

- Falta configurar proveedor real de correo en entornos productivos.
- Falta configurar proveedor real de pago en entornos productivos.
- Falta configurar proveedor IA para activar respuestas reales del Doctor en produccion/staging.
- Falta webhook de pago para activar plan despues de pago confirmado.
- PDF propio requiere carga, almacenamiento seguro, analisis controlado y generacion de respuesta.
- No se encontro archivo exacto de cabina corazon DCFT; se usaron cabinas AUDITORIA como referencia disponible.

## Actualizacion Paquete 1 - 2026-06-08

### Fuente maestra

- Usar `C:\Users\admin\Desktop\entregar a codex la app doctor cft\DCFT.docx` como fuente primaria.
- Usar `C:\Users\admin\Desktop\dcft.txt` como espejo de lectura.
- Usar `1.1_DCFT_CORE_IDENTITY.md` como soporte conceptual.
- Usar fases `1.2`, `1.7`, `10.2`, `10.3` de `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613` para estudiante/planes.
- Nota correctiva: desde este paquete no se considera ausente la fuente maestra de DCFT; `DCFT.docx` reemplaza esa funcion.

### Cambios quirurgicos aplicados

- CTA estudiante ajustada a `Crear cuenta estudiante`.
- Selector empresa conserva ruta empresa sin exponer RUC/SUNAT en primera pantalla estudiante.
- Beneficios activos/proximamente quedan separados.
- Doctor de estudio queda en activo condicionado a OpenRouter real.
- PDF propio queda proximamente.
- Plan Contable queda base inicial/en ampliacion.
- Sidebar desktop evita truncado del nombre largo.

### Validacion ejecutada

- `npm run build`: PASS.
- `python -m compileall apps\backend api -q`: PASS.
- `$env:PYTHONPATH='apps/backend'; python -m pytest -q`: PASS, 43 tests.
- `git diff --check`: PASS, con warnings CRLF solamente.
- Secret scan: REVIEW_FILES_ONLY por placeholders de test, sin valores impresos.
- Mobile 390x844: sin overflow horizontal, sin loading persistente, sin textos cortados detectados.
- Desktop 1280x720 empresa: sin overflow horizontal, sin loading persistente, sin textos cortados detectados.

### Estado

- Estado maximo permitido: `Listo para revision CEO.`
- No se declara estudiante aprobado.
- No push.
- No deploy.
