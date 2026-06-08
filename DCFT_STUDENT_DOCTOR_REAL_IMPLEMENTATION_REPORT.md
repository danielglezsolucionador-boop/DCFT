# DCFT Student Doctor Real Implementation Report

Fecha local: 2026-06-07

## Estado

Listo para revision CEO.

## Consolidacion predeploy 2026-06-07

- Doctor estudiante se mantiene implementado localmente.
- Endpoints activos: `GET /student/doctor/status` y `POST /student/doctor/ask`.
- Cuota mensual: 5 preguntas por usuario/tenant/mes.
- Proveedores IA soportados: OpenRouter, OpenAI, Anthropic y Gemini.
- OpenRouter queda como proveedor recomendado por patron FORJA/CEREBRO.
- Si falta proveedor IA, devuelve `ai_provider_missing=true`.
- Si falta proveedor IA o el proveedor falla, no descuenta cuota.
- Mensaje operativo permitido: `Disponible cuando se configure proveedor IA.`
- No se revierte a `proximamente`.
- No toca SUNAT real.
- No toca produccion.

## Regla CEO

- Estado maximo permitido: `Listo para revision CEO.`
- La decision final solo puede venir del CEO de forma explicita.

## Backup

- `D:\ECOSYSTEM\BACKUPS\dcft-student-doctor-real-prechange-20260607-222156.zip`

## Backend

- `apps/backend/app/core/config.py`: variables IA por proveedor.
- `apps/backend/app/db/models.py`: modelo `StudentDoctorUsage`.
- `apps/backend/alembic/versions/0010_student_doctor_usage.py`: migracion de cuota.
- `apps/backend/app/db/repositories.py`: helpers de storage, status y consumo.
- `apps/backend/app/schemas/common.py`: schemas de ask/status/answer/quota.
- `apps/backend/app/services/student_doctor_service.py`: orquestacion IA, cuota y limites.
- `apps/backend/app/api/student.py`: router estudiante.
- `apps/backend/app/main.py`: inclusion del router.

## Endpoints

- `GET /student/doctor/status`
- `POST /student/doctor/ask`

## Comportamiento

- Nombre visible: `Doctor de estudio contable, financiero y tributario`.
- Limite: 5 preguntas mensuales.
- Alcance de cuota: usuario + tenant + anio + mes.
- Incrementa cuota solo despues de respuesta IA exitosa.
- Si falta proveedor IA, devuelve 503 con `ai_provider_missing=true`.
- Si el proveedor falla, conserva cuota.
- Si el proveedor devuelve respuesta vacia, conserva cuota.
- Si la cuota se agota, devuelve el mensaje de limite mensual.
- Se registran eventos runtime/audit despues de respuesta exitosa.

## Frontera estudiante

- Solo cuenta estudiante.
- Sin RUC.
- Sin SUNAT real.
- Sin diagnostico empresarial.
- Sin acceso a workspace empresarial.
- Sin pasar a empresa automaticamente.

## Frontend

- Doctor deja de aparecer como proximamente.
- UI muestra contador `Te quedan X de 5 preguntas este mes.`
- UI muestra campo de pregunta, sugerencias, boton `Preguntar al Doctor`, respuesta y errores.
- Si falta proveedor IA, la UI informa el bloqueo honesto.
- Beneficios activos y proximamente quedan separados.
- PDF propio queda como proximamente.
- Plan Contable base queda visible en Ejercicios.
- MYPE/Premium quedan como camino comercial.
- Selector Estudiante / Empresa permanece intacto.

## Validacion local

- `python -m compileall apps\backend api -q`: PASS.
- `python -m pytest apps\backend\tests\test_operational_backend.py -q`: PASS, 38 tests.
- `npm run build` en `apps/frontend`: PASS.
- Endpoint local sin proveedor: 503 honesto y cuota intacta.
- Navegador local mobile/desktop: Doctor visible, sin overflow horizontal y console errors 0.
- Empresa local: sin ruptura observada en validacion smoke.

## Produccion

- Frontend publico responde 200.
- Backend `/health` responde ok.
- Backend `/runtime/status` reporta Postgres persistente y `ai_pipeline=blocked_provider_disabled`.
- No se hizo push/deploy desde esta ejecucion; produccion no contiene aun estos cambios locales.

## Riesgos

- Falta configurar proveedor IA real para respuestas en staging/produccion.
- Falta deploy controlado.
- Falta validar costo/latencia/modelo antes de exposicion amplia.
