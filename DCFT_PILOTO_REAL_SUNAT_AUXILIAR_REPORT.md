# DCFT Piloto Real Controlado con SUNAT Auxiliar - Reporte

Fecha: 2026-06-06

## 1. Estado capacidad SUNAT actual

DCFT ya tiene una base SUNAT auxiliar:

- `GET /sunat/auxiliary-access/requirements`
- `GET /sunat/data-classification`
- `GET /sunat/status`
- `GET /sunat/connections`
- `GET /sunat/connections/{connection_id}`
- `POST /sunat/connections/connect`
- `POST /sunat/auxiliary-access/prepare`
- `POST /sunat/connections/{connection_id}/disconnect`
- `POST /sunat/connections/{connection_id}/sync`

Modelos existentes:

- `SunatConnection`
- `SunatConsent`
- `SunatConnectionEvent`

Estados/flags existentes o reforzados:

- `real_connector_enabled=false`
- `real_sunat_session=false`
- `read_only=true`
- `remote_actions_enabled=false`
- `pilot_requires_auxiliary_user=true`
- `credential_capture_enabled=true` solo con vault configurado
- `credential_storage_enabled=true` solo con vault configurado

## 2. Diseno seguro de credenciales

Estado actualizado:

- DCFT acepta `sunat_password` solo en el endpoint del vault auxiliar.
- DCFT no acepta `clave_sol` principal.
- DCFT no devuelve `credential_reference` ni claves al frontend.
- DCFT guarda usuario secundario y clave secundaria cifrados con Fernet.
- DCFT registra consentimiento, alias enmascarado y auditoria sanitizada.

Conclusion:

El vault/cifrado ya esta implementado para usuario secundario SUNAT. SUNAT real sigue apagado hasta aprobacion del conector read-only.

## 3. Permisos minimos propuestos

Permitido:

- consultas necesarias para diagnostico;
- ficha RUC;
- estado y condicion del contribuyente;
- obligaciones/alertas visibles en modo consulta;
- comprobantes/compras/ventas solo si son lectura y se aprueban manualmente.

No permitido:

- declaraciones;
- pagos;
- emision de comprobantes;
- modificacion de datos;
- bajas/anulaciones;
- cambios de clave;
- administracion de usuarios;
- tramites de representacion;
- acciones remotas de escritura.

## 4. Estado implementacion

Implementado en esta revision:

- Contrato backend explicito: empresa piloto requiere SUNAT auxiliar.
- `credential_capture_enabled=true` cuando `DCFT_CREDENTIAL_ENCRYPTION_KEY` esta configurada.
- `credential_storage_enabled=true` cuando el vault esta configurado.
- `pilot_requires_auxiliary_user=true`.
- `POST /sunat/auxiliary/credentials`.
- `GET /sunat/auxiliary/status`.
- `DELETE /sunat/auxiliary/credentials`.
- Tests que fijan esos flags.

No implementado:

- Login SUNAT real.
- Conector read-only real.
- Browser automation SUNAT.
- Lectura real de datos privados SUNAT.

## 5. Estado piloto estudiante

Preparado:

- Estudiante no requiere RUC.
- Estudiante no requiere SUNAT auxiliar.
- Debe probar ejercicios y feedback.

## 6. Estado piloto MYPE

Preparado con condicion obligatoria:

- RUC autorizado.
- Usuario secundario SUNAT obligatorio.
- Solo alias/preparacion en DCFT hasta tener vault.
- Diagnostico inicial con datos disponibles o semi-reales autorizados.

## 7. Estado piloto Premium

Preparado con condicion obligatoria:

- RUC autorizado.
- Usuario secundario SUNAT obligatorio.
- Trial Premium 7 dias.
- Medico de cabecera.
- Diagnostico inicial y reporte con datos disponibles o semi-reales autorizados.

## 8. Riesgos

- SUNAT no expone una API formal universal para todos los datos requeridos por diagnostico.
- Si se usa browser automation, puede ser fragil y debe aprobarse como piloto asistido.
- Las acciones de usuarios secundarios son responsabilidad del titular del RUC; por eso DCFT restringe a consulta.
- Sin vault cifrado, almacenar claves reales seria inseguro.

## 9. Que NO se implemento

- No se activo SUNAT real.
- No se guardaron credenciales reales.
- No se pidio Clave SOL principal.
- No se implementaron declaraciones, pagos ni emision.
- No se tocaron FORJA, CEREBRO ni otras apps.

## 10. Que requiere aprobacion CEO

- Proveedor o mecanismo de vault/cifrado.
- Alcance exacto de permisos SUNAT por empresa piloto.
- Si la primera lectura real sera manual/asistida o con conector.
- RUCs y empresas autorizadas.

## 11. Listo para usar SUNAT real

No.

DCFT esta listo para piloto controlado con usuario SUNAT auxiliar preparado, consentimiento y diagnostico semi-real/autorizado.

DCFT esta listo para capturar y guardar credencial secundaria SUNAT cifrada si el vault productivo esta configurado. DCFT no esta listo para abrir sesion SUNAT real ni ejecutar conector read-only real.

## 12. Actualizacion vault/cifrado SUNAT auxiliar

Fecha: 2026-06-06

Se implemento localmente el bloque minimo de seguridad para poder recibir credenciales de usuario secundario SUNAT en piloto controlado:

- Nuevo vault con Fernet en `apps/backend/app/core/credential_vault.py`.
- Nueva variable requerida `DCFT_CREDENTIAL_ENCRYPTION_KEY`.
- Nuevo modelo `SunatCredential`.
- Nueva migracion `0008_sunat_credentials_vault`.
- Nuevos endpoints:
  - `POST /sunat/auxiliary/credentials`
  - `GET /sunat/auxiliary/status`
  - `DELETE /sunat/auxiliary/credentials`
- UI empresa actualizada para RUC, usuario secundario, clave secundaria, consentimiento, guardar acceso seguro y desconectar SUNAT.
- Conector `SunatReadOnlyConnector` preparado pero real SUNAT sigue apagado.

Estado actualizado:

- `credential_capture_enabled=true` solo cuando `DCFT_CREDENTIAL_ENCRYPTION_KEY` esta configurada y es valida.
- `credential_storage_enabled=true` solo cuando el vault esta configurado y es valido.
- `encrypted_credential_storage=true` con vault valido.
- `real_connector_enabled=false`.
- `real_sunat_session=false`.
- `read_only=true`.
- `remote_actions_enabled=false`.

Validacion local:

- `npm run build`: PASS.
- `.venv\Scripts\python.exe -m compileall apps\backend\app api -q`: PASS.
- `.venv\Scripts\python.exe -m pytest apps\backend\tests\test_operational_backend.py -q`: PASS, `35 passed`.
- Secret scan: PASS tras revisar candidatos esperados; sin secretos reales.

Production backend ya tiene `DCFT_CREDENTIAL_ENCRYPTION_KEY` configurada y redeploy realizado. `health` y `runtime/status` fueron validados manualmente antes del push controlado.

## 13. Prueba controlada post-deploy con datos dummy

Fecha: 2026-06-06

Reporte detallado: `DCFT_CONTROLLED_DUMMY_PILOT_TEST_REPORT.md`.

Resultado: PASS con datos dummy versionados.

Validado en produccion:

- Frontend `https://dcft-frontend.vercel.app`: PASS.
- Backend `https://dcft.vercel.app`: PASS.
- `GET /health`: HTTP 200.
- `GET /runtime/status`: PASS.
- `postgres=true`, `sqlite=false`, `persistent=true`, `temporal=false`: PASS.
- `tamper_detected=false`, `future_chain_hardened=true`: PASS.
- Estudiante dummy: onboarding, login, `/auth/me`, ejercicios y persistencia: PASS.
- Empresa MYPE dummy: onboarding, login, vault, status, disconnect, persistencia y aislamiento tenant: PASS.
- Empresa Premium dummy: onboarding, login, vault, status, disconnect, persistencia y aislamiento tenant: PASS.
- Consentimiento obligatorio: PASS.
- Usuario SUNAT enmascarado: PASS.
- Password SUNAT ausente en respuestas: PASS.
- `read_only=true`: PASS.
- `remote_actions_enabled=false`: PASS.
- `real_connector_enabled=false`: PASS.
- `real_sunat_session=false`: PASS.
- `encrypted_credential_storage=true`: PASS.
- Mobile 390x844: PASS, sin overflow y console errors 0.

Observacion: el RUC dummy exacto `20123456789` ya estaba reservado en produccion y devolvio HTTP 409; se uso RUC dummy numerico versionado para no tocar datos existentes.

Validaciones locales posteriores:

- `npm run build`: PASS.
- `compileall`: PASS.
- `pytest`: PASS, 35 tests.
- Secret scan refinado: PASS.

No se usaron credenciales reales, no se imprimieron tokens, no se imprimio la clave de cifrado y no se activo SUNAT real.

## 14. Preparacion piloto asistido con empresa autorizada

Fecha: 2026-06-06

Documentos creados:

- `DCFT_PILOTO_ASISTIDO_EMPRESA_AUTORIZADA_CHECKLIST.md`
- `DCFT_GUIA_EMPRESA_PILOTO_SUNAT_AUXILIAR.md`
- `DCFT_PILOTO_ASISTIDO_MATRIX.md`
- `DCFT_SUNAT_READONLY_CONNECTOR_DESIGN.md`
- `DCFT_PILOTO_ASISTIDO_EMPRESA_AUTORIZADA_REPORT.md`

Produccion validada:

- Frontend: PASS.
- Backend `/health`: PASS.
- Backend `/runtime/status`: PASS.
- Postgres persistente: PASS.
- Vault SUNAT auxiliar configurado y valido: PASS.
- SUNAT real automatico apagado: PASS.

Estado de seguridad:

- No se implemento conector read-only real.
- No se activo sesion SUNAT real.
- No se uso Clave SOL principal.
- No se tocaron backend funcional ni frontend funcional.
- No se tocaron FORJA, CEREBRO, SENTINELA ni ecosistema.

Proximo paso: ejecutar piloto asistido con empresa autorizada y usuario secundario SUNAT de consulta.
