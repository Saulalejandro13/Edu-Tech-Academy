import pytest
from fastapi.testclient import TestClient
from edutech.api.main import create_app
from edutech.domain.model import Politicas


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(f'sqlite:///{tmp_path / "test.db"}', Politicas(asistencia_minima=80)))


def create_course(client, name='C1'):
    return client.post('/cursos', json={'id': name, 'nombre': 'Python', 'precio': 1500, 'instructor_id': 'I1'})


def enroll(client, cid='C1', sid='E1'):
    return client.post('/inscripciones', json={'curso_id': cid, 'estudiante_id': sid})


def test_health_openapi(client):
    assert client.get('/health').json() == {'status': 'ok'}
    schema = client.get('/openapi.json').json()
    assert '/inscripciones/{inscripcion_id}/certificar' in schema['paths']
    assert client.get('/docs').status_code == 200


def test_catalogo_y_validaciones(client):
    assert client.get('/cursos').json() == []
    assert client.get('/cursos/missing').status_code == 404
    assert create_course(client).status_code == 201
    assert create_course(client).status_code == 422
    assert len(client.get('/cursos').json()) == 1
    assert client.get('/cursos/C1').json()['nombre'] == 'Python'
    assert client.post('/cursos',json={'id':'C2','nombre':'N','precio':-1,'instructor_id':'I'}).status_code == 422


def test_inscripcion_pago_academico_certificacion(client):
    create_course(client)
    assert enroll(client,'missing').status_code == 404
    assert enroll(client).status_code == 201
    insc = enroll(client, sid='E2').json()
    iid = insc['id']
    assert insc['pago'] == 'pendiente'
    assert client.get(f'/inscripciones/{iid}').status_code == 200
    assert client.post(f'/inscripciones/{iid}/certificar').status_code == 422
    assert client.post(f'/inscripciones/{iid}/pago').status_code == 200
    assert client.post(f'/inscripciones/{iid}/pago').status_code == 422
    for _ in range(8):
        assert client.post(f'/inscripciones/{iid}/asistencia',json={'presente':True}).status_code == 200
    for _ in range(2):
        client.post(f'/inscripciones/{iid}/asistencia',json={'presente':False})
    assert client.post(f'/inscripciones/{iid}/calificacion',json={'calificacion':85}).status_code == 200
    for n in range(3,6):
        assert enroll(client,sid=f'E{n}').status_code == 201
    assert client.post('/cursos/C1/iniciar').status_code == 200
    assert client.post('/cursos/C1/concluir').status_code == 200
    r = client.post(f'/inscripciones/{iid}/certificar')
    assert r.status_code == 200
    assert r.json()['certificado'] == 'emitido'
    assert client.post(f'/inscripciones/{iid}/certificar').status_code == 422


def test_cupo_cancelacion(client):
    create_course(client)
    for n in range(25):
        assert enroll(client,sid=str(n)).status_code == 201
    assert enroll(client,sid='extra').status_code == 422
    assert client.get('/cursos/C1').json()['estado'] == 'sin_cupo'
    assert client.post('/cursos/C1/cancelar').status_code == 200
    assert client.post('/cursos/C1/iniciar').status_code == 422
    assert client.get('/cursos/C1').json()['estado'] == 'cancelado'


def test_errores(client):
    assert client.get('/inscripciones/inexistente').status_code == 404
    assert client.post('/inscripciones/inexistente/pago').status_code == 404
    assert client.post('/inscripciones/inexistente/asistencia',json={'presente':True}).status_code == 404
    assert client.post('/inscripciones/inexistente/calificacion',json={'calificacion':50}).status_code == 404
    assert client.post('/inscripciones/inexistente/certificar').status_code == 404
    assert client.post('/cursos/inexistente/cancelar').status_code == 404
    create_course(client)
    assert client.post('/cursos/C1/iniciar').status_code == 422
    assert client.post('/inscripciones',json={'estudiante_id':'','curso_id':'C1'}).status_code == 422
