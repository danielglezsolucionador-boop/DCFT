# DCFT Controlled Dummy Pilot Test Report

Fecha: 2026-06-06

## Alcance

Validacion productiva controlada posterior al deploy del vault SUNAT auxiliar.

Entornos validados:

- Frontend: `https://dcft-frontend.vercel.app`
- Backend: `https://dcft.vercel.app`

Reglas cumplidas:

- No se usaron credenciales SUNAT reales.
- No se uso Clave SOL principal.
- No se imprimio ni guardo password real, token ni clave de cifrado.
- No se activo conector SUNAT real.
- No se ejecutaron declaraciones, pagos, comprobantes ni modificaciones.
- No se tocaron FORJA, CEREBRO, SENTINELA ni otras apps.

## Produccion backend

- `GET /health`: PASS, HTTP 200.
- `GET /runtime/status`: PASS.
- `postgres=true`: PASS.
- `sqlite=false`: PASS.
- `persistent=true`: PASS.
- `temporal=false`: PASS.
- `tamper_detected=false`: PASS.
- `future_chain_hardened=true`: PASS.
- `chain_status=historical_forks_no_tamper`: PASS.

## Estudiante dummy

- Onboarding estudiante: PASS.
- Login estudiante: PASS.
- `/auth/me`: PASS.
- Plan `student`: PASS.
- Sin empresa/RUC creada: PASS.
- Ejercicios disponibles: PASS, 3 ejercicios desde API.
- Persistencia logout/login: PASS.

Cuenta usada: dummy versionada por timestamp para evitar colisiones productivas.

## Empresa MYPE dummy

El RUC dummy exacto `20123456789` ya estaba reservado en produccion y devolvio HTTP 409. Para no tocar datos existentes, se uso un RUC dummy numerico versionado por timestamp.

- Onboarding MYPE: PASS.
- Login MYPE: PASS.
- Empresa y workspace persistentes: PASS.
- `POST /sunat/auxiliary/credentials` sin consentimiento: PASS, bloqueado.
- `POST /sunat/auxiliary/credentials` con consentimiento: PASS.
- `GET /sunat/auxiliary/status`: PASS.
- `DELETE /sunat/auxiliary/credentials`: PASS.
- Persistencia logout/login antes de borrar: PASS.
- Aislamiento tenant cruzado: PASS, otro tenant no accede.
- Username SUNAT vuelve enmascarado: PASS.
- Password SUNAT no vuelve en respuesta: PASS.

Flags confirmados:

- `read_only=true`
- `remote_actions_enabled=false`
- `real_connector_enabled=false`
- `real_sunat_session=false`
- `encrypted_credential_storage=true`

## Empresa Premium dummy

- Onboarding Premium: PASS.
- Login Premium: PASS.
- Empresa y workspace persistentes: PASS.
- `POST /sunat/auxiliary/credentials` sin consentimiento: PASS, bloqueado.
- `POST /sunat/auxiliary/credentials` con consentimiento: PASS.
- `GET /sunat/auxiliary/status`: PASS.
- `DELETE /sunat/auxiliary/credentials`: PASS.
- Persistencia logout/login antes de borrar: PASS.
- Aislamiento tenant cruzado: PASS.
- Username SUNAT vuelve enmascarado: PASS.
- Password SUNAT no vuelve en respuesta: PASS.
- Doctor/Medico y modulos Premium visibles en frontend: PASS por validacion DOM/codigo desplegado.
- Diagnostico pendiente/semaforo pendiente: PASS por frontend y estado sin evidencia inicial.

Flags confirmados:

- `read_only=true`
- `remote_actions_enabled=false`
- `real_connector_enabled=false`
- `real_sunat_session=false`
- `encrypted_credential_storage=true`

## Vault SUNAT auxiliar

Endpoints productivos validados con datos dummy:

- `POST /sunat/auxiliary/credentials`: PASS.
- `GET /sunat/auxiliary/status`: PASS.
- `DELETE /sunat/auxiliary/credentials`: PASS.

Seguridad observada:

- Consentimiento obligatorio: PASS.
- Usuario SUNAT enmascarado: PASS.
- Password SUNAT ausente en respuestas: PASS.
- Username SUNAT completo ausente en respuestas: PASS.
- Payloads de respuesta acotados: PASS, entre 579 y 686 bytes en flujos vault.
- Cifrado activo reportado por API: PASS, `encrypted_credential_storage=true`.

Limitacion: no se inspecciono directamente la fila productiva de PostgreSQL porque no se usaron secretos de base de datos. La evidencia productiva es API/flags/respuestas y la evidencia local de cifrado esta cubierta por tests.

## Frontend y mobile

Mobile 390x844:

- Frontend abre: PASS.
- Entrada estudiante visible: PASS.
- Entrada empresa visible: PASS.
- Campos RUC, usuario secundario SUNAT, clave secundaria SUNAT y plan visibles: PASS.
- Copy seguro visible: PASS, DCFT no declara, no paga y no modifica informacion.
- Sin overflow horizontal: PASS.
- Console errors: 0.

Desktop 1280x720:

- Frontend abre: PASS.
- Entrada estudiante/empresa visible: PASS.
- DCFT, Doctor, Ejercicios, RUC y SUNAT visibles: PASS.
- Sin overflow horizontal: PASS.
- Console errors: 0.

Nota de herramienta: el navegador integrado no pudo escribir formularios por falta de portapapeles virtual, por lo que la autenticacion UI no se uso como fuente principal. La validacion autenticada se hizo por API productiva real y la presencia de controles autenticados se respaldo con codigo desplegado y DOM.

## Validaciones locales

- `npm run build` en `apps/frontend`: PASS.
- `.venv\Scripts\python.exe -m compileall apps\backend\app api -q`: PASS.
- `.venv\Scripts\python.exe -m pytest apps\backend\tests -q`: PASS, 35 tests.
- Secret scan refinado: PASS.

Nota de secret scan: el patron amplio del workflow detecta un falso positivo en `package-lock.json` por `queue-microtask-`. El patron refinado para claves reales (`sk-` con longitud de token, proveedores y private keys) paso sin hallazgos.

## Git y deploy

- Branch local: `main`.
- Ultimo commit local: `1b84b3b fix: shorten sunat event statuses for postgres`.
- `main` no esta ahead de `origin/main`.
- No se hizo push.
- No se hizo deploy.
- No se hicieron cambios funcionales.

Untracked existentes antes del reporte:

- `DCFT_ADMIN_AUDIT_CHAIN_REPORT.md`
- `DCFT_CONTROLLED_REAL_TEST_REPORT.md`

## Riesgos

- Los RUC dummy exactos pueden quedar reservados en produccion tras pilotos previos; para pruebas repetibles conviene usar RUCs dummy versionados.
- No hubo inspeccion directa de logs Vercel ni de filas Postgres porque no se usaron secretos ni acceso administrativo de produccion.
- SUNAT real sigue apagado; la siguiente fase requiere aprobacion humana antes de cualquier conector read-only real.

## Recomendacion

DCFT queda apto para revision CEO del piloto dummy del vault SUNAT auxiliar. El siguiente paso recomendado es ejecutar un piloto asistido con empresa autorizada, siempre con usuario SUNAT auxiliar de consulta, consentimiento explicito y SUNAT real todavia apagado hasta aprobacion.
