# Trazabilidad parcial a código y pruebas

| Regla / Historia | Caso de uso | Código implementado | Evidencia de prueba | Estado |
|---|---|---|---|---|
| BR-01 / US-01 | Crear y consultar catálogo | `application/services.py: crear_curso, cursos`; `api/main.py: /cursos` | `test_catalogo_y_validaciones` | Parcial: no todas las propiedades del curso |
| BR-02 / US-02 | Inscripción individual | `Curso.inscribir`; `EduTechService.inscribir` | `test_inscripcion_pago_academico_certificacion` | Parcial: falta periodo de inscripción |
| BR-03 / US-04 | Cupo mínimo 5, máximo 25 | `Cupo`, `CupoSpecification`, `Curso.iniciar` | `test_cupo_inmutable_y_maximo`, `test_cupo_cancelacion` | Implementado en demo |
| BR-04 / US-05 | Estado de pago | `Inscripcion.pagar`, endpoint `/pago` | `test_inscripcion_pago_y_academico`, API | Parcial: falta plazo de vencimiento |
| BR-05 / US-07 | Asistencia | `Inscripcion.asistencia`, endpoint `/asistencia` | `test_inscripcion_pago_academico_certificacion` | Parcial: sin correcciones autorizadas |
| BR-06 / US-08 | Calificaciones | `Nota`, `Inscripcion.evaluar`, endpoint `/calificacion` | `test_nota`, `test_nota_invalida`, API | Parcial: no se modelan evaluaciones independientes |
| US-10 / US-11 | Certificación | `CertificacionSpecification`, `CertificateMachine`, endpoint `/certificar` | `test_especificaciones`, `test_rechazo_certificacion`, API | Parcial: regla de asistencia configurable pendiente aprobación |
| US-12 / US-13 | Cancelación de curso | `CourseMachine`, `estado_curso('cancelar')`, audit SQL | `test_cupo_cancelacion` | Parcial: sin reembolso/reinscripción |
| RNF-03 | Auditoría | `AuditRow`, `UnitOfWork.audit` | Pruebas de API ejercitan las inserciones | Parcial: faltan usuario/autorizador e inmutabilidad formal |

El diagrama BPMN y los ADRs originales deben enlazarse en la matriz final al fusionar este código con el repositorio existente. La presente tabla **no prueba cumplimiento de las 19 historias**.
