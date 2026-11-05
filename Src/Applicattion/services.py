"""Application services coordinate use cases; invariants stay in the domain."""
from edutech.domain.model import (Curso, Inscripcion, Politicas, DomainError, CourseState,
                                  EnrollmentState, CupoSpecification, nuevo_id)


class NotFoundError(DomainError):
    pass


class EduTechService:
    def __init__(self, uow_factory, politicas=None):
        self.uow_factory = uow_factory
        self.politicas = politicas or Politicas()

    def crear_curso(self, id, nombre, precio, instructor_id):
        if not id or not nombre or precio < 0 or not instructor_id:
            raise DomainError('Datos del curso inválidos')
        with self.uow_factory() as uow:
            if uow.cursos.get(id):
                raise DomainError('Curso ya existe')
            curso = Curso(id, nombre, precio, instructor_id)
            uow.cursos.save(curso)
            uow.audit('Curso', id, 'Creado')
            return curso

    def cursos(self):
        with self.uow_factory() as uow:
            return uow.cursos.list()

    def curso(self, id):
        with self.uow_factory() as uow:
            curso = uow.cursos.get(id)
            if not curso:
                raise NotFoundError('Curso no encontrado')
            return curso

    def inscribir(self, estudiante_id, curso_id):
        if not estudiante_id:
            raise DomainError('Estudiante requerido')
        with self.uow_factory() as uow:
            curso = uow.cursos.get(curso_id)
            if not curso:
                raise NotFoundError('Curso no encontrado')
            if not CupoSpecification().is_satisfied_by(curso):
                raise DomainError('Curso sin cupo o no disponible')
            curso.inscribir()
            inscripcion = Inscripcion(nuevo_id(), estudiante_id, curso_id)
            uow.cursos.save(curso)
            uow.inscripciones.save(inscripcion)
            uow.audit('Inscripcion', inscripcion.id, 'InscripcionRealizada', {'curso_id': curso_id})
            return inscripcion

    def inscripcion(self, id):
        with self.uow_factory() as uow:
            insc = uow.inscripciones.get(id)
            if not insc:
                raise NotFoundError('Inscripción no encontrada')
            return insc

    def pagar(self, id):
        with self.uow_factory() as uow:
            insc = self._get_insc(uow, id)
            insc.pagar()
            uow.inscripciones.save(insc)
            uow.audit('Inscripcion', id, 'PagoRegistrado')
            return insc

    def asistencia(self, id, presente):
        with self.uow_factory() as uow:
            insc = self._get_insc(uow, id)
            insc.asistencia(presente)
            uow.inscripciones.save(insc)
            uow.audit('Inscripcion', id, 'AsistenciaRegistrada', {'presente': presente})
            return insc

    def evaluar(self, id, calificacion):
        with self.uow_factory() as uow:
            insc = self._get_insc(uow, id)
            insc.evaluar(calificacion)
            uow.inscripciones.save(insc)
            uow.audit('Inscripcion', id, 'CalificacionRegistrada')
            return insc

    def estado_curso(self, id, accion):
        with self.uow_factory() as uow:
            curso = uow.cursos.get(id)
            if not curso:
                raise NotFoundError('Curso no encontrado')
            {'iniciar': curso.iniciar, 'concluir': curso.concluir, 'cancelar': curso.cancelar}[accion]()
            uow.cursos.save(curso)
            if accion == 'cancelar':
                for insc in uow.inscripciones.list_by_course(id):
                    insc.estado = EnrollmentState.CANCELLED
                    uow.inscripciones.save(insc)
                    uow.audit('Inscripcion', insc.id, 'CasoResolucionPendiente', {'motivo': 'Curso cancelado'})
            uow.audit('Curso', id, accion)
            return curso

    def certificar(self, id):
        with self.uow_factory() as uow:
            insc = self._get_insc(uow, id)
            curso = uow.cursos.get(insc.curso_id)
            insc.certificar(curso, self.politicas)
            uow.inscripciones.save(insc)
            uow.audit('Inscripcion', id, 'CertificadoEmitido')
            return insc

    @staticmethod
    def _get_insc(uow, id):
        insc = uow.inscripciones.get(id)
        if not insc:
            raise NotFoundError('Inscripción no encontrada')
        return insc
