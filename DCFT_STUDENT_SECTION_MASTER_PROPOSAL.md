# DCFT Student Section Master Proposal

Fecha local: 2026-06-07

## Estado

Listo para revision CEO.

## Regla CEO obligatoria

- Estado maximo permitido: `Listo para revision CEO.`
- La decision final solo puede venir del CEO de forma explicita.
- Reportes, builds, pruebas, capturas o evidencia tecnica no sustituyen esa decision.
- Ningun documento de trabajo debe elevar el estado por cuenta propia.

## Fuentes leidas

- `C:\Users\admin\ecosystem-memory\AUDITORIA\AUDITORIA_HEART_CABIN.md`
- `C:\Users\admin\ecosystem-memory\AUDITORIA\AUDITORIA_HUMAN_CABIN.md`
- `C:\Users\admin\ecosystem-memory\AUDITORIA\AUDITORIA_TECHNICAL_CABIN.md`
- `C:\Users\admin\ecosystem-memory\AUDITORIA\AUDITORIA_MASTER_BRIEF.md`
- `C:\Users\admin\dcft-knowledge-core\docs\IMPLEMENTATION_MATRIX.md`
- `C:\Users\admin\dcft-knowledge-core\DCFT_OPERATIONAL_V1_CEO_REPORT.md`
- `C:\Users\admin\dcft-knowledge-core\DCFT_STUDENT_FLOW_FINAL_LOCK_REPORT.md`
- `C:\Users\admin\dcft-knowledge-core\DCFT_STUDENT_FLOW_SURGICAL_FIX_REPORT.md`
- `C:\Users\admin\dcft-knowledge-core\DCFT_HEART_CABIN_DISCOVERY_REPORT.md`
- `C:\Users\admin\dcft-knowledge-core\DCFT_AI_PROVIDER_DISCOVERY_REPORT.md`

## Propuesta maestra

La seccion estudiante debe ser una experiencia propia de estudio, no una empresa vacia. Debe permitir que una persona aprenda y practique contabilidad, finanzas y tributacion sin RUC, sin SUNAT real y sin diagnostico empresarial.

La promesa correcta es educativa:

- Crear cuenta estudiante sin RUC.
- Confirmar correo antes de iniciar sesion.
- Practicar con ejercicios guiados por tema.
- Ver solucion paso a paso.
- Preguntar al Doctor de estudio contable, financiero y tributario hasta 5 veces al mes.
- Consultar un Plan Contable base desde la zona de ejercicios.
- Ver MYPE y Premium como camino comercial futuro hacia empresa.
- Mantener SUNAT, reportes empresariales, diagnostico empresarial y workspace como modulos tenues o bloqueados para estudiante.

## Activo ahora

- Registro estudiante por `/onboarding/tenants`.
- Verificacion real de email con token seguro hasheado, expiracion y endpoint de confirmacion.
- Bloqueo de login si el correo no esta verificado.
- Reenvio de verificacion con bloqueo honesto si falta proveedor.
- 30 ejercicios locales: 10 Contabilidad, 10 Finanzas, 10 Tributacion.
- Soluciones guiadas por ejercicio.
- Cuenta estudiante sin RUC.
- Selector Estudiante / Empresa intacto.
- Doctor de estudio contable, financiero y tributario con 5 preguntas mensuales.
- Cuota persistida por usuario, tenant, anio y mes.
- Respuesta IA solo cuando el proveedor esta configurado y habilitado.
- Sin descuento de cuota ante proveedor faltante, error de proveedor o respuesta vacia.
- Plan Contable base con 10 cuentas PCGE iniciales y busqueda local.
- Planes visibles: Estudiante S/0, MYPE S/89 mes / S/890 anio, Premium S/199 mes / S/1,990 anio.
- Checkout real preparado; sin proveedor configurado no activa pago ni plan.

## Proximamente

- Subir ejercicio en PDF.
- Recibir solucion guiada desde PDF propio.
- Descargar solucion en PDF.
- Ampliacion validada del dataset de Plan Contable.
- Webhook de pago para activar plan despues de confirmacion del proveedor.

## Beneficios estudiante

Activo ahora:

- Ejercicios por tema.
- Soluciones guiadas.
- Practica para clases y examenes.
- Doctor de estudio 5 preguntas/mes.
- Plan Contable base.
- Cuenta estudiante sin RUC.

Proximamente:

- Subir ejercicio en PDF.
- Recibir solucion guiada desde PDF propio.
- PDF de respuesta.

## Plan Contable

Debe mostrarse como modulo activo base con el copy:

`Consulta cuentas contables y practica ejercicios con referencia al plan contable.`

Estado actual: base inicial disponible con busqueda local. La ampliacion del dataset queda pendiente de validacion tecnica/contable antes de presentarse como catalogo completo.

## Doctor estudiante

Nombre visible:

`Doctor de estudio contable, financiero y tributario`

Copy visible:

`Puedes hacer hasta 5 preguntas mensuales sobre contabilidad, finanzas y tributacion.`

Fronteras:

- Solo cuenta estudiante.
- No pide RUC.
- No ejecuta SUNAT real.
- No genera diagnostico empresarial.
- No consume cuota si falta proveedor IA.
- No consume cuota si el proveedor falla.
- No consume cuota si la respuesta IA viene vacia.

## Email verification

La experiencia correcta es:

- Crear cuenta no inicia sesion automaticamente.
- Backend genera token seguro.
- Solo se guarda hash del token.
- El token expira.
- El login devuelve `Confirma tu correo para activar tu cuenta.` si falta confirmacion.
- Si no hay proveedor de correo, la UI/API muestran `Falta configurar proveedor de correo para activar cuentas.`
- No se simula envio.

## Checkout

La experiencia correcta es:

- Plan Estudiante no requiere checkout.
- MYPE y Premium muestran mensual/anual.
- Si falta proveedor de pago, API/UI muestran `Falta configurar proveedor de pago para activar checkout real.`
- No se activa plan por boton local.
- No se simula pago.
- Con proveedor Stripe configurado, backend crea una sesion real de checkout y espera confirmacion posterior.

## Criterio tecnico para revision CEO

- Build frontend pasa.
- Tests backend pasan.
- Email sin proveedor bloquea honestamente.
- Login no verificado queda bloqueado.
- Checkout sin proveedor bloquea honestamente.
- Doctor sin proveedor IA bloquea honestamente y conserva cuota.
- Beneficios no duplicados.
- Beneficios activos separados de proximamente.
- PDF marcado como proximamente.
- Empresa no se rompe.
- SUNAT real sigue apagado.
- Mobile sin overflow horizontal.
- Produccion revisada sin deploy desde esta ejecucion.

## Actualizacion Paquete 1 - 2026-06-08

### Fuente maestra corregida

- Fuente primaria desde este paquete: `C:\Users\admin\Desktop\entregar a codex la app doctor cft\DCFT.docx`.
- Espejo operativo: `C:\Users\admin\Desktop\dcft.txt`.
- Soporte conceptual: `1.1_DCFT_CORE_IDENTITY.md`.
- Soporte estudiante/planes: fases `1.2`, `1.7`, `10.2`, `10.3` en `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613`.
- No se mantiene como conclusion operativa que falte cabina corazon para estudiante; `DCFT.docx` queda como brief maestro primario.

### Decision funcional propuesta

- Entrada estudiante limpia con selector estudiante/empresa intacto.
- Beneficios activos separados de proximamente.
- Doctor de estudio activo solo si OpenRouter esta configurado.
- PDF propio como proximo bloque.
- Plan Contable como base inicial/en ampliacion.
- MYPE/Premium como camino comercial, sin pago simulado.
- Modulos empresa visibles tenues/bloqueados para estudiante.

### Estado

- Estado maximo permitido: `Listo para revision CEO.`
- No se declara estudiante aprobado.
- No se hizo push.
- No se hizo deploy.
