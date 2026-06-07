# DCFT Operational V1 CEO Report

## 1. Estado previo

- Backup pre-cambio: `D:\ECOSYSTEM\BACKUPS\dcft-operational-v1-prechange-20260605-184725.zip`
- Rama: `main`
- Ultimo commit antes de cambios: `91c2a6b docs: record dcft ceo navigation validation`
- Estado inicial: working tree limpio.

## 2. Alcance ejecutado

- Trabajo local sobre frontend DCFT.
- Sin push.
- Sin deploy.
- Sin cambios en produccion.
- Sin cambios de backend, Postgres, auth ni migraciones.

## 3. Archivos modificados

- `apps/frontend/src/App.tsx`
- `apps/frontend/src/styles.css`
- `apps/frontend/public/doctor-ceo-placeholder-premium.svg`
- `DCFT_OPERATIONAL_V1_CEO_REPORT.md`

## 4. No tocado

- Backend FastAPI.
- Postgres.
- Auth backend.
- Migraciones.
- Configuracion Vercel.
- Variables de entorno productivas.

## 5. Pantalla inicial de acceso

- Nueva pantalla inicial antes del dashboard para usuario sin sesion.
- Muestra DCFT, Doctor Contable Financiero Tributario y Centro Premium de Salud Empresarial.
- Incluye modos: Entrar como estudiante, Entrar como empresa y Admin CEO protegido.
- Estudiante crea cuenta sin RUC.
- Empresa pide RUC, razon social y plan empresarial.
- SUNAT queda como preparacion posterior de consulta.

## 6. Primeros pasos

- Disponible antes de login desde la pantalla inicial.
- Disponible dentro de app desde accesos rapidos y drawer.
- Se mantiene la copia humana "Primeros pasos".
- Contiene bloque SUNAT seguro con:
  - DCFT no declara.
  - DCFT no paga.
  - DCFT no modifica informacion.
  - Solo prepara acceso de consulta para diagnostico.

## 7. Semaforo y diagnostico

- Sin empresa: estado Pendiente con causa visible.
- Empresa/espacio sin informacion: Diagnostico pendiente.
- Simulador local en Diagnostico: Pendiente, Verde / En orden, Ambar / Atencion, Rojo / Riesgo.
- El semaforo muestra color y causa para evitar confundir falta de datos con bug.

## 8. Ejercicios

- 15 ejercicios semilla locales:
  - 5 Contabilidad.
  - 5 Finanzas.
  - 5 Tributacion.
- Cada ejercicio incluye titulo, categoria, nivel, enunciado, pasos guiados, respuesta esperada y explicacion.
- Permite filtrar por categoria, abrir ejercicio, ver solucion y preguntar al Doctor.

## 9. Doctor

- Nuevo asset: `apps/frontend/public/doctor-ceo-placeholder-premium.svg`.
- La UI usa `Doctor DCFT`.
- No queda abreviatura anterior ni asset previo como imagen principal.

## 10. Guias

- Primeros pasos contiene 8 slots de guia.
- Cada slot muestra titulo, duracion, descripcion, estado Pendiente/Disponible y boton de guia escrita.
- Si no hay video, el boton abre guia escrita local y no queda roto.

## 11. SUNAT auxiliar

- Flujo visible dentro de Diagnostico, Primeros pasos y SUNAT auxiliar.
- Campos visibles: RUC, usuario secundario SUNAT, estado y guia.
- Estado/placeholder: Preparado para piloto controlado.
- Boton futuro: Validar pronto.
- No hay campo de password ni clave SUNAT.
- Copy obligatoria visible:
  - DCFT no declara.
  - DCFT no paga.
  - DCFT no modifica informacion.
  - Solo prepara acceso de consulta para diagnostico.

## 12. Prueba Premium 7 dias

- Admin CEO incluye busqueda de usuario.
- Permite activar Premium 7 dias y desactivar prueba.
- Muestra plan base, plan efectivo, inicio, fin y dias restantes cuando backend entrega esos datos.
- Copy de usuario explica que al vencer vuelve al plan base, conserva historial y se bloquean modulos Premium.

## 13. Validacion local

- `npm run build`: PASS.
- `npm test`: no existe script `test` en `apps/frontend/package.json`.
- Browser mobile 390x844: PASS.
- Browser desktop 1366x900: PASS.
- Console errors: 0.
- Overflow horizontal: NO, `overflowX=0`.
- Bottom nav mobile contiene Ejercicios: PASS.
- Accesos rapidos sin SUNAT: PASS.
- Accesos rapidos con Diagnostico: PASS.
- Accesos rapidos con Primeros pasos: PASS.
- Premium muestra solo 3 planes: PASS.
- Ejercicios visibles: 15 cargados, filtro Tributacion devuelve 5, solucion visible: PASS.
- Doctor premium avatar: PASS.
- Primeros pasos: 8 guias, guia escrita, estudiante sin RUC: PASS.
- SUNAT auxiliar: RUC, usuario secundario, estado, guia, Validar pronto, sin password: PASS.

## 14. Validaciones no ejecutadas por restriccion

- Registro/login reales contra API no se ejecutaron para no usar produccion ni Postgres.
- Se intento preparar una API local efimera bajo `work/`, pero Alembic tomo una fuente Postgres externa y la conexion fue rechazada; se detuvo el intento y no quedo backend local corriendo.
- No se cambio backend para corregir esa ruta porque la orden fue no tocar backend.

## 15. Evidencia visual local

- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-operational-v1-mobile-390x844.png`
- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-operational-v1-desktop-1366x900.png`

## 16. Estado final esperado

- Commit local sugerido: `prepare dcft operational v1 flow`
- Pendiente de CEO: aprobacion para push/deploy posterior.

## 17. Correccion flujo empresa con usuario secundario SUNAT

### 17.1 Entrada empresa

- La entrada inicial ahora separa claramente:
  - `Soy estudiante`: correo y contrasena, sin RUC.
  - `Soy empresa`: RUC, usuario secundario SUNAT, clave del usuario secundario SUNAT, razon social opcional y plan MYPE/Premium.
  - `Admin CEO`: acceso protegido para activar pruebas, revisar cuentas y administrar usuarios.
- La empresa ya no entra con copy de correo empresarial; el flujo visible orienta al usuario secundario / auxiliar SUNAT.
- La pantalla inicial muestra `DCFT`, `Doctor Contable Financiero Tributario`, `Centro Premium de Salud Empresarial` y la frase `Diagnostico, prevencion y tranquilidad para la salud empresarial.`.

### 17.2 Textos eliminados

- Eliminado `usuario DCFT`.
- Eliminado `correo registrado de tu empresa`.
- Eliminado `Clave SOL principal`.
- El copy de seguridad usa `acceso principal SUNAT` solo para explicar que no debe compartirse.

### 17.3 Usuario secundario SUNAT

- La experiencia empresa explica que DCFT usa usuario secundario SUNAT solo como acceso de consulta para diagnostico seguro.
- El formulario empresa pide RUC, usuario secundario SUNAT, clave del usuario secundario SUNAT, razon social opcional y plan.
- No se implemento conexion SUNAT real ni se guardaron credenciales nuevas.

### 17.4 Seguridad

- Nuevo bloque `Acceso seguro de consulta`.
- DCFT no puede declarar impuestos, pagar impuestos, emitir facturas, modificar datos ni cambiar informacion de la empresa.
- DCFT solo puede leer informacion autorizada, preparar diagnostico, detectar riesgos, generar alertas y ayudar a prevenir problemas.

### 17.5 Guias y videos

- Nuevo bloque `Primeros pasos para empresas`.
- Guias visibles:
  - Como crear usuario secundario SUNAT.
  - Que permisos debe tener el usuario auxiliar.
  - Que NO puede hacer DCFT con ese usuario.
  - Como conectar tu empresa a DCFT.
  - Como interpretar tu diagnostico.
  - Que significa el semaforo tributario, financiero y contable.
- Si el video no existe, se muestra `Guia escrita disponible mientras preparamos el video.`
- Botones activos: `Ver guia para crear usuario auxiliar`, `Ver seguridad de DCFT` y `Ver primeros pasos`.

### 17.6 Ejercicios estudiante

## 18. Validacion post-deploy del vault SUNAT auxiliar con datos dummy

Fecha: 2026-06-06

Reporte detallado: `DCFT_CONTROLLED_DUMMY_PILOT_TEST_REPORT.md`.

Estado CEO:

- Backend productivo: PASS.
- Frontend productivo: PASS.
- Postgres productivo: PASS.
- Estudiante dummy: PASS.
- Empresa MYPE dummy: PASS.
- Empresa Premium dummy: PASS.
- Vault SUNAT auxiliar: PASS.
- Mobile 390x844: PASS.
- Desktop: PASS.
- Tests locales: PASS.
- Secret scan refinado: PASS.

Seguridad confirmada:

- La clave SUNAT dummy no vuelve al frontend ni a las respuestas API.
- El usuario SUNAT vuelve enmascarado.
- El consentimiento es obligatorio.
- `read_only=true`.
- `remote_actions_enabled=false`.
- `real_connector_enabled=false`.
- `real_sunat_session=false`.
- SUNAT real sigue apagado.

No se hizo push, no se hizo deploy y no se realizaron cambios funcionales durante esta validacion.

## 19. Preparacion de piloto asistido con empresa autorizada

Fecha: 2026-06-06

Estado: preparado documentalmente.

Archivos creados:

- `DCFT_PILOTO_ASISTIDO_EMPRESA_AUTORIZADA_CHECKLIST.md`
- `DCFT_GUIA_EMPRESA_PILOTO_SUNAT_AUXILIAR.md`
- `DCFT_PILOTO_ASISTIDO_MATRIX.md`
- `DCFT_SUNAT_READONLY_CONNECTOR_DESIGN.md`
- `DCFT_PILOTO_ASISTIDO_EMPRESA_AUTORIZADA_REPORT.md`

Produccion:

- Frontend productivo: PASS.
- Backend productivo: PASS.
- Postgres productivo: PASS.
- Vault SUNAT auxiliar: PASS.
- SUNAT real automatico: apagado.

Regla CEO:

- Piloto asistido permitido con empresa autorizada, RUC autorizado, usuario secundario SUNAT, clave secundaria y consentimiento explicito.
- Clave SOL principal prohibida.
- Conector SUNAT real read-only no se implementa ni se activa hasta nueva aprobacion CEO/CTO.

- El flujo estudiante muestra tarjeta protagonista `Ejercicios para estudiantes`.
- Se muestra `15 ejercicios disponibles`.
- Se muestran categorias Contabilidad, Finanzas y Tributacion.
- Boton `Ver ejercicios` abre la vista previa de ejercicios.
- Copy visible: `Puedes ver una vista previa. Para guardar tu avance, crea una cuenta gratuita.`

### 17.7 No tocado

- No se toco backend.
- No se toco Postgres.
- No se toco auth real.
- No se toco Vercel.
- No se hizo push.
- No se hizo deploy.
- No se implemento SUNAT real.
- No se tocaron FORJA ni CEREBRO.

### 17.8 Validaciones locales

- `npm run build`: PASS.
- Frontend local validado en `http://127.0.0.1:5174/` con build preview.
- Mobile 390x844: PASS.
- Desktop 1366x900: PASS.
- Console errors: 0.
- Overflow horizontal: NO.
- Pantalla inicial clara: PASS.
- Estudiante con correo/contrasena: PASS.
- Empresa con usuario secundario SUNAT: PASS.
- Bloque de seguridad empresa: PASS.
- Guias de usuario auxiliar: PASS.
- Ejercicios visibles para estudiante: PASS, 15 ejercicios.
- Textos prohibidos ausentes: PASS.

### 17.9 Evidencia local

- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-sunat-auxiliary-entry-mobile-390x844.png`
- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-sunat-auxiliary-entry-desktop-1366x900.png`
- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-sunat-auxiliary-entry-validation.json`

### 17.10 Pendientes reales

- Validar login real solo cuando el CEO autorice backend/auth local o staging.
- Definir diseno seguro para manejo de credenciales auxiliares antes de cualquier conexion SUNAT real.
- Push/deploy quedan pendientes de aprobacion CEO.

### 17.11 Commit local sugerido

- `polish dcft sunat auxiliary entry and student exercises`

## 18. Push y deploy para revision CEO en celular

### 18.1 Autorizacion y estado Git

- Autorizacion recibida: push/deploy controlado solo para revision CEO en celular.
- Rama: `main`.
- Estado antes del push: `main` ahead de `origin/main` por 2 commits, working tree limpio.
- Commits pendientes confirmados:
  - `a5f498b prepare dcft operational v1 flow`
  - `72c97bb polish dcft sunat auxiliary entry and student exercises`
- Diferencia contra `origin/main` antes del push:
  - `DCFT_OPERATIONAL_V1_CEO_REPORT.md`
  - `apps/frontend/public/doctor-ceo-placeholder-premium.svg`
  - `apps/frontend/src/App.tsx`
  - `apps/frontend/src/styles.css`
- No se modifico backend, Postgres, auth, migraciones ni configuracion productiva.

### 18.2 Validacion local antes/despues de push

- `npm run build` en `apps/frontend`: PASS.
- `.venv\Scripts\python.exe -m compileall apps/backend/app`: PASS.
- `.venv\Scripts\python.exe -m pytest apps/backend/tests/test_operational_backend.py -q`: PASS, 32 tests.
- `secret scan` de patrones reales: PASS; solo aparecieron placeholders `example.com` en CI/tests.
- Frontend local mobile/desktop: PASS.
- Console errors local: 0.
- Overflow horizontal local: NO.

### 18.3 Push y Vercel

- Push ejecutado: `git push origin main`.
- Rango subido: `91c2a6b..72c97bb`.
- Commit de codigo desplegado: `72c97bb7d7fee2e7199d15b296f38512a3103d3a`.
- Vercel frontend:
  - Proyecto: `dcft-frontend`.
  - Estado: Ready.
  - Deployment URL: `https://dcft-frontend-r9iiqx2na-danielglezsolucionador-boops-projects.vercel.app`.
  - Alias final: `https://dcft-frontend.vercel.app`.
  - Creado: Fri Jun 05 2026 22:17:15 GMT-0500.
  - Duracion: 10s.

### 18.4 Validacion frontend produccion

- `GET https://dcft-frontend.vercel.app`: HTTP 200.
- Bundle publicado:
  - JS: `/assets/index-DIveIDrO.js`.
  - Bytes JS aprox.: 243878.
  - API embebida: `https://dcft.vercel.app`.
  - Sin `localhost` embebido.
- Browser produccion:
  - Titulo: `DCFT | Doctor Contable Financiero Tributario`.
  - Console errors: 0.
  - Overflow horizontal: NO.
  - Mobile 390x844: validado con captura Edge.
  - Bottom nav mobile contiene `Ejercicios`: PASS.
  - Entrada inicial contiene `Soy estudiante`, `Soy empresa` y `Admin CEO`: PASS.
  - Entrada empresa visible con usuario secundario SUNAT para diagnostico seguro: PASS.
  - Login empresa tiene campos `Usuario secundario SUNAT` y `Clave del usuario secundario SUNAT` en el bundle publicado: PASS.
  - Accesos rapidos oficiales no incluyen SUNAT: PASS.
  - Accesos rapidos incluyen `Diagnostico`: PASS.
  - Accesos rapidos incluyen `Primeros pasos`: PASS.
  - Primeros pasos visible: PASS.
  - Ejercicios estudiante visibles: PASS, 15 ejercicios.
  - Semaforo muestra estado `Pendiente` y color/causa: PASS.
  - Doctor/Medico de cabecera visible: PASS.
  - Textos prohibidos ausentes:
    - `usuario DCFT`: ausente.
    - `correo registrado de tu empresa`: ausente.
    - `Clave SOL principal`: ausente.
- Planes:
  - UI filtra planes visibles a `student`, `mype`, `premium`: PASS, solo 3 planes de experiencia.
  - Backend publico conserva `free` en `/subscriptions/plans` para compatibilidad API; no aparece como plan comercial principal de la UI.
- Observacion menor:
  - En captura exacta 390x844 el tagline superior queda muy ajustado visualmente, pero no genera overflow horizontal medido.

### 18.5 Validacion backend produccion

- `GET https://dcft.vercel.app/health`: HTTP 200.
- `GET https://dcft.vercel.app/runtime/status`: HTTP 200.
- Runtime productivo confirmado:
  - `postgres=true`.
  - `sqlite=false`.
  - `persistent=true`.
  - `temporal=false`.
  - `database.backend=postgresql`.
  - `database.status=ok`.
  - `database.reason=connection_ok`.
- No se toco backend ni se ejecuto deploy manual de backend.

### 18.6 Auth, registro, trial y Admin CEO

- Frontend produccion apunta al backend real `https://dcft.vercel.app`: PASS.
- `POST /auth/login` con credenciales dummy no secretas: HTTP 401 `invalid_credentials`.
  - Interpretacion: endpoint de login existe, esta conectado y rechaza credenciales invalidas.
  - No se usaron ni imprimieron credenciales reales.
- `GET /auth/me` sin token: HTTP 401 `missing_bearer_token`: PASS, endpoint protegido.
- `GET /admin/ceo/users` sin token: HTTP 401 `missing_bearer_token`: PASS, Admin CEO protegido.
- `GET /onboarding/status`: HTTP 200, signup habilitado y planes disponibles.
- `POST /onboarding/tenants`: preparado en frontend/backend, no ejecutado en produccion para no crear cuentas reales ni tocar Postgres con datos de prueba.
- `GET /subscriptions/plans`: HTTP 200, planes y trial de 7 dias disponibles.
- `GET /dashboard/summary` sin token: HTTP 401 `missing_bearer_token`: PASS, datos empresariales protegidos.
- `GET /onboarding/progress` sin token: HTTP 401 `missing_bearer_token`: PASS, progreso protegido.

### 18.7 SUNAT real

- `GET /sunat/auxiliary-access/requirements`: HTTP 200.
- `GET /sunat/data-classification`: HTTP 200.
- La API declara limites de solo lectura y no requiere permisos para:
  - presentar declaraciones.
  - firmar documentos.
  - enviar formularios.
  - realizar pagos.
  - modificar datos del contribuyente.
  - usar credenciales principales.
- Conexion SUNAT real: NO activada.
- Estado esperado: preparado para piloto controlado / usuario secundario auxiliar.

### 18.8 Evidencia

- Mobile produccion 390x844: `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-production-mobile-390x844.png`
- Desktop produccion 1366x900: `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-production-desktop-1366x900.png`
- Validacion DOM produccion: `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-production-frontend-validation.json`

### 18.9 Resultado

- Produccion frontend: PASS para revision CEO en celular.
- Produccion backend runtime: PASS.
- Auth/login: conectado y protegido; validacion real con usuario productivo queda pendiente de credenciales autorizadas.
- Registro estudiante/empresa: preparado y conectado; no se creo cuenta real por seguridad.
- Trial 7 dias/Admin CEO: preparado y protegido; requiere usuario Admin CEO real para validacion operativa completa.
- SUNAT real: no implementado/no activado, por diseno.
- Recomendacion: listo para revision CEO en URL publica `https://dcft-frontend.vercel.app`.

## 19. Compactacion entrada mobile para revision CEO

### 19.1 Alcance

- Se compacto solo el frontend publico mobile-first.
- No se toco backend.
- No se toco Postgres.
- No se toco auth.
- No se toco SUNAT real.
- No se tocaron migraciones ni otras apps.

### 19.2 Que se compacto

- La entrada publica dejo de mostrar login y formulario completo de crear cuenta al mismo tiempo.
- La entrada ahora muestra un unico formulario protagonista segun modo seleccionado.
- `Crear cuenta nueva` queda como accion secundaria que abre el drawer de Primeros pasos/alta.
- La vista previa completa de beneficios ya no queda abierta debajo de la entrada publica.
- La entrada publica redujo su altura medida en mobile 390x844:
  - Estudiante: `scrollHeight=1362`.
  - Empresa: `scrollHeight=1649`.

### 19.3 Admin CEO

- `Admin CEO` ya no aparece como tercera tarjeta publica.
- La entrada publica muestra solo:
  - `Soy estudiante`.
  - `Soy empresa`.
- La navegacion lateral publica tambien oculta Admin CEO para usuarios sin sesion.
- Admin CEO queda disponible solo como acceso interno mediante `?access=admin` o sesion autorizada.

### 19.4 Seguridad

- El bloque `Acceso seguro de consulta` ya no queda abierto completo en la entrada.
- En modo empresa queda como card compacta con copy corto:
  - DCFT usa usuario secundario SUNAT solo para diagnostico.
  - DCFT no declara.
  - DCFT no paga.
  - DCFT no emite facturas.
  - DCFT no modifica informacion.
- El boton premium `Ver seguridad de DCFT` abre drawer.
- El drawer muestra:
  - DCFT no puede declarar impuestos.
  - DCFT no puede pagar impuestos.
  - DCFT no puede emitir facturas.
  - DCFT no puede modificar datos.
  - DCFT no puede cambiar informacion de la empresa.
  - DCFT solo puede leer informacion autorizada, preparar diagnostico, detectar riesgos, generar alertas y ayudar a prevenir problemas.

### 19.5 Primeros pasos

- Primeros pasos ya no muestra todas las tarjetas abiertas en la entrada.
- En modo empresa queda como card compacta con boton premium `Ver primeros pasos`.
- El drawer muestra la lista esperada:
  - Como crear usuario secundario SUNAT.
  - Que permisos debe tener el usuario auxiliar.
  - Que NO puede hacer DCFT con ese usuario.
  - Como conectar tu empresa a DCFT.
  - Como interpretar tu diagnostico.
  - Que significa el semaforo tributario, financiero y contable.

### 19.6 Beneficios

- `Lo que encontraras en DCFT` ya no queda abierto por defecto.
- Queda como card compacta con boton premium `Ver beneficios`.
- El drawer muestra:
  - Semaforo empresarial.
  - Medico de cabecera.
  - Ejercicios guiados.
  - Primeros pasos.

### 19.7 Estudiante y empresa

- Estudiante mantiene:
  - correo y contrasena.
  - no requiere RUC.
  - ejercicios visibles.
  - 15 ejercicios disponibles.
  - boton `Ver ejercicios`.
- Empresa mantiene:
  - RUC.
  - usuario secundario SUNAT.
  - clave del usuario secundario SUNAT.
  - razon social opcional.
  - plan MYPE/Premium.
  - copy de confianza sin explicacion larga abierta.

### 19.8 Validacion local

- `npm run build`: PASS.
- Mobile 390x844: PASS.
- Desktop 1366x900: PASS.
- Console errors: 0.
- Overflow horizontal: NO.
- Admin CEO no visible en entrada publica: PASS.
- Entrada publica mas corta: PASS.
- Seguridad colapsada en card/boton: PASS.
- Primeros pasos colapsado en card/boton: PASS.
- Beneficios colapsado en card/boton: PASS.
- Drawers/modals funcionan: PASS.
- Ejercicios visibles para estudiante: PASS.
- Empresa con usuario secundario SUNAT: PASS.
- Textos prohibidos ausentes:
  - `usuario DCFT`: ausente.
  - `correo registrado de tu empresa`: ausente.
  - `Clave SOL principal`: ausente.

### 19.9 Evidencia local

- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-compact-local-mobile-student-390x844.png`
- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-compact-local-mobile-business-390x844.png`
- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\outputs\dcft-compact-local-desktop-1366x900.png`

### 19.10 Validacion produccion

- Push ejecutado a `origin/main`.
- Commit desplegado de frontend: `b176023 polish dcft compact mobile entry`.
- Vercel frontend:
  - Proyecto: `dcft-frontend`.
  - Estado: Ready.
  - Deployment URL: `https://dcft-frontend-i9sumackh-danielglezsolucionador-boops-projects.vercel.app`.
  - Alias final: `https://dcft-frontend.vercel.app`.
  - Duracion: 11s.
- Bundle publicado:
  - JS: `/assets/index-D5K9ly2Y.js`.
  - CSS: `/assets/index-D_zaqI5W.css`.
  - API embebida: `https://dcft.vercel.app`.
- Produccion mobile 390x844:
  - Estudiante `scrollHeight=1422`.
  - Empresa `scrollHeight=1709`.
  - Admin CEO no visible en entrada publica: PASS.
  - Solo 2 tarjetas de modo publico: PASS.
  - Seguridad compacta: PASS.
  - Primeros pasos compacto: PASS.
  - Beneficios compacto: PASS.
  - Drawers funcionando: PASS.
  - Console errors: 0.
  - Overflow horizontal: NO.
- Desktop produccion 1366x900:
  - Overflow horizontal: NO.
  - Admin CEO no visible en portal publico: PASS.
- Backend produccion:
  - `GET https://dcft.vercel.app/runtime/status`: HTTP 200.
  - `postgres=true`.
  - `sqlite=false`.
  - `persistent=true`.
  - `temporal=false`.
- SUNAT real: no activado.
- Resultado: listo para revision CEO celular en `https://dcft-frontend.vercel.app`.

### 19.11 Pendientes reales

- Revision CEO en celular real.
- Mantener SUNAT real desactivado hasta diseno seguro de credenciales auxiliares.

## 20. Prueba real controlada V1

### 20.1 Backup creado

- Backup pre-cambio: `D:\ECOSYSTEM\BACKUPS\dcft-controlled-real-test-prechange-20260605-231714.zip`.
- Rama: `main`.
- Ultimo commit: `3f89bd2 docs: record dcft compact mobile production validation`.
- Git status inicial: limpio.

### 20.2 API usada

- Frontend produccion: `https://dcft-frontend.vercel.app`.
- Backend produccion: `https://dcft.vercel.app`.
- Bundle publico apunta a `https://dcft.vercel.app`.
- Bundle publico no contiene `localhost` ni `127.0.0.1`.

### 20.3 Endpoints validados

- `/health`: PASS, HTTP 200.
- `/runtime/status`: PASS, HTTP 200.
- `/subscriptions/plans`: PASS, HTTP 200.
- `/onboarding/status`: PASS, HTTP 200.
- `/auth/login`: PASS con usuarios dummy creados; credenciales invalidas devuelven 401.
- `/auth/register`: no existe; registro real usa `/onboarding/tenants`.
- `/auth/me`: PASS con Bearer token; sin token devuelve 401.
- `/identity/companies`: PASS.
- `/identity/workspaces`: PASS.
- `/identity/context`: PASS.
- `/onboarding/progress`: PASS.
- `/admin/ceo/users`: protegido; sin token 401, usuario comun 403.
- `/sunat/auxiliary-access/requirements`: PASS.
- `/sunat/data-classification`: PASS.
- `/sunat/auxiliary-access/prepare`: PASS sin SUNAT real.

### 20.4 Resultado estudiante

- Usuario dummy: `estudiante.test.dcft.20260605231858@example.com`.
- Registro estudiante: PASS.
- Login estudiante: PASS.
- `/auth/me`: PASS, plan `student`.
- Logout/login: PASS.
- Persistencia: PASS.
- No requiere RUC: PASS.
- Ejercicios visibles: PASS, 15 ejercicios.
- Trial 7 dias activo por onboarding: PASS.

### 20.5 Resultado empresa

- Usuario dummy: `empresa.test.dcft.20260605231858@example.com`.
- RUC dummy: `20123456789`.
- Razon social dummy: `EMPRESA TEST DCFT SAC`.
- Registro empresa: PASS.
- Login empresa: PASS.
- Plan base: `mype`.
- Plan efectivo durante trial: `premium`.
- Diagnostico inicial: pendiente claro.

### 20.6 Resultado workspace

- Empresa creada: `company-e4225f5a3f524307a68a418079efc478`.
- Workspace creado: `workspace-ae618e1268da497ab86fd0512b5fe293`.
- Contexto activo empresa/workspace: PASS.
- Persistencia despues de logout/login: PASS.

### 20.7 Resultado trial

- Estudiante: trial activo 7 dias, vence `2026-06-13T04:19:09Z`.
- Empresa: trial activo 7 dias, vence `2026-06-13T04:19:17Z`.
- Estado persiste en Postgres: PASS.
- Activacion manual desde Admin CEO con token real: pendiente por falta de credenciales admin productivas.

### 20.8 Resultado Admin CEO

- Admin CEO no aparece en entrada publica: PASS.
- Endpoint admin sin token: HTTP 401.
- Endpoint admin con usuario regular: HTTP 403 `admin_ceo_required`.
- Endpoint admin con estudiante: HTTP 403 `admin_ceo_required`.
- Estado: protegido. Validacion con admin real queda pendiente.

### 20.9 Resultado Postgres

- `postgres=true`.
- `sqlite=false`.
- `persistent=true`.
- `temporal=false`.
- Usuarios dummy persisten: PASS.
- Empresa/workspace persiste: PASS.
- Trial persiste: PASS.
- Observacion: runtime muestra `audit_integrity.chain_forks_detected=true`; `tamper_detected=false`.

### 20.10 Resultado seguridad SUNAT auxiliar

- No se uso SUNAT real.
- No se uso Clave SOL real.
- La preparacion SUNAT auxiliar no recibio password.
- `real_connector_enabled=false`.
- `real_sunat_session=false`.
- `read_only=true`.
- `remote_actions_enabled=false`.
- Sync devuelve `NOT_EXECUTED_FOUNDATION_ONLY`.
- UI comunica que DCFT no declara, no paga, no emite facturas y no modifica informacion.

### 20.11 Tests ejecutados

- `npm run build`: PASS.
- `python -m compileall apps\backend api -q`: PASS.
- `python -m pytest apps\backend\tests\test_operational_backend.py -q` con Python global: FAIL por falta de `aiosqlite`.
- `.venv\Scripts\python.exe -m compileall apps\backend api -q`: PASS.
- `.venv\Scripts\python.exe -m pytest apps\backend\tests\test_operational_backend.py -q`: PASS, `32 passed`.
- Secret scan redacted sobre archivos versionados: PASS.
- Frontend produccion HTTP 200: PASS.
- Mobile 390x844: PASS.
- Desktop 1365x900: PASS.
- Console errors: 0.
- Overflow horizontal: NO.

### 20.12 Produccion validada

- Frontend: PASS.
- Backend: PASS.
- Auth: PASS con usuarios dummy.
- Registro estudiante/empresa: PASS.
- Workspace: PASS.
- Trial por onboarding: PASS.
- Admin protegido: PASS.
- SUNAT real apagado: PASS.

### 20.13 Que NO se toco

- No se redisenio.
- No se toco backend.
- No se toco Postgres.
- No se toco auth.
- No se tocaron migraciones.
- No se implemento SUNAT real.
- No se usaron credenciales reales SUNAT.
- No se hizo push.
- No se hizo deploy.
- No se tocaron FORJA, CEREBRO, SENTINELA ni otras apps.

### 20.14 Bloqueos reales

- `/auth/register` no existe; el registro productivo esta conectado por `/onboarding/tenants`.
- Falta token admin CEO real para validar activacion manual de trial desde panel CEO.
- Python global no tiene `aiosqlite`; usar `.venv` para tests.
- Revisar `audit_integrity.chain_forks_detected=true` antes de auditoria externa fuerte.

### 20.15 Recomendacion

- Listo para testers controlados.
- Mantener SUNAT real apagado.
- Siguiente bloque recomendado: validacion Admin CEO con credenciales reales y revision de integridad de audit chain.

## 21. Admin CEO real y audit chain integrity

### 21.1 Backup

- Backup creado: `D:\ECOSYSTEM\BACKUPS\dcft-admin-audit-chain-prechange-20260605-234856.zip`.
- El backup fue creado antes de documentar esta validacion y conserva el estado de `HEAD` mas reportes locales no commiteados.

### 21.2 Estado Admin CEO

- No existe rol literal `admin_ceo`.
- Admin CEO se autoriza por `super_admin` o por usuario cuyo `username` coincide con `DCFT_ADMIN_USERNAME`.
- Si existen `DCFT_ADMIN_USERNAME` y `DCFT_ADMIN_PASSWORD`, el bootstrap crea/actualiza el usuario Admin al arrancar.
- Login Admin: `POST /auth/login`.
- Endpoints Admin: `GET /admin/ceo/users`, `POST /admin/ceo/users/{user_id}/trial`, `PATCH /admin/ceo/users/{user_id}/plan`.

### 21.3 Usuario admin real

- Produccion muestra `security_warnings=[]`, lo que indica que no hay warning de password Admin ausente/debil.
- No se valido login Admin CEO real porque no se proporciono password/token Admin en esta validacion.
- Si el login Admin falla, el paso humano exacto es confirmar `DCFT_ADMIN_USERNAME` y `DCFT_ADMIN_PASSWORD` en Vercel Production y redeployar para que corra el bootstrap.

### 21.4 Trial manual

- Produccion sin token: `POST /admin/ceo/users/user-local-admin/trial` devuelve HTTP 401.
- Produccion con usuario comun autenticado: `POST /admin/ceo/users/{user_id}/trial` devuelve HTTP 403.
- Test local con Admin CEO de prueba activa trial premium 7 dias y confirma plan efectivo premium: PASS.
- Activacion manual real en produccion queda pendiente solo por falta de credencial/token Admin CEO real.

### 21.5 Permisos 401/403

- `GET /admin/ceo/users` sin token: HTTP 401.
- `POST /admin/ceo/users/user-local-admin/trial` sin token: HTTP 401.
- Login usuario comun dummy: HTTP 200.
- `/auth/me` con usuario comun: HTTP 200.
- `GET /admin/ceo/users` con usuario comun: HTTP 403.
- `POST /admin/ceo/users/{user_id}/trial` con usuario comun: HTTP 403.

### 21.6 Audit integrity

- `/runtime/status`: HTTP 200.
- `checked_events=243`.
- `legacy_unhashed_events=0`.
- `tamper_detected=false`.
- `hash_mismatch_event_ids=[]`.
- `broken_link_event_ids=[]`.
- `chain_forks_detected=true`.
- `chain_fork_count=10`.

### 21.7 Causa chain_forks_detected=true

- `chain_forks_detected=true` significa que uno o mas `previous_hash` tienen mas de un hijo.
- No hay evidencia de tampering: no hay hash mismatch, broken links ni eventos sin hash.
- Causa mas probable: eventos historicos/concurrentes de pruebas, deploys o arranques, combinados con seleccion del evento previo por `created_at` en lugar de un orden transaccional monotono.
- Runtime muestra heads en `public` y tenants de pruebas/deploy con fechas 20260604 y 20260605.
- Fecha exacta del primer fork requiere query read-only a `audit_events`; no se hizo lectura SQL porque no se dispone de credencial DB y no se debe tocar Postgres destructivamente.

### 21.8 Impacto real

- No afecta usuarios, onboarding, trial, workspace ni diagnostico.
- No bloquea testers controlados.
- Si bloquea declarar auditoria externa/compliance como completamente cerrada hasta tener diagnostico SQL y hardening de append audit.

### 21.9 Recomendacion

- DCFT puede pasar a testers controlados con SUNAT real apagado.
- Mantener visible `chain_forks_detected=true` hasta diagnostico/hardening.
- Validar Admin CEO real con credencial segura antes de declarar cierre administrativo total.
- No reparar historia ni alterar hashes sin autorizacion explicita.

### 21.10 Tests ejecutados

- `npm run build`: PASS.
- `.venv\Scripts\python.exe -m compileall apps/backend/app`: PASS.
- `.venv\Scripts\python.exe -m pytest apps/backend/tests/test_operational_backend.py -q`: PASS, `32 passed`.
- Produccion `/health`: PASS.
- Produccion `/runtime/status`: PASS.
- Frontend produccion HTTP 200: PASS.
- Mobile 390x844: PASS.
- Console errors: 0.
- Overflow horizontal: NO.

### 21.11 Que NO se toco

- No se modifico frontend.
- No se modifico backend.
- No se modifico auth.
- No se modifico Postgres.
- No se borraron logs.
- No se resetearon datos.
- No se alteraron hashes historicos.
- No se implemento SUNAT real.
- No se hizo push.
- No se hizo deploy.
- No se tocaron FORJA, CEREBRO ni otras apps.

### 21.12 Proximo paso

1. Validar login Admin CEO real con `POST /auth/login` sin imprimir password ni token.
2. Ejecutar `GET /admin/ceo/users` con Bearer token.
3. Activar trial manual en usuario de prueba con `POST /admin/ceo/users/{user_id}/trial` y body `{"active": true, "days": 7}`.
4. Preparar diagnostico read-only de forks por `previous_hash`, tenant, ids y timestamps.

## 22. Reparacion controlada Admin CEO + audit chain

### 22.1 Backup

- Backup pre-cambio: `D:\ECOSYSTEM\BACKUPS\dcft-admin-audit-chain-repair-prechange-20260606-005514.zip`.
- Tamano: 40,169,231 bytes.
- Entradas verificadas: 3,545.
- Branch: `main`.
- Commit base: `3f89bd2602016c3f4eb165bb568528324e0d25c1`.

### 22.2 Admin CEO

- Mecanismo confirmado: `super_admin` o `username == DCFT_ADMIN_USERNAME`.
- `.env` local contiene claves Admin, sin imprimir valores.
- Produccion sin token en `GET /admin/ceo/users`: HTTP 401.
- Tests locales confirman: sin token 401, usuario comun 403, admin de prueba 200.
- Trial manual local con admin de prueba: PASS.
- Trial manual productivo queda pendiente solo por credencial Admin CEO humana.

### 22.3 Audit chain

- Produccion antes del deploy de esta reparacion: `checked_events=251`, `chain_forks_detected=true`, `chain_fork_count=10`, `tamper_detected=false`, `legacy_unhashed_events=0`, sin hash mismatches y sin broken links.
- Produccion post-deploy validada: `checked_events=254`, `chain_forks_detected=true`, `chain_fork_count=10`, `historical_forks=true`, `future_chain_hardened=true`, `chain_status=historical_forks_no_tamper`.
- No hay evidencia de tamper.
- No se recalculo ni se altero historia.
- Reparacion aplicada: runtime/audit ahora distingue forks historicos sin ocultarlos con `historical_forks`, `future_chain_hardened` y `chain_status`.

### 22.4 Tests

- Pruebas puntuales audit/admin: PASS, `3 passed`.
- `npm run build`: PASS.
- `.venv\Scripts\python.exe -m compileall apps/backend/app`: PASS.
- `.venv\Scripts\python.exe -m pytest apps/backend/tests/test_operational_backend.py -q`: PASS, `34 passed`.
- Secret scan basico: PASS, sin secretos reales detectados.

### 22.5 Produccion

- Antes del deploy de esta reparacion: `/health`, `/runtime/status`, `/subscriptions/plans` y frontend HTTP 200.
- Post-deploy commit `4cf99c0`: `/health`, `/runtime/status`, `/subscriptions/plans`, `/onboarding/status`, frontend, SUNAT requirements y data-classification HTTP 200.
- `/admin/ceo/users` sin token: HTTP 401.
- Postgres: `postgres=true`, `sqlite=false`, `persistent=true`, `temporal=false`.
- SUNAT real sigue apagado.

### 22.6 Cierre

- No bloquea testers controlados.
- Si bloquea declarar audit chain externa/compliance como totalmente cerrada hasta tener lectura SQL read-only con IDs/timestamps exactos.
- Reporte dedicado: `DCFT_ADMIN_AUDIT_CHAIN_REPAIR_REPORT.md`.

## 23. Piloto real controlado con SUNAT auxiliar

### 23.1 Cambio CEO

- Empresas del piloto DCFT deben usar usuario secundario SUNAT si o si.
- No se acepta Clave SOL principal.
- No se piden ni guardan accesos principales.
- DCFT no declara, no paga, no emite comprobantes y no modifica informacion.

### 23.2 Capacidad foundation previa al vault

- SUNAT auxiliar foundation existe.
- Endpoints SUNAT existen para requisitos, clasificacion, status, conexiones, preparacion, desconexion y sync bloqueado.
- Modelos existentes: `SunatConnection`, `SunatConsent`, `SunatConnectionEvent`.
- Flags reforzados en esa fase: `pilot_requires_auxiliary_user=true`, `credential_capture_enabled=false`, `credential_storage_enabled=false`, `real_connector_enabled=false`, `real_sunat_session=false`, `read_only=true`, `remote_actions_enabled=false`.

### 23.3 Seguridad credenciales previa al vault

- En esa fase todavia no habia vault/cifrado de credenciales implementado.
- Por seguridad, DCFT no debia guardar clave SUNAT todavia.
- Los payloads SUNAT rechazan campos extra como `password` o `clave_sol`.
- La respuesta no devuelve `credential_reference`.

### 23.4 Piloto

- Tester estudiante: sin RUC y sin SUNAT auxiliar.
- Tester MYPE: RUC autorizado y usuario secundario SUNAT obligatorio.
- Tester Premium: RUC autorizado, usuario secundario SUNAT obligatorio y trial Premium 7 dias.

### 23.5 Documentos creados

- `DCFT_PILOTO_REAL_SUNAT_AUXILIAR_MATRIX.md`.
- `DCFT_GUIA_USUARIO_SECUNDARIO_SUNAT.md`.
- `DCFT_PILOTO_REAL_SUNAT_AUXILIAR_REPORT.md`.

### 23.6 Cierre

- DCFT quedo preparado para piloto controlado con SUNAT auxiliar obligatorio para empresas.
- Esta fase quedo superada por el bloque 24, que agrega vault/cifrado para credenciales secundarias.

## 24. Vault/cifrado SUNAT auxiliar + conector read-only prep

### 24.1 Backup

- Backup pre-cambio: `D:\ECOSYSTEM\BACKUPS\dcft-sunat-vault-readonly-prechange-20260606-051306.zip`.
- Tamano: 39,433,657 bytes.
- Entradas verificadas: 2,953.
- Branch: `main`.
- Commit base local: `1de12b8 docs: record dcft audit chain repair validation`.

### 24.2 Seguridad implementada localmente

- Dependencia nueva: `cryptography==45.0.7`.
- Variable requerida: `DCFT_CREDENTIAL_ENCRYPTION_KEY`.
- Vault Fernet en `apps/backend/app/core/credential_vault.py`.
- Modelo `SunatCredential` y migracion `0008_sunat_credentials_vault`.
- Storage `sunat_credentials` asegurado con `checkfirst=True` en endpoints del vault para Vercel, sin activar Alembic global en cold start.
- Credencial secundaria se guarda cifrada.
- Password no se devuelve al frontend.
- Usuario SUNAT completo no se devuelve al frontend.
- Alias de conexion se guarda enmascarado.
- Logs/audit registran `credential_id`, flags y usuario enmascarado, sin password.

### 24.3 Endpoints

- `POST /sunat/auxiliary/credentials`.
- `GET /sunat/auxiliary/status`.
- `DELETE /sunat/auxiliary/credentials`.

Todos mantienen:

- `read_only=true`.
- `remote_actions_enabled=false`.
- `real_sunat_session=false`.
- `real_connector_enabled=false`.

### 24.4 UI empresa

- Formulario empresa actualizado con RUC, usuario secundario, clave secundaria y consentimiento.
- Boton `Guardar acceso seguro`.
- Boton `Desconectar SUNAT`.
- La clave se limpia despues de guardar.
- Estado de credencial se consulta por `/sunat/auxiliary/status`.

### 24.5 Conector read-only

- Interfaz `SunatReadOnlyConnector` preparada.
- Metodos: `validate_credentials`, `get_ruc_status`, `get_tax_obligations`, `get_basic_alerts`, `disconnect`.
- Estado actual: `NOT_EXECUTED_FOUNDATION_ONLY`.
- No se activo SUNAT real.

### 24.6 Tests y scan

- `npm run build`: PASS.
- `.venv\Scripts\python.exe -m compileall apps\backend\app api -q`: PASS.
- `.venv\Scripts\python.exe -m pytest apps\backend\tests\test_operational_backend.py -q`: PASS, `35 passed`.
- Secret scan de alta confianza: PASS.
- Scan amplio revisado: candidatos fueron placeholders, variables, credenciales dummy de tests o manejo normal de tokens; sin secretos reales.
- Test reforzado: eventos SUNAT mantienen `status` <= 32 caracteres para Postgres.

### 24.7 Produccion

- `DCFT_CREDENTIAL_ENCRYPTION_KEY` fue configurada en Vercel Production por el CEO.
- `DCFT_DB_AUTO_MIGRATE=false` en Vercel Production para evitar 500 por Alembic global en cold start.
- Redeploy backend realizado antes del push controlado.
- `https://dcft.vercel.app/health`: PASS.
- `https://dcft.vercel.app/runtime/status`: PASS.
- Validacion dummy final pendiente despues del push/deploy del bloque.
- Blocker corregido durante deploy: `sunat_connection_events.status` excedia `VARCHAR(32)` en Postgres; codigos acortados y testeados.

### 24.8 Cierre

- DCFT queda listo para push/deploy controlado del vault SUNAT auxiliar.
- No queda autorizado para conectar SUNAT real hasta aprobacion CEO del mecanismo read-only.

## 25. Cirugia fina flujo estudiante

### 25.1 Estado

- Validacion local: PASS.
- Alcance: frontend DCFT.
- Backend: no modificado.
- SUNAT real: no tocado.
- FORJA, CEREBRO y SENTINELA: no tocados.

### 25.2 Cambios

- Textos visibles corregidos para espanol natural en la UI.
- Flujo estudiante separado del flujo empresa.
- Estudiante ve correo, contrasena, ejercicios y acceso sin RUC.
- Estudiante no ve SUNAT, usuario secundario, Clave SOL, razon social ni datos empresariales.
- Empresa conserva RUC, razon social, usuario secundario SUNAT y seguridad de consulta.
- Password eye agregado en login, onboarding y clave secundaria.
- Crear cuenta muestra feedback claro y limpia contrasenas al terminar.

### 25.3 Email verification

- No existe proveedor real SMTP/Resend/SendGrid/Mailgun configurado.
- No existe endpoint real de verificacion de email.
- No existe tabla/token real de verificacion de email.
- Estado documentado: `email_verification_required=false`.
- No se agrego verificacion falsa ni promesa de email inexistente.

### 25.4 Validacion local

- `npm run build`: PASS.
- `python -m compileall apps/backend api tools -q`: PASS.
- `python -m pytest apps/backend/tests -q`: PASS, 35 passed.
- Secret scan alta confianza: PASS.
- Mobile 390x844: PASS.
- Desktop 1280x720: PASS.
- Console errors: 0.
- Overflow horizontal: NO.
- Cuenta estudiante dummy local: PASS, sin imprimir password ni token.

### 25.5 Cierre

- El flujo estudiante queda apto para publicacion controlada.
- Produccion queda pendiente de push/deploy si el CEO autoriza publicar este ajuste frontend.

## 26. Cierre quirurgico final flujo estudiante

### 26.1 Estado

- Validacion local final: PASS.
- Alcance: frontend DCFT.
- Backend: no modificado.
- SUNAT real: no tocado.
- FORJA, CEREBRO y SENTINELA: no tocados.

### 26.2 Control de acceso estudiante

- Estudiante sin sesion ve solo entrada publica: titulo, copy, correo, contrasena, login, crear cuenta y beneficios.
- Estudiante sin sesion no ve bottom nav.
- Estudiante sin sesion no accede a ejercicios completos, soluciones, diagnostico, reportes, perfil interno ni Doctor interno.
- Drawer de beneficios muestra contenido academico, no beneficios empresariales.
- Cuenta estudiante local dummy valida ejercicios con sesion.
- Logout cierra drawers, oculta bottom nav y vuelve a entrada estudiante limpia.

### 26.3 Modulos empresariales para estudiante

- Semaforo empresarial: `Disponible para empresas`.
- Diagnostico empresarial: `Disponible para empresas`.
- Empresa: `No necesitas empresa para estudiar`.
- SUNAT: solo para empresas; SUNAT real apagado.
- Premium queda como vista comercial de desbloqueos.

### 26.4 Ejercicios y PDF

- Seleccionar ejercicio hace scroll al detalle.
- `Ver solucion` queda disponible solo con sesion estudiante.
- Bloque `Sube tu propio ejercicio` agregado en estado preparado.
- PDF maximo previsto: 10 MB.
- Boton `Subir ejercicio en PDF — Próximamente` permanece deshabilitado.
- Resolver PDF real: pendiente tecnico; no se implemento falso resolver.

### 26.5 Validacion local

- `npm run build`: PASS.
- Mobile 390x844 invitado estudiante: PASS.
- Mobile 390x844 estudiante logueado: PASS.
- Flujo empresa local `?access=business`: PASS.
- Console errors: 0.
- Overflow horizontal: NO.
- Secret scan alta confianza: PASS.
- Produccion: pendiente de push/deploy/validacion.
