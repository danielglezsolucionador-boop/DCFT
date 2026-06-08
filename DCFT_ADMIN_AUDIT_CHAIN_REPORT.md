# DCFT Admin CEO Real + Audit Chain Integrity

Fecha de validacion: 2026-06-05
Repositorio: `C:\Users\admin\dcft-knowledge-core`
Branch: `main`
Commit local: `3f89bd2602016c3f4eb165bb568528324e0d25c1`

## 1. Backup

Backup creado antes de documentar hallazgos:

`D:\ECOSYSTEM\BACKUPS\dcft-admin-audit-chain-prechange-20260605-234856.zip`

El backup incluye el estado de `HEAD` y los reportes locales no commiteados existentes al inicio de esta validacion.

## 2. Estado inicial

- `git status`: habia cambios locales previos en `DCFT_OPERATIONAL_V1_CEO_REPORT.md` y `DCFT_CONTROLLED_REAL_TEST_REPORT.md`.
- Frontend produccion: `https://dcft-frontend.vercel.app`, HTTP 200.
- Backend produccion: `https://dcft.vercel.app/health`, HTTP 200.
- Postgres produccion: `postgres=true`, `sqlite=false`, `persistent=true`, `temporal=false`.
- `security_warnings=[]` en `/health`.

## 3. Admin CEO

No existe un rol literal llamado `admin_ceo` en RBAC. Los roles declarados son `readonly`, `auditor`, `operator`, `tenant_admin` y `super_admin`.

El acceso CEO se protege en `AdminService._ensure_ceo_admin`:

- permitido si `user.role == "super_admin"`;
- permitido si el `username` del usuario coincide con `DCFT_ADMIN_USERNAME`;
- denegado con HTTP 403 y `admin_ceo_required` para usuarios comunes.

El usuario Admin CEO se crea o actualiza por bootstrap al iniciar la app si existen variables:

- `DCFT_ADMIN_USERNAME`;
- `DCFT_ADMIN_PASSWORD`.

El login Admin usa el endpoint existente:

- `POST /auth/login`

El token requerido es Bearer JWT y luego se usa en:

- `GET /admin/ceo/users`;
- `POST /admin/ceo/users/{user_id}/trial`;
- `PATCH /admin/ceo/users/{user_id}/plan`.

Admin CEO esta oculto del publico: no aparece como entrada publica y los endpoints Admin requieren token.

## 4. Validacion de permisos en produccion

Validacion ejecutada contra `https://dcft.vercel.app`:

- `GET /admin/ceo/users` sin token: HTTP 401.
- `POST /admin/ceo/users/user-local-admin/trial` sin token: HTTP 401.
- Login con usuario comun dummy existente: HTTP 200.
- `GET /auth/me` con token comun: HTTP 200.
- `GET /admin/ceo/users` con token comun: HTTP 403.
- `POST /admin/ceo/users/{user_id}/trial` con token comun: HTTP 403.

Resultado: la proteccion 401/403 esta funcionando.

## 5. Trial manual Premium 7 dias

Resultado local automatizado:

- `apps/backend/tests/test_operational_backend.py` valida que Admin CEO puede listar usuarios, activar trial por 7 dias, confirmar plan efectivo premium, cambiar plan y desactivar trial.
- La misma prueba valida que un usuario comun no puede acceder al Admin CEO.

Resultado produccion:

- No se ejecuto activacion manual real en produccion porque no se proporciono credencial/token Admin CEO real en esta validacion.
- El endpoint existe y esta protegido.
- Usuario comun autenticado no puede activar trial: HTTP 403.

Paso exacto requerido para validar el Admin CEO real sin exponer secretos:

1. Confirmar en Vercel Production que existen `DCFT_ADMIN_USERNAME` y `DCFT_ADMIN_PASSWORD`.
2. Redeploy si esas variables fueron agregadas despues del ultimo arranque.
3. Ejecutar login seguro con `POST /auth/login` usando el Admin CEO.
4. No imprimir password ni token completo.
5. Ejecutar `GET /admin/ceo/users` con Bearer token.
6. Seleccionar un usuario de prueba.
7. Ejecutar `POST /admin/ceo/users/{user_id}/trial` con body `{"active": true, "days": 7}`.
8. Verificar inicio/vencimiento, plan efectivo premium y persistencia tras logout/login.

Si el login Admin falla, el bloqueo exacto es de bootstrap/configuracion de `DCFT_ADMIN_USERNAME` o `DCFT_ADMIN_PASSWORD`, no de frontend.

## 6. Audit chain integrity

Estado actual de `https://dcft.vercel.app/runtime/status`:

- HTTP 200.
- `checked_events=243`.
- `legacy_unhashed_events=0`.
- `tamper_detected=false`.
- `hash_mismatch_event_ids=[]`.
- `broken_link_event_ids=[]`.
- `chain_forks_detected=true`.
- `chain_fork_count=10`.

Tenants con heads visibles en runtime:

- `public`;
- `estudiante-pg-20260604074614-648c3b10`;
- `mype-pg-20260604074614-ed8c5041`;
- `deploy-probe-20260604101223-01d283a6`;
- `student-final-20260604101305-99369a77`;
- `mype-final-20260604101305-8fcbe12a`;
- `estudiante-dcft-0605231858`;
- `empresa-dcft-0605231858`.

## 7. Que significa chain_forks_detected

`chain_forks_detected=true` significa que al menos un `previous_hash` tiene mas de un hijo en la tabla de auditoria. Es decir, la cadena tiene ramas multiples.

No significa automaticamente manipulacion de datos. En esta validacion:

- no hay hashes recalculados distintos;
- no hay enlaces rotos;
- no hay eventos legacy sin hash;
- `tamper_detected=false`.

## 8. Causa probable de forks

La causa tecnica mas probable es historica/concurrente:

- la cadena se arma por tenant;
- al escribir un evento se busca el evento previo con `order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())`;
- `created_at` puede venir del momento de creacion del evento, no necesariamente del orden real de insercion/commit;
- con eventos concurrentes, redeploys, cold starts o pruebas paralelas, dos eventos pueden tomar el mismo `previous_hash` y crear ramas;
- runtime muestra heads en tenants de pruebas/deploy fechados 20260604 y 20260605.

Hay un lock por tenant y advisory lock PostgreSQL en la escritura actual, pero el criterio de "ultimo evento" basado en `created_at` deja una ventana historica si los timestamps no reflejan el orden transaccional real.

No hay evidencia en `runtime/status` de migracion rota SQLite/Postgres ni de alteracion de hashes. La fecha exacta del primer fork requiere lectura SQL de solo lectura sobre `audit_events`, por ejemplo agrupando `previous_hash` con `count(*) > 1`; no se ejecuto porque no se dispone de credencial DB en esta validacion y no se debe tocar Postgres destructivamente.

## 9. Impacto

Impacto funcional:

- usuarios: sin impacto observado;
- onboarding/trial: sin impacto observado;
- workspace: sin impacto observado;
- diagnostico: sin impacto observado;
- Postgres: sano y persistente.

Impacto de auditoria:

- no bloquea testers controlados;
- si bloquea declarar una audit chain externa/compliance como totalmente cerrada hasta diagnosticar filas exactas y endurecer el criterio de head;
- no debe ocultarse ni cambiarse a `false` sin explicar y preservar historia.

## 10. Recomendacion

Permitir testers controlados con SUNAT real apagado y con este riesgo documentado.

Antes de auditoria externa fuerte:

1. Crear script/endpoint interno de diagnostico read-only que liste forks por `previous_hash`, tenant, ids y timestamps.
2. Endurecer append de auditoria para usar orden transaccional estable, por ejemplo head table por tenant o secuencia monotona, no solo `created_at`.
3. Preservar eventos historicos; cualquier reconciliacion debe ser documental/no destructiva salvo autorizacion explicita.
4. Validar Admin CEO real con credencial segura y activar un trial manual de prueba.

## 11. Tests ejecutados

- `npm run build`: PASS.
- `.venv\Scripts\python.exe -m compileall apps/backend/app`: PASS.
- `.venv\Scripts\python.exe -m pytest apps/backend/tests/test_operational_backend.py -q`: PASS, `32 passed`.
- Produccion `/health`: PASS.
- Produccion `/runtime/status`: PASS.
- Frontend produccion HTTP 200: PASS.
- Mobile 390x844: PASS.
- Console errors: 0.
- Overflow horizontal: NO.

## 12. Que NO se toco

- No se redisenio DCFT.
- No se modifico frontend.
- No se modifico backend.
- No se modifico auth.
- No se modifico Postgres.
- No se resetearon datos.
- No se borraron audit logs.
- No se alteraron hashes historicos.
- No se implemento SUNAT real.
- No se usaron credenciales SUNAT reales.
- No se hizo push.
- No se hizo deploy.
- No se tocaron FORJA, CEREBRO ni otras apps.
