# DCFT Student Flow Final Lock Report

Fecha local: 2026-06-06 23:02 -05:00

## Alcance

- Flujo estudiante del frontend DCFT.
- Backend no modificado.
- Postgres no tocado.
- SUNAT real no tocado.
- FORJA, CEREBRO, SENTINELA y ecosistema no tocados.

## Cambios aplicados

- La entrada publica estudiante queda limitada a titulo, copy, correo, contrasena, login estudiante, crear cuenta estudiante y ver beneficios.
- El estudiante sin sesion no ve bottom nav, ejercicios completos, soluciones, diagnostico, reportes, perfil interno, Doctor interno ni modulos empresariales.
- Se agrego drawer compacto `Que encontraras en DCFT` con beneficios de estudio: ejercicios por tema, soluciones guiadas, practica para clases, Doctor futuro y PDF futuro.
- Al iniciar sesion como estudiante, los modulos empresariales quedan visibles como bloqueados o atenuados:
  - Semaforo empresarial: `Disponible para empresas`.
  - Diagnostico empresarial: `Disponible para empresas`.
  - Empresa: `No necesitas empresa para estudiar`.
  - SUNAT: solo para empresas; SUNAT real sigue apagado.
- Doctor estudiante queda como `Doctor de estudio contable, financiero y tributario`.
- Doctor estudiante informa honestamente: `Proximamente: 5 preguntas mensuales para estudiantes`.
- Ejercicios desplazan automaticamente al detalle cuando se selecciona un caso.
- Se agrego bloque honesto `Sube tu propio ejercicio`:
  - PDF permitido en diseno.
  - Maximo previsto: 10 MB.
  - Estado: preparado.
  - Boton disabled: `Subir ejercicio en PDF — Próximamente`.
  - No se implemento resolver falso.
- Se evito que una cuenta estudiante llame `/admin/ceo/users`, eliminando 403 de consola.
- Logout cierra drawer activo, vuelve a modo estudiante y oculta bottom nav.

## Evidencia local

- `npm run build`: PASS.
- Invitado estudiante mobile 390x844:
  - bottom nav: NO.
  - RUC: NO.
  - SUNAT: NO.
  - razon social: NO.
  - Clave SOL: NO.
  - ejercicios completos: NO.
  - soluciones: NO.
  - overflow horizontal: NO.
  - console errors: 0.
- Drawer beneficios:
  - contabilidad: PASS.
  - finanzas: PASS.
  - tributacion: PASS.
  - soluciones guiadas: PASS.
  - practica para clases: PASS.
  - Doctor futuro: PASS.
  - PDF futuro: PASS.
  - beneficios empresa: NO.
- Cuenta estudiante dummy local:
  - plan: `student`.
  - company_created: false.
  - workspace_created: false.
  - bottom nav con sesion: SI.
  - semaforo empresarial bloqueado: PASS.
  - empresa bloqueada: PASS.
  - SUNAT real activo: NO.
- Ejercicios:
  - lista visible con sesion: PASS.
  - boton `Ver solucion`: PASS.
  - scroll al detalle: PASS, detalle visible tras seleccionar ejercicio.
- PDF Exercise Resolver:
  - titulo visible: PASS.
  - estado `Proximamente`: PASS.
  - boton disabled: PASS.
  - resolver falso: NO.
- Doctor estudiante:
  - copy estudiante: PASS.
  - limite futuro 5 preguntas mensuales: PASS.
  - copy `Medico de Cabecera Empresarial` dentro del drawer estudiante: NO.
- Logout:
  - click logout: PASS.
  - bottom nav oculto: PASS.
  - login estudiante visible: PASS.
  - password recordado: NO.
  - RUC en vista logout: NO.
- Flujo empresa local `?access=business`:
  - RUC visible: PASS.
  - SUNAT visible: PASS.
  - usuario secundario SUNAT visible: PASS.
  - copy de consulta segura / vault consent: PASS.
  - overflow horizontal: NO.
  - console errors: 0.

## Produccion

- Frontend: `https://dcft-frontend.vercel.app`.
- Backend: `https://dcft.vercel.app`.
- Deploy frontend: PASS, bundle nuevo servido por Vercel.
- `/health`: PASS.
- `/runtime/status`: PASS.
- Postgres: true.
- SQLite: false.
- Persistent: true.
- Temporal: false.
- Tamper detected: false.
- Future chain hardened: true.
- Chain status: `historical_forks_no_tamper`.
- Invitado estudiante mobile 390x844: PASS.
- Beneficios estudiante produccion: PASS.
- Flujo empresa publico `?access=business`: PASS.
- Cuenta estudiante dummy produccion:
  - plan: `student`.
  - company_created: false.
  - workspace_created: false.
  - bottom nav con sesion: SI.
  - semaforo empresarial bloqueado: PASS.
  - empresa bloqueada: PASS.
  - diagnostico bloqueado: PASS.
  - Doctor estudiante: PASS.
  - ejercicios con solucion: PASS.
  - scroll al detalle: PASS.
  - PDF proximo/deshabilitado: PASS.
  - logout oculta bottom nav: PASS.
  - password recordado: NO.
  - SUNAT real activo: NO.
  - console errors: 0.

## Riesgos pendientes

- El resolver PDF sigue pendiente tecnico hasta aprobar backend seguro de carga, almacenamiento, analisis y trazabilidad.
- El Doctor estudiante sigue pendiente de API/cuota real; la UI lo declara como proximo.
- Las pruebas de cuenta estudiante usaron datos dummy locales, sin credenciales reales.

## Cierre local

Estado local: PASS para publicacion controlada del frontend.

## Cierre produccion

Estado produccion: PASS.

## Validacion final antes de commit

- `npm run build`: PASS.
- Secret scan alta confianza: PASS.
