# Trazabilidad verificada de EduTech Academy v2

Esta matriz distingue implementación demostrable, implementación parcial y políticas por confirmar. Se originó en el BRD, las 19 historias/Gherkin, BPMN y arquitectura U3. Los archivos fuente están en `docs/fuentes/`.

| BRD / historia | Proceso BPMN | Código y endpoint | Prueba / estado |
|---|---|---|---|
| BR-01 / US-01 | Publicación/consulta cursos | Curso, CourseProfileRow; GET/POST `/cursos`, fechas/modalidad/requisitos | `test_courses_and_inscription_rules` / Implementado, calendarios opcionales |
| BR-02 / US-02 | Solicitud y validación inscripción | CupoSpecification; POST `/inscripciones`, cierre configurable | `test_courses_and_inscription_rules` / Implementado |
| BR-03 / US-04 | Validación de disponibilidad y cupo | Cupo, CourseMachine, grupos / endpoint `grupos` | `test_courses_and_inscription_rules`; mínimo 5 queda sujeto a revisión |
| BR-04 / US-05-06 | Pago / confirmar inscripción | Inscripcion.pagar, POST `/inscripciones/{id}/pago` | `test_instructor_evaluations_and_authorization` / Sin pasarela real |
| BR-05 / US-07 | Registrar asistencia | POST `/inscripciones/{id}/asistencia` | `test_instructor_evaluations_and_authorization` |
| BR-06 / US-08 | Aplicar evaluaciones | EvaluationRow, POST `/inscripciones/{id}/evaluaciones` | `test_instructor_evaluations_and_authorization` / agregación de nota final pendiente de definir |
| BR-07 / US-09 | Corrección autorizada | Control Escolar, auditoría; `corregir-calificacion` | `test_instructor_evaluations_and_authorization` |
| BR-08 / US-03 | Cliente proporciona lista; inscripción empresarial | Invitación/consentimiento; POST `/empresas/inscripciones` atómico | `test_company_invitation_and_atomic_enrollment` |
| US-10-11 | Validar criterios y emitir certificado | CertificacionSpecification/CertificateMachine, CertificateRow, POST `certificar` | `test_certificate_flow_and_audit` |
| US-12-13 | Cancelación y caso de resolución | CourseMachine; RequestRow para cada inscrito, `/solicitudes` | `test_course_minimum_cancel_and_resolution` / No reembolso monetario |
| US-14-15 | Solicitud/cambio de grupo | RequestRow, autorización Control Escolar, AssignmentRow | `test_group_change_workflow` |
| US-16 | Reinscripción tras reprobar | POST `/inscripciones/{id}/solicitudes` tipo `reinscripcion` | `test_group_change_workflow` rechazo si no reprobó; resolución monetaria pendiente |
| US-17 | Sustitución del instructor | `sustituir-instructor`; auditoría | Implementado con cuenta de instructor registrada |
| US-18 / RNF-03 | Bitácora de cambios | AuditRow y endpoint `/bitacora` | `test_certificate_flow_and_audit` |
| US-19 / RNF-01 | Permisos por rol | Auth PBKDF2, SessionRow, dependencies `access()` | `test_public_and_access_controls`, `test_registration_restrictions` |
| RNF-02 | Integridad | SQLAlchemy UnitOfWork; FK, transacciones; tests SQLite | `test_company_invitation_and_atomic_enrollment` / falta concurrencia PostgreSQL |
| PIA API / DDD | Arquitectura de U3 | OpenAPI `/docs`; domain/application/infrastructure/api | `test_public_and_access_controls`, `tests/test_domain.py` |

**Limitaciones:** no hay reglas oficiales de asistencia mínima, vencimiento automático, costo o mecanismo de reinscripción y reembolso. La UI representa estos pasos como solicitudes explícitas y deja registro, sin inferir políticas inexistentes.
