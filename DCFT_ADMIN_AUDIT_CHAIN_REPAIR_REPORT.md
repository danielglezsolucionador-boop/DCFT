# DCFT Admin CEO and Audit Chain Repair Report

Fecha: 2026-06-06 01:04:33 -05:00

## 1. Backup

- Backup pre-cambio creado: `D:\ECOSYSTEM\BACKUPS\dcft-admin-audit-chain-repair-prechange-20260606-005514.zip`.
- Tamano: 40,169,231 bytes.
- Entradas verificadas: 3,545.
- Excluye secretos y artefactos pesados: `.env*`, `.venv`, `node_modules`, `.git`, `.vercel`, caches, builds, logs, sqlite/db locales.
- Branch al iniciar: `main`.
- Commit al iniciar: `3f89bd2602016c3f4eb165bb568528324e0d25c1`.

No fue posible crear export especifico de tablas productivas desde esta maquina porque `.env` local no contiene `DATABASE_URL`. No se hizo pull de secretos desde Vercel y no se imprimieron credenciales.

## 2. Estado Admin CEO

- No existe rol literal `admin_ceo`.
- El acceso Admin CEO se autoriza por `role=super_admin` o por `username == DCFT_ADMIN_USERNAME`.
- El bootstrap crea/actualiza el usuario admin si existen `DCFT_ADMIN_USERNAME` y `DCFT_ADMIN_PASSWORD`.
- `.env` local contiene las claves `DCFT_ADMIN_USERNAME` y `DCFT_ADMIN_PASSWORD`; no se imprimieron valores.
- Endpoints Admin CEO:
  - `GET /admin/ceo/users`
  - `POST /admin/ceo/users/{user_id}/trial`
  - `PATCH /admin/ceo/users/{user_id}/plan`

Validacion productiva sin credenciales:

- `GET https://dcft.vercel.app/admin/ceo/users` sin token: HTTP 401.

Validacion local automatizada:

- Sin token: HTTP 401.
- Usuario comun autenticado: HTTP 403.
- Admin CEO de prueba: HTTP 200.
- Admin CEO de prueba activa trial premium 7 dias: PASS.

Admin CEO real en produccion queda pendiente si no se provee password/token humano. Comando seguro sugerido, sin imprimir password ni token completo:

```powershell
$body = @{
  username = $env:DCFT_ADMIN_USERNAME
  password = $env:DCFT_ADMIN_PASSWORD
} | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri "https://dcft.vercel.app/auth/login" -ContentType "application/json" -Body $body
$token = $login.access_token
Invoke-RestMethod -Method Get -Uri "https://dcft.vercel.app/admin/ceo/users" -Headers @{ Authorization = "Bearer $token" }
```

## 3. Trial manual

Flujo local validado:

- Crear usuario/tenant de prueba.
- Confirmar usuario comun no accede a Admin CEO.
- Login admin de prueba.
- Listar usuarios.
- Activar trial premium 7 dias.
- Confirmar `trial_active=true`.
- Confirmar `plan_effective=premium`.
- Confirmar dashboard del usuario refleja Premium.
- Cambiar plan y desactivar trial.

Flujo productivo real queda listo, bloqueado solo por credencial Admin CEO humana:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "https://dcft.vercel.app/admin/ceo/users/<USER_ID>/trial" `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body (@{ active = $true; days = 7 } | ConvertTo-Json)
```

## 4. Diagnostico audit forks

Produccion antes del deploy de esta reparacion:

- `/runtime/status`: HTTP 200.
- `postgres=true`.
- `sqlite=false`.
- `persistent=true`.
- `temporal=false`.
- `checked_events=251`.
- `legacy_unhashed_events=0`.
- `tamper_detected=false`.
- `hash_mismatch_event_ids=[]`.
- `broken_link_event_ids=[]`.
- `chain_forks_detected=true`.
- `chain_fork_count=10`.

Evidencia:

- No hay hash mismatches.
- No hay broken links.
- No hay eventos legacy sin hash.
- Los forks son ramas por `previous_hash` repetido, no prueba de alteracion.
- Los heads visibles pertenecen a `public` y tenants de pruebas/deploy.
- La query exacta de filas afectadas requiere acceso read-only a `audit_events`; no se ejecuto por falta de `DATABASE_URL` local y para no tocar Postgres sin credencial explicita.

## 5. Causa

La causa confirmada por codigo e historia es fork historico/concurrente de audit chain:

- El modelo usa `previous_hash` y `event_hash` por evento.
- El calculo futuro ya estaba endurecido en el commit `07ad6dc` con lock en memoria por tenant y `pg_advisory_xact_lock` para PostgreSQL.
- Los forks productivos actuales persisten como historia porque no se recalcularon hashes ni se modificaron eventos existentes.
- Recalcular cadena historica no es seguro sin export/read-only detallado y validacion en copia.

## 6. Reparacion aplicada

Reparacion no destructiva aplicada:

- `audit_integrity_summary` ahora mantiene `chain_forks_detected=true` cuando hay forks.
- Agrega `historical_forks=true` cuando hay forks sin tamper, sin legacy y sin broken links.
- Agrega `future_chain_hardened=true` para exponer que el append futuro usa serializacion.
- Agrega `chain_status` con valores:
  - `ok`
  - `historical_forks_no_tamper`
  - `legacy_unhashed_events`
  - `tamper_detected`

No se borraron eventos. No se alteraron hashes. No se recalculo historia. No se toco Postgres.

## 7. Audit antes

- `chain_forks_detected=true`.
- `chain_fork_count=10`.
- `tamper_detected=false`.
- `legacy_unhashed_events=0`.
- `hash_mismatch_event_ids=[]`.
- `broken_link_event_ids=[]`.
- Campos `historical_forks`, `future_chain_hardened` y `chain_status`: no disponibles en produccion antes del deploy.

## 8. Audit despues validado post-deploy

Validado en `https://dcft.vercel.app/runtime/status?final=4cf99c0` despues del deploy:

- `checked_events=254`.
- `chain_forks_detected=true`.
- `chain_fork_count=10`.
- `tamper_detected=false`.
- `legacy_unhashed_events=0`.
- `hash_mismatch_event_ids=[]`.
- `broken_link_event_ids=[]`.
- `historical_forks=true`.
- `future_chain_hardened=true`.
- `chain_status=historical_forks_no_tamper`.

## 9. Tests

- Pruebas puntuales audit/admin: PASS, `3 passed`.
- `npm run build`: PASS.
- `.venv\Scripts\python.exe -m compileall apps/backend/app`: PASS.
- `.venv\Scripts\python.exe -m pytest apps/backend/tests/test_operational_backend.py -q`: PASS, `34 passed`.
- Secret scan basico: PASS; coincidencias revisadas fueron placeholders, nombres de variables o manejo de token en codigo/tests, no secretos reales.

## 10. Produccion validada antes del deploy

- `https://dcft.vercel.app/health`: HTTP 200, `production_ready=true`, `security_warnings=[]`.
- `https://dcft.vercel.app/runtime/status`: HTTP 200.
- `https://dcft.vercel.app/subscriptions/plans`: HTTP 200.
- `https://dcft-frontend.vercel.app/`: HTTP 200.
- Postgres sigue PASS.
- SUNAT real sigue apagado: `ai_pipeline=blocked_provider_disabled`, `ocr_pipeline=placeholder_disabled`; no se habilito conector SUNAT real.

## 10.1 Produccion validada post-deploy

- Commit desplegado por Git push: `4cf99c0`.
- `/health`: HTTP 200, `production_ready=true`, `security_warnings=[]`.
- `/runtime/status`: HTTP 200.
- `/subscriptions/plans`: HTTP 200.
- `/onboarding/status`: HTTP 200.
- Frontend `https://dcft-frontend.vercel.app/?validation=4cf99c0`: HTTP 200.
- `/admin/ceo/users` sin token: HTTP 401.
- `/sunat/auxiliary-access/requirements`: HTTP 200.
- `/sunat/data-classification`: HTTP 200, `remote_actions_enabled=false`.
- Postgres: `postgres=true`, `sqlite=false`, `persistent=true`, `temporal=false`.

## 11. Que NO se toco

- No se redisenio frontend.
- No se tocaron vistas visuales.
- No se implemento SUNAT real.
- No se usaron credenciales SUNAT.
- No se borraron datos.
- No se truncaron tablas.
- No se hizo reset de base de datos.
- No se oculto `chain_forks_detected`.
- No se tocaron FORJA, CEREBRO ni otras apps.

## 12. Riesgos restantes

- Sin `DATABASE_URL` o acceso read-only a Postgres no se pueden listar IDs/timestamps exactos de forks productivos.
- La historia de forks queda preservada y visible; esto no bloquea testers controlados, pero si debe resolverse documentalmente antes de auditoria externa fuerte.
- Admin CEO productivo real requiere password/token humano para cerrar trial manual en produccion.

## 13. Recomendacion

- Autorizar testers controlados.
- Validar Admin CEO real con credencial segura cuando el CEO la ingrese.
- Para auditoria externa, ejecutar diagnostico read-only de `audit_events` y evaluar una reconciliacion documental, no destructiva.
