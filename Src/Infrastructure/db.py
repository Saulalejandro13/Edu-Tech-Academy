"""SQLAlchemy relational persistence, works with PostgreSQL and SQLite."""
from dataclasses import asdict
from sqlalchemy import create_engine, Column, String, Float, Integer, JSON, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from edutech.domain.model import Curso, Inscripcion, Cupo, CourseState, EnrollmentState, PaymentState, CertificateState


class Base(DeclarativeBase):
    pass


class CourseRow(Base):
    __tablename__ = 'cursos'
    id = Column(String(100), primary_key=True)
    nombre = Column(String(200), nullable=False)
    precio = Column(Float, nullable=False)
    instructor_id = Column(String(100), nullable=False)
    estado = Column(String(40), nullable=False)
    cupo = Column(JSON, nullable=False)


class EnrollmentRow(Base):
    __tablename__ = 'inscripciones'
    id = Column(String(100), primary_key=True)
    estudiante_id = Column(String(100), nullable=False)
    curso_id = Column(String(100), ForeignKey('cursos.id'), nullable=False)
    estado = Column(String(40), nullable=False)
    pago = Column(String(40), nullable=False)
    asistidas = Column(Integer, nullable=False, default=0)
    sesiones = Column(Integer, nullable=False, default=0)
    calificacion = Column(Float, nullable=True)
    certificado = Column(String(40), nullable=False)


class AuditRow(Base):
    __tablename__ = 'bitacora'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entidad = Column(String(100), nullable=False)
    identificador = Column(String(100), nullable=False)
    accion = Column(String(100), nullable=False)
    detalle = Column(JSON, nullable=False)


def make_session_factory(url):
    engine = create_engine(url, future=True, connect_args={'check_same_thread': False} if url.startswith('sqlite') else {})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.cursos = CursoRepository(self.session)
        self.inscripciones = InscripcionRepository(self.session)
        return self

    def audit(self, entidad, identificador, accion, detalle=None):
        self.session.add(AuditRow(entidad=entidad, identificador=identificador, accion=accion, detalle=detalle or {}))

    def __exit__(self, error_type, error, traceback):
        try:
            self.session.commit() if error_type is None else self.session.rollback()
        finally:
            self.session.close()


class CursoRepository:
    def __init__(self, session):
        self.session = session

    def get(self, id):
        row = self.session.get(CourseRow, id)
        if not row:
            return None
        return Curso(row.id, row.nombre, row.precio, row.instructor_id, Cupo(**row.cupo), CourseState(row.estado))

    def list(self):
        return [self.get(row.id) for row in self.session.scalars(select(CourseRow)).all()]

    def save(self, curso):
        row = self.session.get(CourseRow, curso.id)
        if row is None:
            row = CourseRow(id=curso.id)
            self.session.add(row)
        row.nombre, row.precio, row.instructor_id = curso.nombre, curso.precio, curso.instructor_id
        row.estado, row.cupo = curso.estado.value, asdict(curso.cupo)


class InscripcionRepository:
    def __init__(self, session):
        self.session = session

    def get(self, id):
        row = self.session.get(EnrollmentRow, id)
        if not row:
            return None
        return Inscripcion(row.id, row.estudiante_id, row.curso_id, EnrollmentState(row.estado),
                           PaymentState(row.pago), row.asistidas, row.sesiones, row.calificacion,
                           CertificateState(row.certificado))

    def list_by_course(self, curso_id):
        ids = self.session.scalars(select(EnrollmentRow.id).where(EnrollmentRow.curso_id == curso_id)).all()
        return [self.get(id) for id in ids]

    def save(self, inscripcion):
        row = self.session.get(EnrollmentRow, inscripcion.id)
        if row is None:
            row = EnrollmentRow(id=inscripcion.id)
            self.session.add(row)
        row.estudiante_id, row.curso_id = inscripcion.estudiante_id, inscripcion.curso_id
        row.estado, row.pago = inscripcion.estado.value, inscripcion.pago.value
        row.asistidas, row.sesiones = inscripcion.asistidas, inscripcion.sesiones
        row.calificacion, row.certificado = inscripcion.calificacion, inscripcion.certificado.value
