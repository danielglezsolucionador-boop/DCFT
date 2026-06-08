# DCFT Cabinas Originales Discovery Report

Fecha/hora de busqueda: 2026-06-08 00:01:34 -05:00

## Estado

Busqueda documental dedicada completada.

No se modifico frontend, backend, runtime, SUNAT, produccion ni variables de entorno.

No se declara aprobado. Estado maximo permitido: pendiente decision CEO.

## Proveedores oficiales CEO/CTO

- Email: Resend como objetivo; SMTP como fallback.
- Payment: Stripe.
- AI Doctor estudiante: OpenRouter.

No se imprimieron secretos y no se solicitaron claves por chat.

## Rutas revisadas

- `C:\Users\admin\ecosystem-memory` - existe.
- `C:\Users\admin\ecosystem-memory\DCFT` - no existe.
- `C:\Users\admin\ecosystem-memory\DOCTOR` - no existe.
- `C:\Users\admin\ecosystem-memory\AUDITORIA` - existe.
- `C:\Users\admin\ecosystem-memory\NUBE` - existe.
- `C:\Users\admin\dcft-knowledge-core` - existe.
- `C:\Users\admin\dcft-knowledge-core\docs` - existe.
- `C:\Users\admin\Documents\Codex` - existe.
- `C:\Users\admin\Desktop` - existe.
- `D:\ECOSYSTEM` - existe.
- `D:\ECOSYSTEM\BACKUPS` - existe.

## Comandos usados

Se usaron comandos de solo lectura y filtros de exclusion para no leer `.env`, dependencias, caches ni perfiles de navegador.

- `rg --files --hidden --follow` sobre las rutas existentes.
- `rg -n --hidden --follow --ignore-case` con terminos DCFT/cabinas/estudiante/Doctor/planes.
- `Get-ChildItem -Recurse -File` sobre `D:\ECOSYSTEM\BACKUPS`.
- `System.IO.Compression.ZipFile::OpenRead` para listar entradas internas de ZIP sin extraer contenido.
- `System.IO.Compression.ZipFile::OpenRead` sobre `C:\Users\admin\Desktop\entregar a codex la app doctor cft\DCFT.docx` para extraer texto de `word/document.xml` sin modificar el archivo.
- `Select-String` por categorias: estudiante, Doctor, ejercicios, planes, cabina humana, cabina corazon, cabina tecnica.

Evidencia intermedia generada en el workspace de esta sesion:

- `work\dcft-discovery-document-candidates.txt`: 410 candidatos documentales.
- `work\dcft-discovery-content-matches.txt`: 7479 lineas coincidentes.
- `work\dcft-docx-extracted.txt`: 357 parrafos extraidos del DOCX.
- `work\dcft-discovery-backup-file-candidates.txt`: 326 candidatos en backups descomprimidos/nombres de ZIP.
- `work\dcft-discovery-backup-zip-entry-candidates.txt`: 52291 entradas ZIP con coincidencias amplias; al filtrar DCFT + cabina exacta, no aparece un master original de cabina DCFT, solo migraciones/logs/reporte derivado.

## Archivos encontrados

### Candidatos fuertes

- `C:\Users\admin\Desktop\entregar a codex la app doctor cft\DCFT.docx`
- `C:\Users\admin\Desktop\dcft.txt`
- `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613\forja-knowledge-core\dcft-knowledge-core\phases\phase_1_dcft_foundation\1.1_DCFT_CORE_IDENTITY.md`
- `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613\forja-knowledge-core\dcft-knowledge-core\phases\phase_1_dcft_foundation\1.2_DCFT_USER_LEVELS.md`
- `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613\forja-knowledge-core\dcft-knowledge-core\phases\phase_1_dcft_foundation\1.7_DCFT_EDUCATIONAL_SYSTEM.md`
- `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613\forja-knowledge-core\dcft-knowledge-core\phases\phase_9_enterprise_ux_ui_experience_and_product_ecosystem_design\9.1_DCFT_GLOBAL_UX_UI_AND_PRODUCT_EXPERIENCE_PHILOSOPHY.md`
- `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613\forja-knowledge-core\dcft-knowledge-core\phases\phase_10_enterprise_business_model_growth_and_monetization_ecosystem\10.2_DCFT_FREEMIUM_STRATEGY_AND_CONVERSION_ECOSYSTEM.md`
- `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613\forja-knowledge-core\dcft-knowledge-core\phases\phase_10_enterprise_business_model_growth_and_monetization_ecosystem\10.3_DCFT_SUBSCRIPTION_TIERS_AND_VALUE_DIFFERENTIATION_SYSTEM.md`
- `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613\forja-knowledge-core\dcft-knowledge-core\phases\phase_12_enterprise_integrations_external_ecosystem_and_strategic_connectivity\12.8_DCFT_EDUCATIONAL_AND_UNIVERSITY_INTEGRATION_ECOSYSTEM.md`
- `C:\Users\admin\dcft-knowledge-core\DCFT_HEART_CABIN_DISCOVERY_REPORT.md`
- `C:\Users\admin\dcft-knowledge-core\DCFT_STUDENT_SECTION_MASTER_PROPOSAL.md`
- `C:\Users\admin\dcft-knowledge-core\DCFT_STUDENT_SECTION_IMPLEMENTATION_PLAN.md`
- `C:\Users\admin\ecosystem-memory\AUDITORIA\AUDITORIA_MASTER_BRIEF.md`
- `C:\Users\admin\ecosystem-memory\AUDITORIA\AUDITORIA_HEART_CABIN.md`
- `C:\Users\admin\ecosystem-memory\AUDITORIA\AUDITORIA_HUMAN_CABIN.md`
- `C:\Users\admin\ecosystem-memory\AUDITORIA\AUDITORIA_TECHNICAL_CABIN.md`

### Candidatos debiles

- `C:\Users\admin\dcft-knowledge-core\DCFT_OPERATIONAL_V1_CEO_REPORT.md` - contiene historial operativo y confirma ausencia de cabina corazon exacta, pero no parece brief original.
- `C:\Users\admin\dcft-knowledge-core\phases\PHASE_09_UX_UI_PRODUCT_EXPERIENCE.md` y `PHASE_10_BUSINESS_MODEL_GROWTH_MONETIZATION.md` - actuales, muy resumidos frente a las fases historicas del backup.
- Reportes recientes `DCFT_*_IMPLEMENTATION_REPORT.md` - derivados de ejecuciones, no fuente original.
- `C:\Users\admin\ecosystem-memory\NUBE\NUBE_*_CABIN.md`, `C:\Users\admin\ecosystem-memory\SENTINELA\*`, `D:\ECOSYSTEM\APPS\CEREBRO\*CABIN*` - cabinas reales del ecosistema, pero no son DCFT.
- Backups ZIP `dcft-*prechange*.zip` - utiles para trazabilidad de cambios, no muestran un master original de cabina DCFT.
- Archivos regulatorios `data\regulatory\*\README.md` y PDFs de fuente legal - utiles para corpus, no brief de producto estudiante.

## Fragmentos relevantes sobre estudiantes

- `DCFT.docx`, parrafos 113-120: `Free / Student`, sin login obligatorio inicialmente, ejercicios contables, financieros y tributarios, simulaciones basicas, preguntas educativas y funciones premium visibles pero bloqueadas.
- `1.2_DCFT_USER_LEVELS.md`: Level 1 Student es `Free`, permite practicar ejercicios, aprender contabilidad, tributacion y finanzas.
- `1.7_DCFT_EDUCATIONAL_SYSTEM.md`: usuarios objetivo incluyen estudiantes que desean aprender contabilidad, tributacion, finanzas y administracion empresarial.
- `DCFT_STUDENT_SECTION_MASTER_PROPOSAL.md`: la seccion estudiante debe ser experiencia propia de estudio, sin RUC, sin SUNAT real y sin diagnostico empresarial.

## Fragmentos relevantes sobre Doctor

- `DCFT.docx`, parrafo 3: objetivo de construir DCFT / Doctor Contable Financiero Tributario con arquitectura enterprise fases 1-15.
- `1.1_DCFT_CORE_IDENTITY.md`: nombre oficial `Doctor Contable Financiero Tributario`; plataforma para empresarios, contadores y estudiantes.
- `DCFT_STUDENT_SECTION_MASTER_PROPOSAL.md`: `Doctor de estudio contable, financiero y tributario`, con 5 preguntas mensuales y fronteras educativas.
- `DCFT_AI_PROVIDER_DISCOVERY_REPORT.md`: OpenRouter queda como patron operativo recomendado para activar IA del Doctor cuando CEO/CTO configuren proveedor real.

## Fragmentos relevantes sobre ejercicios

- `DCFT.docx`, parrafos 115-117: ejercicios contables, financieros y tributarios para Free / Student.
- `1.2_DCFT_USER_LEVELS.md`: Student puede practicar ejercicios y usar simulaciones basicas.
- `1.7_DCFT_EDUCATIONAL_SYSTEM.md`: DCFT debe ensenar con ejemplos, simulaciones, ejercicios, explicaciones y escenarios reales.
- `12.8_DCFT_EDUCATIONAL_AND_UNIVERSITY_INTEGRATION_ECOSYSTEM.md`: valor educativo incluye ejercicios inteligentes, simulaciones y casos reales.

## Fragmentos relevantes sobre planes

- `DCFT.docx`, parrafos 106-135: producto y planes: Free / Student, Business Basic, Business Premium.
- `1.2_DCFT_USER_LEVELS.md`: Student Free, Business Basic, Business Premium; premium visibility para incentivar upgrade.
- `10.2_DCFT_FREEMIUM_STRATEGY_AND_CONVERSION_ECOSYSTEM.md`: value before payment; free debe atraer usuarios, generar confianza y permitir valor antes de pagar.
- `10.3_DCFT_SUBSCRIPTION_TIERS_AND_VALUE_DIFFERENTIATION_SYSTEM.md`: el free tier permite ejercicios educativos, simulaciones basicas, consultas basicas y experiencia IA introductoria; no incluye analisis profundos ni workflows premium.
- `DCFT_STUDENT_SECTION_MASTER_PROPOSAL.md`: planes actuales visibles para revision CEO: Estudiante S/0, MYPE S/89 mes / S/890 anio, Premium S/199 mes / S/1990 anio.

## Fragmentos relevantes sobre cabina humana

- No se encontro `DCFT_HUMAN_CABIN.md` ni documento DCFT exacto equivalente.
- `AUDITORIA_HUMAN_CABIN.md`: usa lenguaje de revision humana y ejemplos donde DCFT queda en revision/testers con observaciones.
- `AUDITORIA_MASTER_BRIEF.md`: la cabina humana debe ser sobria, ejecutiva y clara; AUDITORIA revisa calidad visual, experiencia movil, claridad de planes, flujo de usuario, modulos premium y riesgo de confusion de DCFT.
- `9.1_DCFT_GLOBAL_UX_UI_AND_PRODUCT_EXPERIENCE_PHILOSOPHY.md`: DCFT debe sentirse intuitivo, moderno, rapido, seguro, empresarial y premium, usable por estudiantes, empresarios, contadores y usuarios no tecnicos.

## Fragmentos relevantes sobre cabina corazon

- No se encontro archivo exacto de cabina corazon DCFT.
- `DCFT_HEART_CABIN_DISCOVERY_REPORT.md`: confirma que no se encontro archivo exacto de cabina corazon DCFT y que no existe `C:\Users\admin\ecosystem-memory\DCFT`.
- `1.1_DCFT_CORE_IDENTITY.md`: reemplaza mejor la funcion de cabina corazon conceptual: identidad, promesa, usuarios, motores y limites de seguridad.
- `AUDITORIA_HEART_CABIN.md`: evalua apps internas incluido DCFT y prohibe reemplazar a DCFT; sirve como criterio de auditoria, no como cabina corazon DCFT.

## Fragmentos relevantes sobre cabina tecnica

- No se encontro `DCFT_TECHNICAL_CABIN.md` ni `DCFT_TECHNICAL_PROFILE.md` exacto.
- Existen fases tecnicas DCFT historicas en backups: arquitectura, IA, datos, seguridad, UX, monetizacion e integraciones.
- `AUDITORIA_TECHNICAL_CABIN.md`: refuerza evidencia, criterios, estados, scores y reportes para emitir dictamen; aplica como metodologia de revision, no como cabina tecnica DCFT original.

## Conclusion

No aparece una cabina corazon, cabina humana o cabina tecnica original exacta de DCFT en las rutas solicitadas.

El documento mas cercano al brief original es:

- `C:\Users\admin\Desktop\entregar a codex la app doctor cft\DCFT.docx`

El espejo textual mas util es:

- `C:\Users\admin\Desktop\dcft.txt`

La fuente historica mas fuerte para estudiante/planes/educacion es el bloque de fases en:

- `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613\forja-knowledge-core\dcft-knowledge-core\phases`

Si no existe cabina corazon exacta, el documento que mejor reemplaza esa funcion conceptual es:

- `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613\forja-knowledge-core\dcft-knowledge-core\phases\phase_1_dcft_foundation\1.1_DCFT_CORE_IDENTITY.md`

Como funcion de brief operativo maestro, debe usarse:

- `C:\Users\admin\Desktop\entregar a codex la app doctor cft\DCFT.docx`

## Recomendacion de fuente maestra

Para decisiones de la seccion estudiante desde ahora:

1. Fuente maestra primaria: `C:\Users\admin\Desktop\entregar a codex la app doctor cft\DCFT.docx`.
2. Fuente espejo legible: `C:\Users\admin\Desktop\dcft.txt`.
3. Fuente conceptual estudiante/educacion/planes: fases historicas `1.1`, `1.2`, `1.7`, `9.1`, `10.2`, `10.3`, `12.8` del backup `CEREBRO_FINAL_CLOSURE_20260528-222613`.
4. Fuente de criterio de revision: cabinas AUDITORIA disponibles.

No convertir esta recomendacion en aprobacion. La decision de fuente maestra final corresponde al CEO.
