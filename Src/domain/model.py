"""Domain model of EduTech Academy. No framework or database dependencies."""
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from uuid import uuid4


class DomainError(ValueError):
    pass


class CourseState(StrEnum):
    AVAILABLE = 'disponible'
    FULL = 'sin_cupo'
    ACTIVE = 'en_curso'
    FINISHED = 'concluido'
    CANCELLED = 'cancelado'


class EnrollmentState(StrEnum):
    ENROLLED = 'inscrito'
    CANCELLED = 'cancelado'


class PaymentState(StrEnum):
    PENDING = 'pendiente'
    PAID = 'pagado'


class CertificateState(StrEnum):
    NOT_ELIGIBLE = 'no_apto'
    ELIGIBLE = 'apto'
    ISSUED = 'emitido'


@dataclass(frozen=True)
class Cupo:
    minimo: int = 5
    maximo: int = 25
    ocupados: int = 0

    def __post_init__(self):
        if self.minimo < 1 or self.maximo < self.minimo or not 0 <= self.ocupados <= self.maximo:
            raise DomainError('Cupo inválido')

    @property
    def disponibles(self):
        return self.maximo - self.ocupados

    def ocupar(self, cantidad=1):
        if cantidad < 1 or cantidad > self.disponibles:
            raise DomainError('Sin cupo suficiente')
        return Cupo(self.minimo, self.maximo, self.ocupados + cantidad)


@dataclass(frozen=True)
class Nota:
    valor: float

    def __post_init__(self):
        if not 0 <= self.valor <= 100:
            raise DomainError('Calificación fuera de rango')

    def aprueba(self):
        return self.valor >= 70


@dataclass(frozen=True)
class Politicas:
    """Illustrative parameters, NOT approved EduTech business rules."""
    asistencia_minima: float = 80.0
    plazo_pago_dias: int = 7

    def __post_init__(self):
        if not 0 <= self.asistencia_minima <= 100 or self.plazo_pago_dias < 0:
            raise DomainError('Parámetros inválidos')


class CourseMachine:
    TRANSITIONS = {
        CourseState.AVAILABLE: {CourseState.FULL, CourseState.ACTIVE, CourseState.CANCELLED},
        CourseState.FULL: {CourseState.ACTIVE, CourseState.CANCELLED},
        CourseState.ACTIVE: {CourseState.FINISHED, CourseState.CANCELLED},
        CourseState.FINISHED: set(),
        CourseState.CANCELLED: set(),
    }

    @classmethod
    def transition(cls, current: CourseState, to: CourseState) -> CourseState:
        if to not in cls.TRANSITIONS[current]:
            raise DomainError(f'Transición de curso inválida: {current} -> {to}')
        return to


class CertificateMachine:
    TRANSITIONS = {
        CertificateState.NOT_ELIGIBLE: {CertificateState.ELIGIBLE},
        CertificateState.ELIGIBLE: {CertificateState.ISSUED, CertificateState.NOT_ELIGIBLE},
        CertificateState.ISSUED: set(),
    }

    @classmethod
    def transition(cls, current: CertificateState, to: CertificateState) -> CertificateState:
        if to not in cls.TRANSITIONS[current]:
            raise DomainError('Transición de certificado inválida')
        return to


@dataclass
class Curso:
    id: str
    nombre: str
    precio: float
    instructor_id: str
    cupo: Cupo = field(default_factory=Cupo)
    estado: CourseState = CourseState.AVAILABLE

    def inscribir(self, cantidad=1):
        if self.estado not in {CourseState.AVAILABLE, CourseState.FULL}:
            raise DomainError('Curso no disponible para inscripción')
        self.cupo = self.cupo.ocupar(cantidad)
        if self.cupo.disponibles == 0 and self.estado == CourseState.AVAILABLE:
            self.estado = CourseMachine.transition(self.estado, CourseState.FULL)

    def iniciar(self):
        if self.cupo.ocupados < self.cupo.minimo:
            raise DomainError('El curso no alcanza el cupo mínimo; requiere revisión administrativa')
        self.estado = CourseMachine.transition(self.estado, CourseState.ACTIVE)

    def concluir(self):
        self.estado = CourseMachine.transition(self.estado, CourseState.FINISHED)

    def cancelar(self):
        self.estado = CourseMachine.transition(self.estado, CourseState.CANCELLED)


@dataclass
class Inscripcion:
    id: str
    estudiante_id: str
    curso_id: str
    estado: EnrollmentState = EnrollmentState.ENROLLED
    pago: PaymentState = PaymentState.PENDING
    asistidas: int = 0
    sesiones: int = 0
    calificacion: float | None = None
    certificado: CertificateState = CertificateState.NOT_ELIGIBLE

    def pagar(self):
        if self.estado != EnrollmentState.ENROLLED:
            raise DomainError('Inscripción no activa')
        if self.pago == PaymentState.PAID:
            raise DomainError('Pago duplicado')
        self.pago = PaymentState.PAID

    def asistencia(self, presente: bool):
        if self.estado != EnrollmentState.ENROLLED:
            raise DomainError('Inscripción no activa')
        self.sesiones += 1
        self.asistidas += int(presente)

    def evaluar(self, nota: float):
        self.calificacion = Nota(nota).valor

    @property
    def porcentaje_asistencia(self):
        return self.asistidas / self.sesiones * 100 if self.sesiones else 0

    def certificar(self, curso: Curso, politica: Politicas):
        spec = CertificacionSpecification(politica)
        if not spec.is_satisfied_by(self, curso):
            raise DomainError('No cumple los requisitos de certificación')
        if self.certificado == CertificateState.NOT_ELIGIBLE:
            self.certificado = CertificateMachine.transition(self.certificado, CertificateState.ELIGIBLE)
        self.certificado = CertificateMachine.transition(self.certificado, CertificateState.ISSUED)


class Specification:
    def is_satisfied_by(self, obj, context=None):
        raise NotImplementedError

    def __and__(self, other):
        return AndSpecification(self, other)


class AndSpecification(Specification):
    def __init__(self, left, right):
        self.left, self.right = left, right

    def is_satisfied_by(self, obj, context=None):
        return self.left.is_satisfied_by(obj, context) and self.right.is_satisfied_by(obj, context)


class CupoSpecification(Specification):
    def __init__(self, cantidad=1):
        self.cantidad = cantidad

    def is_satisfied_by(self, curso, context=None):
        return curso.estado == CourseState.AVAILABLE and curso.cupo.disponibles >= self.cantidad


class PagoSpecification(Specification):
    def is_satisfied_by(self, inscripcion, context=None):
        return inscripcion.pago == PaymentState.PAID


class AcademiaSpecification(Specification):
    def __init__(self, politicas):
        self.politicas = politicas

    def is_satisfied_by(self, inscripcion, curso=None):
        return (inscripcion.calificacion is not None and Nota(inscripcion.calificacion).aprueba()
                and inscripcion.porcentaje_asistencia >= self.politicas.asistencia_minima)


class CertificacionSpecification(Specification):
    def __init__(self, politicas):
        self.politicas = politicas

    def is_satisfied_by(self, inscripcion, curso):
        return (curso.estado == CourseState.FINISHED
                and inscripcion.estado == EnrollmentState.ENROLLED
                and (PagoSpecification() & AcademiaSpecification(self.politicas)).is_satisfied_by(inscripcion, curso))


def nuevo_id():
    return uuid4().hex
