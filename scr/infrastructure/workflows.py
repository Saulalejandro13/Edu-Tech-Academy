"""Persistence of group allocation, business enrollments, requests, evaluation and resolution history."""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, select
from .db import Base

class GroupRow(Base):
    __tablename__ = 'grupos'
    id = Column(String(100), primary_key=True)
    curso_id = Column(String(100), ForeignKey('cursos.id'), nullable=False)
    nombre = Column(String(100), nullable=False)
    maximo = Column(Float, nullable=False, default=25)

class AssignmentRow(Base):
    __tablename__ = 'asignaciones_grupo'
    inscripcion_id = Column(String(100), ForeignKey('inscripciones.id'), primary_key=True)
    grupo_id = Column(String(100), ForeignKey('grupos.id'), nullable=False)
    empresa_id = Column(String(100), nullable=True)

class RequestRow(Base):
    __tablename__ = 'solicitudes'
    id = Column(String(100), primary_key=True)
    inscripcion_id = Column(String(100), ForeignKey('inscripciones.id'), nullable=False)
    tipo = Column(String(40), nullable=False)
    estado = Column(String(30), nullable=False, default='pendiente')
    destino = Column(String(100), nullable=True)
    motivo = Column(String(700), nullable=False)
    responsable = Column(String(100), nullable=True)
    observacion = Column(String(700), nullable=True)
    fecha = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class EvaluationRow(Base):
    __tablename__ = 'evaluaciones'
    id = Column(String(100), primary_key=True)
    inscripcion_id = Column(String(100), ForeignKey('inscripciones.id'), nullable=False)
    tipo = Column(String(40), nullable=False)
    fecha = Column(String(40), nullable=False)
    nota = Column(Float, nullable=False)
    instructor_id = Column(String(100), nullable=False)

class CertificateRow(Base):
    __tablename__ = 'certificados'
    id = Column(String(100), primary_key=True)
    inscripcion_id = Column(String(100), ForeignKey('inscripciones.id'), unique=True, nullable=False)
    emitido_en = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    emisor = Column(String(100), nullable=False)

def new_id():
    return uuid4().hex

def request_dict(r):
    return {'id':r.id, 'inscripcion_id':r.inscripcion_id, 'tipo':r.tipo, 'estado':r.estado,
            'destino':r.destino, 'motivo':r.motivo, 'responsable':r.responsable, 'observacion':r.observacion,
            'fecha':r.fecha.isoformat() if r.fecha else ''}

class CompanyInviteRow(Base):
    __tablename__ = 'invitaciones_empresa'
    id = Column(String(100), primary_key=True)
    empresa_id = Column(String(100), nullable=False)
    estudiante_id = Column(String(100), nullable=False)
    estado = Column(String(20), nullable=False, default='pendiente')

class CourseProfileRow(Base):
    __tablename__ = 'perfiles_curso'
    curso_id = Column(String(100), ForeignKey('cursos.id'), primary_key=True)
    modalidad = Column(String(30), nullable=False, default='por_definir')
    fecha_inicio = Column(String(10), nullable=True)
    fecha_fin = Column(String(10), nullable=True)
    cierre_inscripcion = Column(String(10), nullable=True)
    requisitos = Column(String(700), nullable=True)
