# DCFT Student Section Implementation Plan

Fecha local: 2026-06-07

## Regla obligatoria

No declarar "estudiante aprobado", "seccion estudiante aprobada" ni "experiencia estudiante aprobada" hasta que el CEO lo diga expresamente.

Estado maximo permitido: `Listo para revision CEO.`

## Alcance

Aplicar solo ajustes quirurgicos de frontend si son seguros:

- Beneficios no duplicados.
- Beneficios separados entre activo ahora y proximamente.
- Doctor estudiante como proximamente.
- PDF propio como proximamente.
- Modulos empresariales tenues.
- Planes MYPE/Premium como camino comercial.
- Selector estudiante/empresa intacto.

No tocar backend salvo necesidad real. No tocar SUNAT real.

## A. Cambios que se pueden hacer ahora sin backend

1. Dejar un solo CTA principal `Ver beneficios` en la entrada estudiante publica.
2. Hacer el CTA de beneficios mas fuerte, ancho y visualmente premium.
3. Reestructurar el drawer de beneficios en dos bloques: `Activo ahora` y `Proximamente`.
4. Ajustar copy del Doctor de estudio para que diga claramente `Proximamente`.
5. Ajustar copy de PDF propio para que diga claramente `Subir ejercicio en PDF - Proximamente`.
6. Mantener boton de PDF deshabilitado.
7. Afinar opacidad/estilo de modulos empresariales bloqueados para estudiante.
8. Cambiar accesos rapidos del estudiante a Ejercicios, Doctor proximamente, Planes y Perfil.
9. Reforzar planes como camino comercial: Estudiante gratis, MYPE S/ 89 / mes, Premium S/ 199 / mes.
10. Mantener selector estudiante/empresa intacto.

## B. Cambios que requieren backend

1. Limite real mensual de preguntas del Doctor por usuario.
2. Persistencia de uso mensual del Doctor.
3. Registro de eventos de preguntas/respuestas.
4. Estado real de feature flags por usuario o plan.
5. Conversion real de estudiante a empresa con migracion de cuenta si requiere flujo persistente.
6. Control real de elegibilidad para prueba Premium solicitada desde estudiante.

## C. Cambios que requieren IA/API

1. Doctor de estudio real.
2. Respuestas trazables sobre contabilidad, finanzas y tributacion.
3. Moderacion/seguridad de preguntas.
4. Explicaciones pedagogicas con fuentes o criterios.
5. Resumen de ejercicios y solucion asistida.

## D. Cambios que requieren storage/upload

1. Upload de PDF propio.
2. Validacion real de archivo, peso, tipo MIME y antivirus si aplica.
3. Storage seguro.
4. Extraccion de texto/OCR.
5. Analisis del ejercicio.
6. Generacion de solucion guiada.
7. Generacion o descarga de PDF de respuesta.
8. Retencion y borrado de archivos.

## E. Cambios que requieren email provider

1. Email verification real.
2. Token de verificacion con expiracion.
3. Endpoint de confirmacion.
4. Reenvio de correo.
5. Plantilla transaccional.
6. Variables de proveedor SMTP/Resend/SendGrid/Mailgun.
7. Politica de bloqueo si email no esta verificado.

Mientras no exista proveedor real, el mensaje correcto es:

`Cuenta estudiante creada correctamente.`

No decir que se envio correo.

## F. Cambios que quedan para fase posterior

1. Checkout real.
2. Facturacion.
3. Activacion automatica de MYPE/Premium por pago.
4. SUNAT real read-only.
5. Browser automation SUNAT.
6. Piloto con empresa real sin supervision.
7. App Store / Play Store.
8. Auditoria externa completa.

## Validacion requerida si se implementa frontend

Local:

- `npm run build`
- Mobile 390x844 sin overflow horizontal.
- Console errors: 0.
- Selector estudiante/empresa intacto.
- Un solo `Ver beneficios` principal en estudiante publico.
- Beneficios separados: activo ahora / proximamente.
- Doctor estudiante claramente proximamente.
- PDF claramente proximamente.
- Modulos empresariales tenues.
- Planes visibles como camino comercial.
- Empresa no rota.

Produccion:

- `https://dcft-frontend.vercel.app`
- `https://dcft-frontend.vercel.app/?access=business`
- `https://dcft.vercel.app/runtime/status`

Backend esperado:

- `postgres=true`
- `sqlite=false`
- `persistent=true`
- `temporal=false`
- SUNAT real apagado.
