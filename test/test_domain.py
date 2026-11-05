import pytest
from edutech.domain.model import (
    Cupo, Nota, Politicas, Curso, Inscripcion, DomainError, CourseState,
    CertificateState, CourseMachine, CertificateMachine, CupoSpecification,
    PagoSpecification, AcademiaSpecification, CertificacionSpecification,
)


def test_cupo_inmutable_y_maximo():
    c = Cupo()
    assert c.ocupar().ocupados == 1
    assert c.ocupados == 0
    assert c.ocupar(25).disponibles == 0
    with pytest.raises(DomainError):
        c.ocupar(26)


@pytest.mark.parametrize('args', [(0,25,0), (5,4,0), (5,25,-1), (5,25,26)])
def test_cupo_invalido(args):
    with pytest.raises(DomainError):
        Cupo(*args)


@pytest.mark.parametrize('nota,aprueba', [(0,False),(69,False),(70,True),(100,True)])
def test_nota(nota,aprueba):
    assert Nota(nota).aprueba() == aprueba


@pytest.mark.parametrize('valor', [-1,101])
def test_nota_invalida(valor):
    with pytest.raises(DomainError):
        Nota(valor)


def test_politicas_invalidas():
    with pytest.raises(DomainError):
        Politicas(asistencia_minima=101)
    with pytest.raises(DomainError):
        Politicas(plazo_pago_dias=-1)


def test_maquina_cursos():
    assert CourseMachine.transition(CourseState.AVAILABLE, CourseState.ACTIVE) == CourseState.ACTIVE
    with pytest.raises(DomainError):
        CourseMachine.transition(CourseState.CANCELLED, CourseState.ACTIVE)


def test_maquina_certificados():
    assert CertificateMachine.transition(CertificateState.NOT_ELIGIBLE, CertificateState.ELIGIBLE) == CertificateState.ELIGIBLE
    with pytest.raises(DomainError):
        CertificateMachine.transition(CertificateState.NOT_ELIGIBLE, CertificateState.ISSUED)


def test_curso_inscribir_iniciar_concluir():
    c = Curso('C', 'Python', 100, 'I')
    with pytest.raises(DomainError):
        c.iniciar()
    c.inscribir(5)
    c.iniciar()
    c.concluir()
    assert c.estado == CourseState.FINISHED
    with pytest.raises(DomainError):
        c.inscribir()


def test_curso_lleno_cancelar():
    c = Curso('C','Python',100,'I')
    c.inscribir(25)
    assert c.estado == CourseState.FULL
    c.cancelar()
    assert c.estado == CourseState.CANCELLED
    with pytest.raises(DomainError):
        c.iniciar()


def test_especificaciones():
    c = Curso('C','Python',100,'I')
    assert CupoSpecification().is_satisfied_by(c)
    assert not CupoSpecification(26).is_satisfied_by(c)
    ins = Inscripcion('A','E','C')
    assert not PagoSpecification().is_satisfied_by(ins)
    assert not AcademiaSpecification(Politicas()).is_satisfied_by(ins,c)
    ins.pagar()
    ins.evaluar(85)
    for _ in range(10):
        ins.asistencia(True)
    c.inscribir(5)
    c.iniciar()
    c.concluir()
    assert CertificacionSpecification(Politicas()).is_satisfied_by(ins,c)
    ins.certificar(c, Politicas())
    assert ins.certificado == CertificateState.ISSUED
    with pytest.raises(DomainError):
        ins.certificar(c, Politicas())


def test_rechazo_certificacion():
    c = Curso('C','Python',100,'I')
    ins = Inscripcion('A','E','C')
    with pytest.raises(DomainError):
        ins.certificar(c, Politicas())


def test_inscripcion_pago_y_academico():
    ins = Inscripcion('A','E','C')
    assert ins.porcentaje_asistencia == 0
    ins.asistencia(True)
    ins.asistencia(False)
    assert ins.porcentaje_asistencia == 50
    ins.pagar()
    with pytest.raises(DomainError):
        ins.pagar()
    ins.evaluar(70)
    assert ins.calificacion == 70
    with pytest.raises(DomainError):
        ins.evaluar(110)
