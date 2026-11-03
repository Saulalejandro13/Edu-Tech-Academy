# Auditoría y pendientes — EduTech Academy

## Fuente
Rúbrica PIA CLN AD2026 (6 de noviembre de 2026), BRD Equipo 15, 19 User Stories con Gherkin, BPMN EduTech, glosario y actividad Unidad 3 EduTech. Los archivos BBVA fueron excluidos.

## Estado de este complemento
| Requisito | Estado verificable | Evidencia |
|---|---|---|
| BRD, 19 US/Gherkin, BPMN, glosario | Disponibles en los documentos del equipo; no modificados | Adjuntos originales |
| DDD, patrones, SOLID, ADRs, UML | Documentados en Unidad 3; modelo parcial implementado en el complemento | `src/edutech/domain/model.py` |
| Specification | Implementado y probado, alcance parcial | `domain/model.py`, `tests/test_domain.py` |
| State Machine | Implementado y probado para curso/certificación | `domain/model.py`, `tests/test_domain.py` |
| API REST + Swagger | Funcional localmente | `api/main.py`, `tests/test_api.py`, `docs/api/openapi.json` |
| Base de datos | SQLAlchemy SQLite probada; PostgreSQL configurado, no ejecutado | `infrastructure/db.py` |
| Pruebas ≥80% | 24 pruebas locales pasan; 98.77% del código del complemento | `tests/`, registro de prueba |
| Docker DB + App + Tests | Archivos preparados; no ejecutado por ausencia de Docker | `Dockerfile`, `docker-compose.yml` |
| GitHub Actions | Workflow preparado; no habilitado ni ejecutado en repositorio remoto | `.github/workflows/ci.yml` |
| Variables de entorno | Plantilla creada | `.env.example` |
| Reporte final y defensa | Pendientes | Documentos originales disponibles, falta consolidación |
| Despliegue público | Pendiente; URL no disponible | No verificado |

## Pendientes de alta prioridad antes de entregar
1. Fusionar con el código real del repositorio después de clonarlo; no borrar ninguna funcionalidad existente.
2. Implementar/autenticar roles y permisos. La presente API es DEMO y no puede publicarse abiertamente tal como está.
3. Completar inscripción empresarial (US-03), cambios de grupo (US-14/15), modificación autorizada de calificaciones (US-09), cancelación y resolución/reembolso (US-12/13), reinscripción y sustitución de instructor, y el resto de historias que exija el BRD.
4. Revisar estados y transiciones con el modelo final y cubrir pagos, solicitud de cambios y otros procesos exigidos.
5. Ejecutar `docker compose up --build` y `docker compose run --rm tests`, resolver problemas y guardar evidencias.
6. Crear workflow en repositorio remoto y comprobar corrida verde real.
7. Desplegar en servicio autorizado, proteger credenciales, configurar base de datos y demostrar Swagger en producción.
8. Integrar documentación, diagramas y ADRs del equipo sin alterarlos indebidamente; ampliar matriz con código y pruebas del repositorio fusionado.
9. Preparar PDF final, presentación y defensa con evidencias auténticas.

## Riesgos de consistencia
- En el BRD hay políticas pendientes de confirmación (asistencia mínima, plazo de pago, etc.). Los defaults usados en este complemento NO son reglas aprobadas.
- Se requiere verificar que `iniciar curso` con mínimo de 5 y `sin cupo` con máximo de 25 respondan correctamente al negocio. El flujo de cancelación necesita decisiones de devolución no automatizadas en este demo.
- Los registros SQL de auditoría guardan eventos, pero carecen de usuario autenticado/autorizador y no prueban inmutabilidad ante administradores de DB.
