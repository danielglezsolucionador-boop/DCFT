# DCFT SUNAT Clave SOL Flow

Fecha: 2026-06-09

## Decisión CEO

DCFT permite a una empresa conectar SUNAT usando RUC, Usuario SOL y Clave SOL con consentimiento expreso. El usuario secundario SUNAT o clave secundaria ya no es obligatorio para el flujo comercial principal.

## Campos de la cabina empresa

La cabina empresa debe pedir solo:

- RUC.
- Usuario SOL.
- Clave SOL.
- Consentimiento expreso.
- Plan MYPE o Premium.
- Periodo mensual o anual.

No debe exigir razón social, correo empresarial, password empresarial, usuario secundario SUNAT ni clave secundaria SUNAT para crear el acceso de empresa.

## Consentimiento obligatorio

Texto oficial:

> Autorizo a DCFT a usar mi RUC, Usuario SOL y Clave SOL para consultar información tributaria disponible en SUNAT, guardar evidencia, generar diagnósticos y mostrar recomendaciones. DCFT no realizará pagos, declaraciones, emisiones, modificaciones ni acciones irreversibles sin autorización expresa.

## Seguridad

- La Clave SOL no se imprime en logs.
- La Clave SOL no vuelve al frontend después de guardar.
- La Clave SOL se guarda cifrada cuando el vault está configurado.
- El Usuario SOL se muestra enmascarado.
- El usuario puede desconectar SUNAT.
- Cada consentimiento queda registrado para auditoría.
- El acceso real puede quedar bloqueado si SUNAT exige captcha o validación manual.

Mensaje oficial de bloqueo manual:

> SUNAT requiere validación manual para continuar. DCFT no puede completar automáticamente esta sesión sin esa validación.

## Alcance permitido

DCFT puede consultar información tributaria disponible en SUNAT para:

- Guardar evidencia.
- Generar diagnósticos.
- Normalizar datos.
- Mostrar recomendaciones.
- Identificar riesgos y brechas.

## Acciones prohibidas

DCFT no debe ejecutar automáticamente:

- Declaraciones.
- Pagos.
- Emisión de comprobantes.
- Modificación de RUC.
- Cambio de Clave SOL.
- Administración de usuarios SUNAT.
- Fraccionamientos.
- Recursos, apelaciones o trámites irreversibles.
- Cualquier acción sensible sin autorización expresa.

## API SUNAT avanzada

Las credenciales API SUNAT, CPE, SIRE Compras y SIRE Ventas quedan como flujo avanzado opcional. No reemplazan el flujo comercial principal de RUC, Usuario SOL y Clave SOL.

## Compatibilidad técnica

Algunos endpoints, nombres de campo y modelos internos mantienen la palabra `auxiliary` por compatibilidad con datos y pruebas anteriores. La semántica de negocio expuesta al CEO y al cliente es `SUNAT_SOL_CREDENTIALS`.

Endpoints de compatibilidad:

- `POST /sunat/auxiliary-access/prepare`.
- `POST /sunat/auxiliary/credentials`.
- `GET /sunat/auxiliary/status`.
- `DELETE /sunat/auxiliary/credentials`.

Estos endpoints deben aceptar el flujo SOL, no exigir usuario secundario SUNAT como requisito comercial.

## Estado esperado

El dashboard empresa debe mostrar:

- Conexión SUNAT.
- RUC.
- Usuario SOL enmascarado.
- Estado de conexión.
- Última lectura.
- Leer SUNAT.
- Diagnóstico automático.
- Desconectar SUNAT.

## Prueba real controlada

Las credenciales reales no deben pedirse ni compartirse por chat. Para una prueba real, el CEO debe ingresar los datos solo en la UI local o en un archivo `.env.local` no commiteado si se requiere una prueba técnica controlada.

Resultado permitido:

- Token o sesión obtenida sin imprimir secreto.
- Error oficial SUNAT claro.
- Bloqueo por captcha o validación manual.
- Evidencia guardada sin secretos.

Resultado no permitido:

- Fingir éxito.
- Imprimir Clave SOL.
- Guardar secretos en reportes.
- Hacer push o deploy.
