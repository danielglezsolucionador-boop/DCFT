# DCFT Package 3 - Company MYPE/Premium + SUNAT Auxiliary Report

Fecha local: 2026-06-08 01:05:47 -05:00

## Estado

- Paquete 3 cerrado localmente para revision CEO/CTO.
- No se hizo commit.
- No se hizo push.
- No se hizo deploy.
- Produccion no se toco.
- SUNAT real automatico sigue apagado.

## Fuente maestra

- `C:\Users\admin\Desktop\entregar a codex la app doctor cft\DCFT.docx`.
- Espejo: `C:\Users\admin\Desktop\dcft.txt`.
- Soporte conceptual: `1.1_DCFT_CORE_IDENTITY.md`.
- Soporte planes/fases: `1.2`, `1.7`, `10.2`, `10.3` en `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613`.

## Backup y commit

- Backup pre-cambio: `D:\ECOSYSTEM\BACKUPS\dcft-package-3-company-sunat-prechange-20260608-005019.zip`.
- Commit HEAD al iniciar: `e5e00f4 fix: refine dcft student review flow`.
- Arbol local ya tenia cambios pendientes de paquetes previos; se mantuvieron sin revertir.

## Empresa

- Selector principal conserva `Entrar como estudiante` y `Entrar como empresa`.
- Entrada empresa muestra RUC, razon social, correo, contrasena, usuario secundario SUNAT, clave secundaria SUNAT, consentimiento, plan MYPE/Premium, `Crear cuenta empresa`, `Entrar como empresa` y `Ver seguridad`.
- Ajuste mobile aplicado solo al portal empresa para que los campos clave entren en 390x844.
- Plan MYPE/Premium ahora se muestra como control visible de dos opciones en la entrada empresa.

## MYPE

- Plan MYPE visible como camino empresa.
- Estado sin datos reales conserva diagnostico pendiente y semaforo gris/pendiente.
- Mensaje visible: `Esperando datos autorizados para diagnostico completo.`
- Doctor empresa MYPE documentado como pendiente de proveedor IA y autorizacion CEO; cuota comercial visible: 10 preguntas/mes.

## Premium

- Plan Premium visible como camino empresa.
- Reportes, diagnostico y semaforo no inventan datos cuando falta evidencia real.
- Doctor empresa Premium documentado como pendiente de proveedor IA y autorizacion CEO; cuota comercial visible: 30 preguntas/mes.

## SUNAT auxiliar

- Endpoints existentes validados por tests:
  - `POST /sunat/auxiliary/credentials`.
  - `GET /sunat/auxiliary/status`.
  - `DELETE /sunat/auxiliary/credentials`.
  - `GET /sunat/status`.
- Flags esperadas:
  - `read_only=true`.
  - `real_connector_enabled=false`.
  - `real_sunat_session=false`.
  - `remote_actions_enabled=false`.

## Vault y consentimiento

- Consentimiento obligatorio antes de guardar credenciales auxiliares.
- Password no vuelve al frontend.
- Username vuelve enmascarado.
- Credencial se guarda cifrada por vault.
- Desconexion revoca el registro local del vault.
- Logs/auditoria sanitizados sin imprimir secretos.
- Copy obligatoria visible:
  - `Usa un usuario secundario SUNAT. No uses tu Clave SOL principal.`
  - `DCFT no declara, no paga, no emite comprobantes y no modifica informacion.`
  - `El acceso se guarda cifrado.`
  - `SUNAT real automatico sigue apagado hasta autorizacion.`

## Doctor empresa

- No se activa como IA real en este paquete.
- La UI no promete diagnostico activo sin datos autorizados.
- Texto visible: `Doctor empresa IA pendiente de proveedor IA y autorizacion CEO. MYPE: 10 preguntas/mes. Premium: 30 preguntas/mes.`

## Piloto asistido

- Documentacion actualizada:
  - `DCFT_PILOTO_ASISTIDO_EMPRESA_AUTORIZADA_CHECKLIST.md`.
  - `DCFT_GUIA_EMPRESA_PILOTO_SUNAT_AUXILIAR.md`.
  - `DCFT_PILOTO_ASISTIDO_MATRIX.md`.
  - `DCFT_SUNAT_READONLY_CONNECTOR_DESIGN.md`.
  - `DCFT_PILOTO_ASISTIDO_EMPRESA_AUTORIZADA_REPORT.md`.
- Participantes minimos:
  - 1 estudiante real/controlado.
  - 1 empresa MYPE autorizada.
  - 1 empresa Premium o trial Premium autorizada.
- La matriz no debe incluir passwords, tokens, Clave SOL principal ni secretos de entorno.

## Validacion tecnica

- `npm run build` en `apps/frontend`: PASS.
- `python -m compileall apps\backend api -q`: PASS.
- `$env:PYTHONPATH='apps/backend'; python -m pytest -q`: PASS, 49 passed.
- `git diff --check`: PASS con warnings CRLF solamente.
- Secret scan: no se detectaron secretos reales; hubo coincidencias documentales de nombres de variables en `DCFT_EMAIL_PAYMENT_PROVIDER_SETUP_GUIDE.md`.

## Validacion mobile 390x844

- URL local: `http://127.0.0.1:5174/?access=business`.
- Viewport medido: `390x844`.
- Console errors: 0.
- Loading persistente: NO.
- Overflow horizontal: NO.
- Textos cortados detectados: 0.
- Primera pantalla empresa limpia:
  - RUC visible.
  - Razon social visible.
  - Correo visible.
  - Contrasena visible.
  - Usuario secundario SUNAT visible.
  - Clave secundaria SUNAT visible.
  - Consentimiento visible.
  - MYPE y Premium visibles.
  - Crear cuenta empresa visible.
  - Entrar como empresa visible.
  - Ver seguridad visible.
- Posiciones finales en viewport:
  - RUC: top 185 / bottom 221.
  - Clave secundaria SUNAT: top 395 / bottom 431.
  - Consentimiento: top 437 / bottom 490.
  - Plan MYPE/Premium: top 496 / bottom 530.
  - Acciones: top 536 / bottom 654.

## Estudiante

- Selector estudiante/empresa intacto.
- Ajuste CSS mobile se limita al portal empresa.
- Test estatico conserva `Entrar como estudiante`.

## Produccion

- No push.
- No deploy.
- No Vercel.
- No validacion productiva porque no hubo autorizacion CEO/CTO para publicar este paquete.

## Riesgos

- Falta configuracion real de proveedores para email, pagos e IA si se quiere exponer flujo completo.
- SUNAT real read-only sigue siendo diseno/control futuro; no esta autorizado ni activo.
- El piloto asistido debe ejecutarse con empresa autorizada y usuario secundario, nunca con Clave SOL principal.
- La captura por navegador integrado agoto timeout CDP; la validacion se hizo con viewport real, DOM, consola y mediciones de overflow.

## Recomendacion

Mantener Paquete 3 en estado local para revision CEO/CTO. El siguiente paso debe ser ejecutar piloto asistido controlado con 1 estudiante, 1 MYPE autorizada y 1 Premium/trial autorizada, sin activar SUNAT real automatico.
