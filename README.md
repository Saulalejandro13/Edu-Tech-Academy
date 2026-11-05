# EduTech Academy — complemento funcional del PIA CLN

**Estado:** módulo complementario autocontenido, NO fusionado ni desplegado en el repositorio original. Preparado a partir del BRD, las User Stories y la arquitectura de EduTech Academy aportados para el PIA.

## Alcance comprobado
- DDD: `Curso`, `Inscripcion`, `Cupo`, `Nota`, políticas, invariantes.
- Specification: `CupoSpecification`, `PagoSpecification`, `AcademiaSpecification`, `CertificacionSpecification`, composición con AND.
- State Machine: estados y transiciones de cursos y certificados.
- REST: catálogo, crear curso, inscribir, registrar pago/asistencia/calificación, iniciar/concluir/cancelar curso, emitir certificado.
- Persistencia: SQLAlchemy, SQLite para local/pruebas, PostgreSQL en Docker.
- Swagger/OpenAPI disponible en `/docs`, `/openapi.json`.
- Pruebas unitarias e integración vía pytest y TestClient; umbral de cobertura 80% exigido por configuración.
- GitHub Actions CI y Docker Compose (DB + App + Tests) preparados, no ejecutados en GitHub/Docker en este entorno.

## Instalación local (Python >= 3.11)
```bash
python -m venv .venv
# Activar el entorno virtual según tu sistema
pip install -r requirements-dev.txt -e .
uvicorn edutech.api.main:app --reload
```
Visitar `http://127.0.0.1:8000/docs`.
La base local usa `sqlite:///./edutech.db` si `DATABASE_URL` no está configurada.

## Pruebas
```bash
pytest -q
```
Configuración en `pyproject.toml` exige al menos 80% en este módulo. Pruebas sin dependencia de PostgreSQL usan bases SQLite temporales independientes.

## Docker
```bash
cp .env.example .env
# Reemplazar POSTGRES_PASSWORD antes de exponer servicios
# Asegurar que DATABASE_URL en .env coincida con el secreto

docker compose up --build db app
# Terminal adicional
docker compose run --rm tests
```
Servicio: `http://localhost:8000/docs`.
**Nota:** Docker no estuvo disponible en el entorno de generación, por lo que esta ejecución requiere validación externa.

## Demostración rápida
1. POST `/cursos` `{ "id":"PY-101", "nombre":"Python", "precio":1500, "instructor_id":"I1" }`.
2. POST `/inscripciones` para cinco estudiantes diferentes usando `{ "curso_id":"PY-101", "estudiante_id":"E1" }`, etc.
3. POST `/inscripciones/{id}/pago` y 10 registros en `/asistencia` para un estudiante.
4. POST `/inscripciones/{id}/calificacion` con 85.
5. POST `/cursos/PY-101/iniciar` y luego `/concluir`.
6. POST `/inscripciones/{id}/certificar`; confirmar `emitido`.
7. Intentar certificar otro estudiante sin pago: error de negocio 422.

## Parámetros no aprobados
`ASISTENCIA_MINIMA=80` y `PLAZO_PAGO_DIAS=7` son **valores de referencia**, explícitamente sujetos a validación en ADR-008. No presentarlos como reglas oficiales de EduTech Academy. Nota mínima aprobatoria 70 y cupo de 5 a 25 están documentados en el caso.

## Avisos importantes para la integración
**No sustituir a ciegas el repo `Saulalejandro13/Edu-Tech_Academy`.** El repositorio existente usa paquetes `src/edutech/dominio` y `src/edutech/aplicacion`, mientras que este complemento usa `src/edutech/domain`, `src/edutech/application`. Antes de integrar, comparar los módulos y migrar funcionalidades sin duplicarlas. Deben conservarse funciones de la solución original que no aparecen en este complemento, especialmente cliente empresarial, cambio de grupo, correcciones autorizadas, reembolso/reinscripción y autorizaciones por rol.

## Limitaciones conocidas — no se declaran cumplidas
- No integra las 19 User Stories ni todas las excepciones del BRD.
- No contiene autenticación ni autorización por roles (requiere implementación antes de producción).
- El registro de correcciones, casos de resolución y auditoría no está completo para las 19 historias.
- No se ejecutó Docker ni GitHub Actions ni un despliegue remoto.
- No se verificó el código final del repositorio GitHub original.
- No se preparó la defensa ni se generaron capturas reales de producción.

Ver `docs/AUDITORIA_Y_PENDIENTES.md` y `docs/TRAZABILIDAD.md`.
