# DCFT Company Flow Final Lock Report

Fecha: 2026-06-07

## Alcance

- Repo oficial: `C:\Users\admin\dcft-knowledge-core`.
- Flujo empresa MYPE/Premium refinado.
- Vault SUNAT auxiliar controlado validado con datos dummy.
- Flujo estudiante conservado.
- SUNAT real no activado.
- FORJA, CEREBRO y SENTINELA no tocados.

## Backup

- Backup pre-cambio creado: `D:\ECOSYSTEM\BACKUPS\dcft-company-flow-surgery-prechange-20260606-234026.zip`.
- Incluye repo oficial sin `.git`, `.env`, `.venv`, `node_modules`, builds pesados ni caches.

## Cambios funcionales

- Entrada empresa separa cuenta DCFT de credenciales SUNAT auxiliares.
- Empresa sin login ve: RUC, razon social, correo, contrasena empresa, usuario secundario SUNAT, clave secundaria SUNAT, consentimiento, plan MYPE/Premium, Crear cuenta empresa, Entrar como empresa y Ver seguridad.
- Texto residual que confundia login empresa con usuario SUNAT fue reemplazado.
- Consentimiento SUNAT auxiliar ahora muestra error explicito antes de guardar: `Debes aceptar el consentimiento para guardar el acceso SUNAT auxiliar.`
- Panel/drawer empresa agrega acceso directo `Ver seguridad SUNAT`.
- Estado del vault muestra: acceso guardado seguro o pendiente, usuario enmascarado, modo solo consulta, vault cifrado, SUNAT real apagado, sesion real apagada y acciones remotas desactivadas.
- Despues de guardar, el formulario limpia clave y alias SUNAT; el usuario queda visible solo enmascarado en el estado.
- Cuenta `free` deja de clasificarse automaticamente como estudiante; estudiante queda asociado a plan `student`.

## Vault SUNAT auxiliar

- Migracion `0008_sunat_credentials_vault`: presente y migrada en SQLite temporal local.
- Prueba dummy MYPE: PASS.
- Prueba dummy Premium: PASS.
- `POST /sunat/auxiliary/credentials` sin consentimiento: HTTP 400.
- `POST /sunat/auxiliary/credentials` con consentimiento: `CREDENTIAL_RECEIVED`.
- `GET /sunat/auxiliary/status`: `CREDENTIAL_RECEIVED`.
- `DELETE /sunat/auxiliary/credentials`: `DISCONNECTED`.
- Usuario SUNAT dummy: enmascarado.
- Clave SUNAT dummy: no vuelve al frontend.
- Usuario y clave dummy: no aparecen en payload de status ni en drawer.
- `read_only=true`.
- `remote_actions_enabled=false`.
- `real_connector_enabled=false`.
- `real_sunat_session=false`.

## Evidencia visual local

- Desktop drawer SUNAT: `.dcft/outputs/company-flow/business-auth-sunat-drawer-desktop-1280x720.png`.
- Mobile drawer SUNAT: `.dcft/outputs/company-flow/business-auth-sunat-drawer-mobile-390x844.png`.
- Mobile 390x844: overflow horizontal NO.
- Desktop 1280x720: overflow horizontal NO.
- Console errors: 0 en validacion headless.

## Validaciones locales

- `npm run build`: PASS.
- `python -m compileall apps\backend api -q`: PASS.
- `python -m pytest -q`: PASS, 35 passed.
- `python tools\validate_dcft.py`: PASS usando credencial local existente sin imprimirla.
- Secret scan diff funcional: PASS.

## Produccion

- Estado: PASS.
- Commit desplegado: `b453b83`.
- Push main: PASS.
- Frontend production `https://dcft-frontend.vercel.app/?access=business`: PASS.
- Backend production `https://dcft.vercel.app/health`: PASS.
- Backend production `https://dcft.vercel.app/runtime/status`: PASS.
- Vercel frontend desplego automaticamente desde GitHub con commit `b453b83`.
- Intento manual posterior de Vercel CLI no hizo deploy porque la CLI duplico el root `apps/frontend`; no fue necesario porque el auto-deploy ya estaba Ready.
- Frontend production contiene textos nuevos: `No uses tu Clave SOL principal`, consentimiento explicito y `Ver seguridad SUNAT`.
- Modo empresa sin login production: RUC, razon social, MYPE, Premium, SUNAT auxiliar y consentimiento visibles.
- Mobile production 390x844: PASS, overflow horizontal NO.
- Desktop production 1280x720: PASS, overflow horizontal NO.
- Console errors production: 0.
- Captura production: intento por navegador integrado agoto timeout CDP; evidencia DOM/viewport PASS registrada durante validacion.
- Backend production fue validado con:
  - `postgres=true`
  - `sqlite=false`
  - `persistent=true`
  - `temporal=false`
  - `tamper_detected=false`
  - `future_chain_hardened=true`
  - `chain_status=historical_forks_no_tamper`
- Vault SUNAT auxiliar production con datos dummy:
  - Onboarding empresa dummy: PASS.
  - `POST /sunat/auxiliary/credentials` sin consentimiento: HTTP 400.
  - `POST /sunat/auxiliary/credentials` con consentimiento: HTTP 200, `CREDENTIAL_RECEIVED`.
  - `GET /sunat/auxiliary/status`: HTTP 200, `CREDENTIAL_RECEIVED`.
  - `DELETE /sunat/auxiliary/credentials`: HTTP 200, `DISCONNECTED`.
  - Usuario dummy enmascarado: PASS.
  - Usuario y clave dummy no volvieron en payload: PASS.
  - `read_only=true`.
  - `remote_actions_enabled=false`.
  - `real_connector_enabled=false`.
  - `real_sunat_session=false`.
  - `credential_storage_enabled=true`.
  - `encrypted_credential_storage=true`.

## Riesgos

- El flujo SUNAT real sigue apagado por diseno; la siguiente fase debe continuar usando datos dummy o credenciales SUNAT auxiliares autorizadas, nunca Clave SOL principal.
- La evidencia visual del drawer depende del flujo de drawer, no del panel tecnico legacy oculto por la reorganizacion mobile-first.
- La prueba dummy productiva deja un tenant dummy de validacion en Postgres; las credenciales SUNAT dummy fueron desconectadas y borradas del vault.

## Cierre

- DCFT queda desplegado y validado para el flujo empresa MYPE/Premium y vault SUNAT auxiliar controlado.
