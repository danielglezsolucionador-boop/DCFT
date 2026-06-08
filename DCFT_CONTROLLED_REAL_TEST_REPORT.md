# DCFT Controlled Real Test Report

Fecha: 2026-06-05 23:25 -05

## 1. Backup creado

- Backup pre-cambio: `D:\ECOSYSTEM\BACKUPS\dcft-controlled-real-test-prechange-20260605-231714.zip`
- Tipo: `git archive` de `HEAD` para respaldar codigo versionado sin empaquetar `.env` ni secretos locales.

## 2. Estado antes de tocar

- Repo: `C:\Users\admin\dcft-knowledge-core`
- Rama: `main`
- Ultimo commit: `3f89bd2 docs: record dcft compact mobile production validation`
- Git status inicial: limpio, `main...origin/main`
- Frontend produccion: `https://dcft-frontend.vercel.app`
- Backend produccion: `https://dcft.vercel.app`
- API embebida en bundle publico: `https://dcft.vercel.app`
- Bundle publico sin `localhost` ni `127.0.0.1`.

## 3. Que archivos se tocaron

- `DCFT_CONTROLLED_REAL_TEST_REPORT.md`
- `DCFT_OPERATIONAL_V1_CEO_REPORT.md`

## 4. Que NO se toco

- No se redisenio la cabina visual.
- No se toco backend.
- No se toco Postgres.
- No se tocaron migraciones.
- No se toco auth.
- No se implemento SUNAT real.
- No se usaron credenciales reales SUNAT.
- No se hizo push.
- No se hizo deploy.
- No se tocaron FORJA, CEREBRO, SENTINELA ni otras apps.

## 5. Auditoria auth/API actual

| Punto | Resultado |
| --- | --- |
| API frontend produccion | `https://dcft.vercel.app` |
| Auth | JWT Bearer token |
| Frontend session | `localStorage` key `dcft_token` |
| `/health` | PASS, HTTP 200 |
| `/runtime/status` | PASS, HTTP 200 |
| `/auth/login` | Existe, POST; dummy invalido devuelve HTTP 401 `invalid_credentials` |
| `/auth/register` | No existe, HTTP 404; el registro real usa `/onboarding/tenants` |
| `/auth/me` | Protegido; sin token HTTP 401, con token HTTP 200 |
| Empresa/workspace | `/identity/companies`, `/identity/workspaces`, `/identity/context` |
| Trial | `/onboarding/tenants`, `/onboarding/progress`, `/admin/ceo/users/{user_id}/trial` |
| Admin CEO | `/admin/ceo/users`, `/admin/ceo/users/{user_id}/trial`, `/admin/ceo/users/{user_id}/plan` |

## 6. Prueba estudiante

Datos dummy:

- Usuario: `estudiante.test.dcft.20260605231858@example.com`
- Password dummy: no impreso en logs del reporte.
- Tenant: `estudiante-dcft-0605231858`

Resultados:

- Registro estudiante por `/onboarding/tenants`: PASS, HTTP 200.
- Login estudiante por `/auth/login`: PASS, HTTP 200.
- `/auth/me`: PASS, usuario correcto, plan `student`.
- Logout: PASS, `/auth/logout` HTTP 200.
- Token revocado despues de logout: PASS, `/auth/me` devuelve HTTP 401 `token_revoked`.
- Login nuevamente: PASS, HTTP 200.
- Persistencia despues de logout/login: PASS.
- Estudiante no requiere RUC: PASS, `company=null`, `workspace=null`.
- Ejercicios visibles en UI publica: PASS, 15 ejercicios.
- Ejercicios con solucion/guia en frontend: PASS por UI previa validada.
- Modulos Premium: visibles/controlados por plan efectivo y trial.

Estado estudiante: operativo.

## 7. Prueba empresa

Datos dummy:

- Usuario: `empresa.test.dcft.20260605231858@example.com`
- Tenant: `empresa-dcft-0605231858`
- RUC: `20123456789`
- Razon social: `EMPRESA TEST DCFT SAC`
- Usuario secundario SUNAT: `usuario_auxiliar_test`
- Clave secundaria SUNAT: no enviada al backend en la preparacion segura; no se uso `NO_REAL_TEST_123` en API.
- Plan: `mype`

Resultados:

- Registro empresa por `/onboarding/tenants`: PASS, HTTP 200.
- Login empresa por `/auth/login`: PASS, HTTP 200.
- Empresa creada: PASS, `company-e4225f5a3f524307a68a418079efc478`.
- Workspace creado: PASS, `workspace-ae618e1268da497ab86fd0512b5fe293`.
- Contexto activo empresa/workspace: PASS.
- Plan base: `mype`.
- Plan efectivo durante trial: `premium`.
- Diagnostico inicial: pendiente claro, no parece bug.
- Logout/login y persistencia de empresa/workspace: PASS.

Estado empresa: operativa en modo controlado sin SUNAT real.

## 8. Trial Premium 7 dias

- Trial automatico solicitado en onboarding: PASS.
- Estudiante: trial activo, inicio `2026-06-06T04:19:09Z`, vencimiento `2026-06-13T04:19:09Z`, `days_remaining=7`.
- Empresa: trial activo, inicio `2026-06-06T04:19:17Z`, vencimiento `2026-06-13T04:19:17Z`, `days_remaining=7`.
- Persistencia tras logout/login: PASS.
- Estado guardado en Postgres: PASS por persistencia API.
- Activacion manual por Admin CEO con token admin real: pendiente porque no se proporcionaron credenciales admin CEO productivas.
- Endpoint admin para activar trial existe y esta protegido.

Estado trial: PASS por onboarding; activacion manual CEO pendiente de credencial admin real.

## 9. Admin CEO protegido

- Admin CEO no aparece en entrada publica: PASS.
- `/admin/ceo/users` sin token: PASS, HTTP 401 `missing_bearer_token`.
- `/admin/ceo/users` con usuario regular empresa: PASS, HTTP 403 `admin_ceo_required`.
- `/admin/ceo/users` con estudiante: PASS, HTTP 403 `admin_ceo_required`.
- Token admin CEO real: no disponible para esta prueba.

Estado Admin CEO: protegido. Validacion con admin real pendiente.

## 10. Postgres y persistencia

`GET https://dcft.vercel.app/runtime/status`: PASS.

- `postgres=true`
- `sqlite=false`
- `persistent=true`
- `temporal=false`
- `database.backend=postgresql`
- `database.status=ok`
- `database.reason=connection_ok`

Persistencia:

- Usuario estudiante persiste: PASS.
- Usuario empresa persiste: PASS.
- Empresa/workspace persiste: PASS.
- Trial persiste: PASS.
- Logout/login no borra datos: PASS.

Observacion tecnica:

- Runtime reporto `audit_integrity.tamper_detected=false`.
- Runtime tambien reporto `audit_integrity.chain_forks_detected=true`; no bloqueo esta prueba funcional, pero queda como riesgo de observabilidad/auditoria a revisar antes de auditoria fuerte.

## 11. Seguridad SUNAT auxiliar

API publica:

- `/sunat/auxiliary-access/requirements`: PASS, HTTP 200.
- `/sunat/data-classification`: PASS, HTTP 200.

Flujo empresa:

- `/sunat/status` antes: `NOT_CONNECTED`, `foundation_only=true`, `real_connector_enabled=false`.
- `/sunat/auxiliary-access/prepare`: PASS, HTTP 200.
- Resultado: `PREPARED_PENDING_REAL_CONNECTOR`.
- Conexion real SUNAT: apagada.
- `real_sunat_session=false`.
- `read_only=true`.
- `remote_actions_enabled=false`.
- `password_received=false` en evento de preparacion.
- `/sunat/connections/{id}/sync`: PASS, devuelve `NOT_EXECUTED_FOUNDATION_ONLY`; no ejecuta SUNAT real.

UI empresa:

- Comunica usuario secundario/auxiliar SUNAT.
- Comunica acceso de consulta.
- Comunica que DCFT no declara, no paga, no emite facturas y no modifica informacion.
- No pide Clave SOL principal en la entrada publica.
- No muestra usuario principal.
- No expone la clave dummy en HTML ni logs.

Estado SUNAT auxiliar: preparado de forma segura, sin conector real.

## 12. UI produccion

Frontend:

- `GET https://dcft-frontend.vercel.app`: HTTP 200.
- Mobile 390x844: PASS.
- Desktop 1365x900: PASS.
- Console errors: 0.
- Overflow horizontal: NO.
- Admin CEO publico: ausente.
- `Soy estudiante`: visible.
- `Soy empresa`: visible.
- `Ejercicios`: visible.
- `Diagnostico`: visible.
- `Primeros pasos`: disponible en acciones/drawer.
- Seguridad DCFT empresa: disponible y valida.

Evidencia:

- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-prod-mobile-390x844.png`
- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-prod-desktop-1365x900.png`

## 13. Tests y build

| Comando | Resultado |
| --- | --- |
| `npm run build` en `apps/frontend` | PASS |
| `python -m compileall apps\backend api -q` | PASS |
| `python -m pytest apps\backend\tests\test_operational_backend.py -q` con Python global | FAIL por entorno local: falta `aiosqlite` |
| `.venv\Scripts\python.exe -m compileall apps\backend api -q` | PASS |
| `.venv\Scripts\python.exe -m pytest apps\backend\tests\test_operational_backend.py -q` | PASS, `32 passed` |
| Secret scan redacted sobre archivos versionados | PASS |

## 14. Produccion validada

- Backend `/health`: PASS.
- Backend `/runtime/status`: PASS.
- Frontend HTTP 200: PASS.
- Auth real con usuarios dummy: PASS.
- Registro estudiante: PASS.
- Registro empresa: PASS.
- Workspace: PASS.
- Trial 7 dias por onboarding: PASS.
- Admin CEO protegido: PASS.
- SUNAT real apagado: PASS.

## 15. Bloqueos reales

- `/auth/register` no existe; el endpoint real de registro es `/onboarding/tenants`.
- No se valido activacion manual de trial desde Admin CEO con token admin real porque no hubo credenciales admin CEO productivas para Codex.
- Python global no tiene `aiosqlite`; los tests pasan con `.venv`.
- `audit_integrity.chain_forks_detected=true` en runtime queda como riesgo de observabilidad/auditoria para revisar.

## 16. Recomendacion

DCFT esta listo para testers controlados como producto operativo V1, con estas condiciones:

- Usar solo datos dummy/controlados en pilotos.
- Mantener SUNAT real apagado.
- No pedir ni guardar Clave SOL principal.
- Revisar el riesgo de `chain_forks_detected=true` antes de una auditoria externa fuerte.
- Validar Admin CEO con credenciales reales en un bloque separado.
