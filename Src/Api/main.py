"""Documented REST API with FastAPI. /docs displays interactive Swagger UI."""
import os
from dataclasses import asdict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from edutech.application.services import EduTechService, NotFoundError
from edutech.domain.model import DomainError, Politicas
from edutech.infrastructure.db import UnitOfWork, make_session_factory


class NuevoCurso(BaseModel):
    id: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    precio: float = Field(ge=0)
    instructor_id: str = Field(min_length=1)


class NuevaInscripcion(BaseModel):
    estudiante_id: str = Field(min_length=1)
    curso_id: str = Field(min_length=1)


class NuevaAsistencia(BaseModel):
    presente: bool


class NuevaCalificacion(BaseModel):
    calificacion: float = Field(ge=0, le=100)


def create_app(database_url=None, politicas=None):
    database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///./edutech.db')
    session_factory = make_session_factory(database_url)
    service = EduTechService(lambda: UnitOfWork(session_factory), politicas or Politicas(
        asistencia_minima=float(os.getenv('ASISTENCIA_MINIMA', 80)),
        plazo_pago_dias=int(os.getenv('PLAZO_PAGO_DIAS', 7))))
    app = FastAPI(title='EduTech Academy API', version='1.0.0', description='PIA CLN: catálogo, inscripción, pagos, registros académicos y certificación.')

    @app.exception_handler(NotFoundError)
    async def not_found(_, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={'detail': str(exc)})

    @app.exception_handler(DomainError)
    async def domain_error(_, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=422, content={'detail': str(exc)})

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    @app.post('/cursos', status_code=201)
    def crear_curso(payload: NuevoCurso):
        return asdict(service.crear_curso(**payload.model_dump()))

    @app.get('/cursos')
    def cursos():
        return [asdict(curso) for curso in service.cursos()]

    @app.get('/cursos/{curso_id}')
    def curso(curso_id: str):
        return asdict(service.curso(curso_id))

    @app.post('/inscripciones', status_code=201)
    def inscribir(payload: NuevaInscripcion):
        return asdict(service.inscribir(**payload.model_dump()))

    @app.get('/inscripciones/{inscripcion_id}')
    def inscripcion(inscripcion_id: str):
        return asdict(service.inscripcion(inscripcion_id))

    @app.post('/inscripciones/{inscripcion_id}/pago')
    def pagar(inscripcion_id: str):
        return asdict(service.pagar(inscripcion_id))

    @app.post('/inscripciones/{inscripcion_id}/asistencia')
    def asistencia(inscripcion_id: str, payload: NuevaAsistencia):
        return asdict(service.asistencia(inscripcion_id, payload.presente))

    @app.post('/inscripciones/{inscripcion_id}/calificacion')
    def calificacion(inscripcion_id: str, payload: NuevaCalificacion):
        return asdict(service.evaluar(inscripcion_id, payload.calificacion))

    @app.post('/cursos/{curso_id}/iniciar')
    def iniciar(curso_id: str):
        return asdict(service.estado_curso(curso_id, 'iniciar'))

    @app.post('/cursos/{curso_id}/concluir')
    def concluir(curso_id: str):
        return asdict(service.estado_curso(curso_id, 'concluir'))

    @app.post('/cursos/{curso_id}/cancelar')
    def cancelar(curso_id: str):
        return asdict(service.estado_curso(curso_id, 'cancelar'))

    @app.post('/inscripciones/{inscripcion_id}/certificar')
    def certificar(inscripcion_id: str):
        return asdict(service.certificar(inscripcion_id))

    return app


app = create_app()
