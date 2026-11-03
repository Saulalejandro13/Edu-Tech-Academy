# Decisiones del complemento (no sustituyen ADR-001 a ADR-009)

1. Mantener DDD por capas y reglas dentro de entidades/Value Objects; API sin reglas de negocio.
2. Specification con condiciones componibles y comprobables por pruebas unitarias.
3. State Machines explícitas para Curso y Certificado; el modelo final debe revisar todas las máquinas y transiciones con el equipo.
4. SQLAlchemy con base relacional compatible con SQLite y PostgreSQL; cambios de un caso de uso en una transacción con UnitOfWork.
5. API FastAPI para Swagger/OpenAPI automático; sin dependencia en el dominio.
6. Defaults configurables de asistencia mínima y plazo de pago son referencias NO confirmadas, según ADR-008.

## Coherencia con documentos originales
La implementación es **parcial**, no reemplaza los 9 ADR ni el modelo completo de 19 historias de usuario y está preparada para revisión/integración con la solución del equipo.
