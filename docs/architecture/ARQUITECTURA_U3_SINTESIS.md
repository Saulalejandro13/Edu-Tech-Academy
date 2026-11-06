# Síntesis de la arquitectura de Unidad 3 — EduTech Academy

**Naturaleza:** síntesis de los elementos documentados por el equipo en la actividad de Unidad 3. No sustituye al archivo original ni incluye sus diagramas fuente. Conservar el DOCX original en el repositorio oficial.

## Patrón principal

El trabajo de Unidad 3 comparó Transaction Script, Table Module y Domain Model. El equipo seleccionó **Domain Model + Service Layer**, por la combinación de cupos, pagos, trayectorias académicas, cambios de grupo, correcciones, cancelaciones y requisitos de certificación. El dominio concentra invariantes; los Application Services coordinan casos de uso. Repository y Unit of Work separan persistencia y límites transaccionales. Una separación elemental Command/Query evita cargar todo el Domain Model para consultas simples.

## Entidades, agregados y eventos

Entre los conceptos trazados en la arquitectura están `Curso` y `Grupo`, `Inscripcion` y `Pago`, `RegistroAcademico`, `Certificado`, `Cupo`, `Nota`, `CalendarioCurso`, `PorcentajeAsistencia`, `Bitacora`, así como eventos del tipo `InscripcionRealizada`, `PagoRegistrado`, `CursoCancelado`, `CalificacionModificada`, `CambioGrupoAutorizado`, `CertificadoEmitido`.

La **implementación web complementaria** reduce inicialmente el modelo para los flujos de catálogo, cupo, inscripción, pago, asistencia, nota y certificación. No presenta un mapeo completo de todos los aggregates del diseño U3.

## ADRs del trabajo original

- ADR-001 — Uso de Domain Model como patrón principal.
- ADR-002 — Uso de Service Layer para coordinar casos de uso.
- ADR-003 — Uso de Repository para persistencia.
- ADR-004 — Aggregates como límites de consistencia.
- ADR-005 — Value Objects para conceptos sin identidad.
- ADR-006 — Domain Events para comunicación entre procesos.
- ADR-007 — Bitácora de auditoría inmutable.
- ADR-008 — Parametrización de reglas todavía no definidas.
- ADR-009 — Consultas simples para operaciones de solo lectura.

## Artefactos documentados en U3

Dos diagramas de secuencia (certificación y cancelación), diagramas de clases DDD en cuatro vistas, matriz de trazabilidad de los principales casos de uso, ADR y bitácora de uso de IA.

**Tarea de integración pendiente:** cotejar el código final con el documento DOCX original y conservar también los archivos fuente editables de diagramas (por ejemplo .drawio o .puml), no solo imágenes.
