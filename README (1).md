# EduTech Academy — Sistema de inscripción, evaluación y certificación

Proyecto Integrador de Aprendizaje (PIA) de **Componentes de Lógica de Negocios**, FIME – UANL. Equipo 15.

| Integrante | Matrícula |
|---|---|
| Carlos Hugo García Gómez | 2226690 |
| Alan Bertín Castillo Martínez | 2226653 |
| Saúl Alejandro Hernández Garza | 2226664 |

## Enlaces

| Recurso | URL |
|---|---|
| Repositorio | https://github.com/Saulalejandro13/Edu-Tech-Academy |
| Sistema desplegado (Render) | https://edu-tech-academy.onrender.com/ |
| Swagger UI | https://edu-tech-academy.onrender.com/docs |
| Especificación OpenAPI | https://edu-tech-academy.onrender.com/openapi.json |

> Nota: en el plan gratuito de Render el servicio puede tardar cerca de un minuto en responder la primera vez.

## Descripción

EduTech Academy digitaliza el ciclo del estudiante: consulta de cursos, inscripción individual o empresarial, pago, asistencia, evaluación, certificación, cambios de grupo, cancelaciones, reinscripción y sustitución de instructor, con trazabilidad de cambios y permisos por rol. Los pagos y reembolsos son una **simulación académica**.

## Arquitectura

Domain-Driven Design en cuatro capas dentro de `src/edutech/`:

| Capa | Ruta | Responsabilidad |
|---|---|---|
| API | `src/edutech/api/` | Endpoints REST (FastAPI) y OpenAPI |
| Aplicación | `src/edutech/application/` | Casos de uso (Service Layer) y permisos por rol |
| Dominio | `src/edutech/domain/` | Entidades, Value Objects, Specification y State Machine |
| Infraestructura | `src/edutech/infrastructure/` | Repositorios, Unit of Work, SQLAlchemy, usuarios y sesiones |

Componentes del curso: DDD, Specification (cupo y certificación), State Machine (`CourseMachine`, `CertificateMachine`), Repository + Unit of Work y API REST documentada.

## Estructura del repositorio

```
├── docs/
│   ├── BRD.md
│   ├── architecture/        # ADR-001 a ADR-009, diagramas DDD/UML
│   └── api/                 # openapi.json
├── src/edutech/             # domain, application, infrastructure, api
├── tests/                   # unitarias + integración
├── .github/workflows/       # CI
├── Dockerfile
├── docker-compose.yml       # DB + App + Tests
├── .env.example             # variables sin secretos
└── README.md
```

## Requisitos

- Python 3.12
- Docker y Docker Compose (para el entorno reproducible)

## Configuración

Copia el archivo de ejemplo y ajusta los valores:

```bash
cp .env.example .env
```

`.env` no se versiona. `.env.example` no contiene secretos reales. La configuración se separa del código mediante variables de entorno (12-Factor App).

## Ejecución con Docker Compose (recomendada)

```bash
docker compose up --build
```

Levanta la base de datos (PostgreSQL) y la aplicación en http://localhost:8000. Swagger en http://localhost:8000/docs.

Para ejecutar solo las pruebas en contenedor:

```bash
docker compose run --rm tests
```


## Ejecución local sin Docker

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn edutech.api.main:app --reload --app-dir src
```

## Pruebas y cobertura

```bash
pytest --cov=src/edutech --cov-report=term-missing
```

Resultado de referencia (ejecución en contenedor, Python 3.12): **29 pruebas aprobadas, cobertura total 90.93 %** (mínimo exigido: 80 %).

| Módulo | Cobertura |
|---|---|
| `domain/model.py` | 98 % |
| `infrastructure/db.py` | 99 % |
| `infrastructure/workflows.py` | 100 % |
| `api/main.py` | 93 % |
| `infrastructure/identity.py` | 87 % |
| `application/services.py` | 69 % |

## CI/CD

El flujo `.github/workflows/ci.yml` ejecuta las pruebas con cobertura en cada push y pull request. Estado: ver la pestaña **Actions** del repositorio.

## Despliegue

Desplegado como Web Service en **Render**, con la base de datos y las variables de entorno configuradas en la plataforma. Swagger UI y OpenAPI están activos en producción para la demostración.

## Roles y demostración

Perfiles: 
Estudiante
puede crear su popria cuenta un ejemplo 
Saul@gmail.com
Instructor

Control Escolar, Administración y Cliente empresarial (permisos según el BRD, sección 11).

Guion de demostración:

1. Inicio de sesión con distintos roles y verificación de permisos.
2. Catálogo de cursos y control de cupo (mínimo 5, máximo 25).
3. Inscripción individual, pago simulado e inscripción empresarial.
4. Asistencia, calificación (aprobatoria 70) y corrección autorizada con bitácora.
5. Validación y emisión de certificado.
6. Cancelación de curso y cambio de estado.
7. Swagger UI y trazabilidad BRD → historias → dominio → código → pruebas.

## Trazabilidad

Los requerimientos del BRD (BR-01 a BR-09, EX-01 a EX-04, RNF-01 a RNF-05), las 19 historias de usuario con Gherkin, el BPMN y el glosario están en `docs/` y en el reporte final. La matriz de trazabilidad relaciona cada historia con su endpoint, componente de dominio y pruebas.

## Limitaciones conocidas

- Reglas pendientes de confirmar por EduTech (asistencia mínima, fecha límite de inscripción, plazo de pago, costo de reinscripción, límite de cambios de grupo): se manejan como valores configurables (ADR-008).
- Pagos y reembolsos simulados; sin integración con facturación.
- Algunos aggregates del diseño (RegistroAcademico, Certificado, SolicitudCambioGrupo, CancelacionCurso) están implementados de forma simplificada.
- La cobertura de `application/services.py` (69 %) es el área de refuerzo.

- ## API pública

Aplicación:
https://edu-tech-academy.onrender.com/

Swagger:
https://edu-tech-academy.onrender.com/docs

OpenAPI:
https://edu-tech-academy.onrender.com/openapi.json

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



