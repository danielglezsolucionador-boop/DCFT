# DCFT SUNAT Auxiliary Vault / Read-Only Prep Report

Fecha: 2026-06-06

## 1. Backup

- Backup pre-cambio: `D:\ECOSYSTEM\BACKUPS\dcft-sunat-vault-readonly-prechange-20260606-051306.zip`.
- Tamano: 39,433,657 bytes.
- Entradas verificadas: 2,953.
- Branch: `main`.
- Commit base local: `1de12b8 docs: record dcft audit chain repair validation`.
- Produccion no fue tocada durante el backup pre-cambio.

## 2. Auditoria previa

Antes de este bloque, DCFT tenia foundation SUNAT auxiliar sin captura segura de clave:

- Endpoints existentes: requirements, data-classification, status, connections, prepare, disconnect y sync bloqueado.
- Modelos existentes: `SunatConnection`, `SunatConsent`, `SunatConnectionEvent`.
- No existia modelo dedicado de credenciales SUNAT.
- No existia `DCFT_CREDENTIAL_ENCRYPTION_KEY`.
- No existia vault/cifrado de credenciales auxiliares.
- Los schemas previos rechazaban campos extra como `password` o `clave_sol`.
- El conector real SUNAT seguia apagado.

## 3. Vault / cifrado

Implementado localmente:

- Dependencia: `cryptography==45.0.7`.
- Variable requerida: `DCFT_CREDENTIAL_ENCRYPTION_KEY`.
- Nuevo modulo: `apps/backend/app/core/credential_vault.py`.
- Cifrado: Fernet simetrico.
- Si la variable falta o es invalida, el guardado de credenciales responde `503` con error seguro.
- En Vercel, la tabla del vault se asegura de forma idempotente con `checkfirst=True` al usar endpoints del vault, evitando ejecutar Alembic global en cada cold start.
- Nunca se guarda la clave SUNAT en texto plano.
- Usuario SUNAT completo solo queda cifrado en `sunat_username_encrypted`.
- Clave secundaria solo queda cifrada en `sunat_password_encrypted`.
- RUC y usuario se devuelven enmascarados.

Comando local para generar una llave sin imprimir credenciales reales:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

La llave generada debe cargarse como secreto de entorno, no versionarse.

## 4. Modelo y migracion

Agregado modelo `SunatCredential` y migracion `0008_sunat_credentials_vault` para tabla `sunat_credentials`.

Campos principales:

- `tenant_id`
- `empresa_id`
- `workspace_id`
- `ruc`
- `sunat_username_encrypted`
- `sunat_password_encrypted`
- `status`
- `read_only=true`
- `remote_actions_enabled=false`
- `last_validated_at`
- `disconnected_at`

## 5. Endpoints seguros

Nuevos endpoints locales:

- `POST /sunat/auxiliary/credentials`
- `GET /sunat/auxiliary/status`
- `DELETE /sunat/auxiliary/credentials`

Propiedades:

- Requieren usuario autenticado y permisos de negocio.
- Validan empresa y workspace.
- Validan que el RUC corresponda a la empresa.
- Requieren consentimiento explicito.
- No devuelven password ni campos cifrados.
- Devuelven `read_only=true`.
- Devuelven `remote_actions_enabled=false`.
- Devuelven `real_sunat_session=false`.
- Devuelven `real_connector_enabled=false`.

## 6. Consentimiento

Texto incorporado:

`Autorizo a DCFT a usar un usuario secundario SUNAT exclusivamente para consulta y diagnostico. DCFT no declara, no paga, no emite comprobantes ni modifica informacion.`

Sin consentimiento no se guarda la credencial.

## 7. Logs y auditoria

Eventos agregados sin secretos:

- `sunat.credential_received`
- `sunat.credential_disconnected`
- evento de conexion `credential_received`

Payloads auditables:

- incluyen `credential_id`, empresa, workspace, flags read-only y usuario enmascarado;
- no incluyen password;
- no incluyen usuario SUNAT completo;
- no incluyen token;
- no incluyen clave cifrada.

## 8. Conector read-only

Preparado `SunatReadOnlyConnector` con interfaz:

- `validate_credentials()`
- `get_ruc_status()`
- `get_tax_obligations()`
- `get_basic_alerts()`
- `disconnect()`

Estado actual:

- `real_connector_enabled=false`
- `real_sunat_session=false`
- `read_only=true`
- `remote_actions_enabled=false`
- `status=NOT_EXECUTED_FOUNDATION_ONLY`

No se implemento automatizacion SUNAT real.

## 9. UI empresa

El flujo empresa ahora permite:

- RUC.
- Usuario secundario SUNAT.
- Clave secundaria SUNAT.
- Checkbox de consentimiento.
- Boton `Guardar acceso seguro`.
- Boton `Desconectar SUNAT`.
- Estado visible de credencial.
- Usuario guardado visible solo enmascarado.

La clave se limpia del estado del formulario despues de guardar.

## 10. Tests

Validaciones ejecutadas:

- `npm run build`: PASS.
- `.venv\Scripts\python.exe -m compileall apps\backend\app api -q`: PASS.
- `.venv\Scripts\python.exe -m pytest apps\backend\tests\test_operational_backend.py -q`: PASS, `35 passed`.

Cobertura nueva:

- Sin consentimiento no guarda.
- Password no se guarda en texto plano.
- Password no vuelve al frontend.
- Usuario SUNAT completo no vuelve en respuestas de credential/status/connections.
- Status devuelve usuario enmascarado.
- DELETE desconecta y borra encrypted username/password.
- `read_only=true`.
- `remote_actions_enabled=false`.
- Otro tenant no puede leer credencial ajena.
- Conector real sigue apagado.

## 11. Secret scan

- Scan de patrones de alta confianza: PASS.
- Scan amplio genero candidatos esperados por placeholders, nombres de variables, credenciales dummy de tests y manejo normal de tokens.
- Revision manual: sin secretos reales detectados.

## 12. Produccion

Production backend fue preparado por el CEO antes del push controlado:

- `DCFT_CREDENTIAL_ENCRYPTION_KEY` configurada en Vercel Production.
- `DCFT_DB_AUTO_MIGRATE=false` en Vercel Production; Alembic global en cold start queda apagado para evitar 500 de arranque.
- Redeploy backend realizado.
- `https://dcft.vercel.app/health`: PASS.
- `https://dcft.vercel.app/runtime/status`: PASS.
- Runtime esperado: `postgres=true`, `sqlite=false`, `persistent=true`, `temporal=false`.

La validacion final de endpoints dummy debe ejecutarse despues del push/deploy de este bloque. Si falta o es invalida la variable, el guardado seguro de credenciales queda bloqueado por diseno con `credential_vault_key_missing` o `credential_vault_key_invalid`.

## 13. Riesgos

- SUNAT puede requerir navegador controlado, captcha o pasos asistidos; no se debe automatizar sin autorizacion CEO.
- La llave de cifrado debe gestionarse como secreto real y con plan de rotacion.
- La tabla guarda credenciales secundarias cifradas; esto exige controles operativos y auditoria.
- El conector read-only todavia no valida contra SUNAT real.

## 14. Cierre local

DCFT queda listo para push/deploy controlado del vault SUNAT auxiliar con credencial dummy.

No queda autorizado para SUNAT real hasta que CEO revise el riesgo de conector read-only y autorice activacion real.
