# DCFT SUNAT Read-Only Intelligence Report

Fecha: 2026-06-08

## Estado

Se implementó la capa SUNAT read-only intelligence sobre el flujo empresa existente de DCFT:

- RUC + usuario secundario SUNAT + clave secundaria guardados solo en vault cifrado.
- Lectura real read-only detrás del flag `SUNAT_READONLY_ENABLED`.
- Acciones sensibles bloqueadas de forma explícita con `SUNAT_ALLOW_SENSITIVE_ACTIONS=false`.
- Permission discovery con permisos recomendados, faltantes, adicionales y sensibles.
- Snapshots raw en PostgreSQL actual.
- Hechos normalizados, corridas de diagnóstico y hallazgos priorizados por severidad.
- Endpoints `/sunat/readonly/*`.
- Dashboard empresa con lectura SUNAT, permisos, hallazgos y bloqueo honesto.

## Seguridad

DCFT no ejecuta:

- declaraciones;
- pagos;
- emisión de comprobantes;
- modificación de RUC;
- cambio de clave;
- administración de usuarios;
- fraccionamientos;
- recursos;
- acciones irreversibles.

El backend descifra la clave secundaria solo durante la corrida read-only. La clave no vuelve al frontend, no se imprime y no se guarda en logs.

## Flags

Variables operativas:

- `SUNAT_READONLY_ENABLED=true`
- `SUNAT_ALLOW_SENSITIVE_ACTIONS=false`
- `SUNAT_STORE_RAW_SNAPSHOTS=true`
- `SUNAT_STORAGE_BACKEND=postgres`
- `SUNAT_EXTERNAL_DATALAKE_ENABLED=false`

`/runtime/status` expone:

- `sunat_readonly_enabled`
- `sensitive_actions_enabled=false`
- `raw_snapshot_storage`
- `external_datalake_enabled=false`
- `storage_backend`
- `real_sunat_session=false` salvo corrida autenticada real
- `remote_actions_enabled=false`
- `real_connector_enabled` solo para lectura read-only

## Tablas

Se agregaron:

- `sunat_permission_checks`
- `sunat_raw_snapshots`
- `sunat_normalized_facts`
- `sunat_diagnostic_runs`
- `sunat_findings`

También se agregó migración Alembic:

- `0012_sunat_readonly_intelligence.py`

## Endpoints

- `POST /sunat/readonly/run`
- `GET /sunat/readonly/status`
- `GET /sunat/readonly/permissions`
- `GET /sunat/readonly/diagnosis`
- `GET /sunat/readonly/findings`
- `GET /sunat/readonly/history`
- `POST /sunat/readonly/refresh`
- `DELETE /sunat/auxiliary/credentials` se mantiene.

## Permisos

La lista mínima recomendada excluye `Credenciales de API SUNAT`.

Si falta un permiso:

> Para responder esta consulta falta habilitar el permiso SUNAT: [nombre exacto del permiso]. Entra a SUNAT → Administración de usuarios secundarios → Modificar programas → marca ese permiso.

Si aparece un permiso sensible:

> Este permiso está disponible, pero DCFT no ejecuta acciones sensibles. Solo puede leer información consultable.

## Bloqueo SUNAT Real

El punto oficial de autenticación SOL observado incluye captcha o validación manual. Si SUNAT lo exige, DCFT registra:

- `BLOCKED_MANUAL_CHALLENGE`
- snapshot de preflight sanitizado
- hallazgo de severidad alta
- cero sesión real
- cero acción remota

No se declara lectura exitosa si SUNAT no permite completar sesión read-only automática.

Fuentes oficiales revisadas:

- https://www.sunat.gob.pe/sol.html
- https://ww1.sunat.gob.pe/xssecurity/SignOnVerification.htm

## Suscripción

Si la suscripción está pendiente o vencida:

- se bloquean nuevas lecturas SUNAT con 402;
- se conserva historial;
- se conserva vault mientras el usuario no desconecte voluntariamente;
- se conserva diagnóstico/snapshots existentes.

## Validación Local

Validado inicialmente:

- `python -m compileall apps\backend api -q`
- `npm --prefix apps/frontend run build`
- `python -m pytest apps/backend/tests/test_operational_backend.py -q -k "sunat_readonly or frontend_company_sunat_auxiliary_flow"`

Resultado inicial: PASS.

## Validación Visual Local

Capturas creadas:

- `outputs/dcft-sunat-readonly-mobile-390x844.png`
- `outputs/dcft-sunat-readonly-desktop-1280x720.png`

Resultado:

- mobile 390x844: sin overflow horizontal, sin loading persistente, consola 0 errores;
- desktop 1280x720: sin overflow horizontal, sin loading persistente, consola 0 errores;
- copy antiguo `SUNAT real automático apagado` no aparece;
- copy read-only visible: lectura SUNAT solo consulta y bloqueo por validación humana si SUNAT lo exige.

## Riesgo

La lectura real de SUNAT puede quedar bloqueada por captcha o controles humanos del portal oficial. Ese bloqueo es esperado y se reporta honestamente. Para una automatización productiva completa puede requerirse canal oficial API, autorización SUNAT o flujo asistido por operador autorizado.
