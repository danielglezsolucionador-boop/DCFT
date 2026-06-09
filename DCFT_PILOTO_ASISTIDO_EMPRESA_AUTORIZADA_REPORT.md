# DCFT Piloto Asistido con Empresa Autorizada - Reporte

Fecha: 2026-06-06

## 1. Estado actual

DCFT paso la prueba controlada con datos dummy y queda preparado documentalmente para piloto asistido con empresa autorizada.

Produccion validada:

- Frontend `https://dcft-frontend.vercel.app`: PASS.
- Backend `https://dcft.vercel.app/health`: PASS, HTTP 200.
- Runtime `https://dcft.vercel.app/runtime/status`: PASS, HTTP 200.
- `postgres=true`: PASS.
- `sqlite=false`: PASS.
- `persistent=true`: PASS.
- `temporal=false`: PASS.
- `tamper_detected=false`: PASS.
- `future_chain_hardened=true`: PASS.

## 2. Checklist creado

Archivo: `DCFT_PILOTO_ASISTIDO_EMPRESA_AUTORIZADA_CHECKLIST.md`.

Incluye:

- Estudiante.
- Empresa MYPE autorizada.
- Empresa Premium o trial Premium.
- Seguridad.
- Evidencias.
- Cierre por tester.

## 3. Guia empresa creada

Archivo: `DCFT_GUIA_EMPRESA_PILOTO_SUNAT_AUXILIAR.md`.

Incluye:

- Que es DCFT.
- Que se probara.
- Que es usuario secundario SUNAT.
- Por que no usar Clave SOL principal.
- Que puede y no puede hacer DCFT.
- Seguridad del vault.
- Capturas y feedback.

## 4. Matriz creada

Archivo: `DCFT_PILOTO_ASISTIDO_MATRIX.md`.

Incluye placeholders para:

- Estudiante.
- MYPE autorizada.
- Premium o trial Premium.

No contiene datos reales.

## 5. Diseno conector read-only creado

Archivo: `DCFT_SUNAT_READONLY_CONNECTOR_DESIGN.md`.

Estado: diseno solamente. No implementado. No activado.

Define:

- Alcance del conector.
- Validacion de usuario secundario.
- Informacion minima de consulta.
- Acciones prohibidas.
- Manejo de errores, captcha, 2FA y bloqueo SUNAT.
- Recomendacion de piloto manual/asistido antes de browser automation.
- Aprobacion CEO requerida.

## 6. Vault y SUNAT real

Produccion confirma:

- Vault configurado y valido segun requisitos SUNAT auxiliar: PASS.
- `credential_capture_enabled=true`: PASS.
- `credential_storage_enabled=true`: PASS.
- `encrypted_credential_storage=true`: PASS.
- `frontend_secret_echo=false`: PASS.
- `principal_clave_sol_allowed=false`: PASS.

Validacion autenticada con cuenta dummy existente:

- `/sunat/status`: PASS.
- `foundation_only=true`: PASS.
- `real_connector_enabled=false`: PASS.
- `real_sunat_session=false`: PASS.
- `read_only=true`: PASS.
- `remote_actions_enabled=false`: PASS.
- `pilot_requires_auxiliary_user=true`: PASS.

## 7. Riesgos

- El piloto real depende de que la empresa cree bien el usuario secundario SUNAT.
- Permisos excesivos en SUNAT deben evitarse.
- No hay conector real automatico todavia; diagnostico inicial debe ser asistido.
- Captcha/2FA pueden bloquear automatizacion futura.
- Browser automation debe esperar validacion manual/asistida.
- No se debe capturar ni compartir Clave SOL principal.

## 8. Que falta para piloto real

- Seleccionar estudiante tester.
- Seleccionar empresa MYPE autorizada.
- Seleccionar empresa Premium o activar trial Premium.
- Confirmar RUC autorizado.
- Confirmar usuario secundario SUNAT de consulta.
- Confirmar consentimiento.
- Ejecutar checklist.
- Registrar matriz con placeholders reemplazados por datos autorizados, sin claves.
- Recolectar capturas y feedback.

## 9. Que falta para conector real

- Aprobar diseno read-only.
- Definir informacion minima a leer.
- Definir reintentos y limites.
- Definir manejo de captcha/2FA.
- Ejecutar piloto asistido manual primero.
- Obtener aprobacion CEO/CTO para activar cualquier sesion SUNAT real.

## 10. Proximo paso

Ejecutar piloto asistido con testers autorizados, manteniendo SUNAT real automatico apagado y usando solo usuario secundario SUNAT con permisos de consulta.

## 11. Actualizacion Paquete 3 - 2026-06-08

Estado local:

- Paquete 3 empresa MYPE/Premium + SUNAT auxiliar cerrado localmente para revision CEO/CTO.
- No se hizo push.
- No se hizo deploy.
- Produccion no se toco.
- SUNAT real automatico sigue apagado.

Evidencia local:

- Entrada empresa mobile 390x844 validada en `http://127.0.0.1:5174/?access=business`.
- Primera pantalla empresa sin loading persistente, sin overflow horizontal, sin textos cortados detectados y con console errors 0.
- RUC, usuario secundario SUNAT, clave secundaria SUNAT, consentimiento y plan MYPE/Premium quedan como flujo inicial vigente; razón social queda pendiente de validación y correo/contraseña empresarial no son obligatorios.

Piloto asistido minimo:

- 1 estudiante real/controlado.
- 1 empresa MYPE autorizada.
- 1 empresa Premium o trial Premium autorizada.

Reglas reforzadas:

- No poner claves en matriz.
- No pedir ni usar Clave SOL principal.
- No activar sesion SUNAT real automatica.
- No declarar, no pagar, no emitir comprobantes y no modificar informacion.
- Usar solo usuario secundario SUNAT con consentimiento explicito.

Validacion local:

- `npm run build`: PASS.
- `python -m compileall apps\backend api -q`: PASS.
- `$env:PYTHONPATH='apps/backend'; python -m pytest -q`: PASS, 49 passed.
- `git diff --check`: PASS con warnings CRLF solamente.
- Secret scan: sin secretos reales detectados; coincidencias documentales de nombres de variables en guia de proveedores.
