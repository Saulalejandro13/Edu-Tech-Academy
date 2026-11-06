import os
import pytest
from fastapi.testclient import TestClient
from edutech.api.main import create_app

@pytest.fixture(scope='module')
def env(tmp_path_factory):
    path=tmp_path_factory.mktemp('integration')/'edu.sqlite3'
    old=os.environ.get('DEMO_SEED');os.environ['DEMO_SEED']='1'
    try:client=TestClient(create_app(f'sqlite:///{path}'))
    finally:
        if old is None:os.environ.pop('DEMO_SEED',None)
        else:os.environ['DEMO_SEED']=old
    def login(email='alumno@edutech.test',password='DemoSegura2026!'):
        r=client.post('/auth/login',json={'email':email,'password':password})
        assert r.status_code==200,r.text
        return {'Authorization':'Bearer '+r.json()['token']}
    return client, {role:login(email) for role,email in [
        ('estudiante','alumno@edutech.test'),('empresa','empresa@edutech.test'),
        ('instructor','instructor@edutech.test'),('administracion','admin@edutech.test'),
        ('control_escolar','escolar@edutech.test')]}

def test_public_and_access_controls(env):
    c,h=env
    assert c.get('/health').json()=={'status':'ok'}
    assert c.get('/docs').status_code==200
    assert '/auth/login' in c.get('/openapi.json').json()['paths']
    assert c.get('/auth/me').status_code==401
    assert c.get('/auth/me',headers=h['empresa']).json()['rol']=='empresa'
    assert c.post('/cursos',json={'id':'NO','nombre':'N','precio':3,'instructor_id':'INST-DEMO'}).status_code==401
    assert c.post('/cursos',json={'id':'NO','nombre':'N','precio':3,'instructor_id':'INST-DEMO'},headers=h['estudiante']).status_code==403
    assert c.get('/usuarios',headers=h['instructor']).status_code==403
    assert c.get('/bitacora',headers=h['administracion']).status_code==200
    assert c.get('/bitacora',headers=h['estudiante']).status_code==403
    assert c.get('/static/app.js').status_code==200

def test_registration_restrictions(env):
    c,h=env
    data={'nombre':'Estudiante Nuevo','email':'nuevo@example.test','password':'nuevaClaveSegura123','rol':'estudiante'}
    assert c.post('/auth/registro',json=data).status_code==201
    assert c.post('/auth/registro',json=data).status_code==409
    assert c.post('/auth/registro',json={**data,'email':'otro@example.test','rol':'administracion'}).status_code==403
    assert c.post('/auth/login',json={'email':data['email'],'password':'malaclave'}).status_code==401
    admin=c.post('/usuarios',headers=h['administracion'],json={'nombre':'Nuevo Instructor','email':'inst2@example.test','password':'SeguraYDistinta123','rol':'instructor'})
    assert admin.status_code==201
    assert admin.json()['rol']=='instructor'
    assert c.post('/usuarios',headers=h['administracion'],json={'nombre':'X','email':'x@example.test','password':'clave123456','rol':'otro'}).status_code==422
    assert c.get('/auth/me',headers=h['administracion']).status_code==200

def test_courses_and_inscription_rules(env):
    c,h=env
    assert len(c.get('/cursos').json())>=3
    assert c.get('/cursos/not-found').status_code==404
    assert c.get('/cursos/PY-101/grupos').status_code==200
    r=c.post('/cursos',headers=h['administracion'],json={'id':'WEB-QA','nombre':'Curso QA','precio':100,'instructor_id':'INST-DEMO','modalidad':'en_linea','fecha_inicio':'2026-10-01','fecha_fin':'2026-12-01'})
    assert r.status_code==201,r.text
    assert r.json()['modalidad']=='en_linea'
    assert c.post('/cursos',headers=h['administracion'],json={'id':'WEB-QA','nombre':'Duplicado','precio':2,'instructor_id':'INST-DEMO'}).status_code==422
    assert c.post('/cursos',headers=h['administracion'],json={'id':'MAL','nombre':'Mal','precio':2,'instructor_id':'INST-DEMO','fecha_inicio':'2026-12-01','fecha_fin':'2026-01-01'}).status_code==422
    assert c.post('/cursos/PY-101/grupos',headers=h['administracion'],json={'nombre':'Turno tarde','maximo':25}).status_code==201
    groups=c.get('/cursos/PY-101/grupos').json()
    assert len(groups)>=2
    assert c.post('/inscripciones',headers=h['empresa'],json={'curso_id':'PY-101'}).status_code==403
    assert c.post('/inscripciones',headers=h['estudiante'],json={'curso_id':'NO'}).status_code==404
    r=c.post('/inscripciones',headers=h['estudiante'],json={'curso_id':'PY-101','estudiante_id':'EST-FAKE'})
    assert r.status_code==201,r.text
    assert r.json()['estudiante_id']=='EST-DEMO'
    assert c.post('/inscripciones',headers=h['estudiante'],json={'curso_id':'PY-101'}).status_code==422
    assert c.get('/mis-inscripciones',headers=h['estudiante']).json()[0]['curso_id']=='PY-101'

def test_company_invitation_and_atomic_enrollment(env):
    c,h=env
    eid='EST-DEMO'
    denied=c.post('/empresas/inscripciones',headers=h['empresa'],json={'curso_id':'SQL-201','empleados':[eid]})
    assert denied.status_code==403
    inv=c.post('/empresas/invitaciones/'+eid,headers=h['empresa']).json()
    assert inv['estado']=='pendiente'
    assert c.post('/empresas/invitaciones/'+eid,headers=h['empresa']).status_code==201
    assert c.post(f"/empresas/invitaciones/{inv['id']}/responder?decision=aceptada",headers=h['empresa']).status_code==403
    assert c.post(f"/empresas/invitaciones/{inv['id']}/responder?decision=aceptada",headers=h['estudiante']).status_code==200
    assert c.post(f"/empresas/invitaciones/{inv['id']}/responder?decision=aceptada",headers=h['estudiante']).status_code==422
    assert c.post('/empresas/inscripciones',headers=h['empresa'],json={'curso_id':'SQL-201','empleados':['NO-EST']}).status_code==422
    r=c.post('/empresas/inscripciones',headers=h['empresa'],json={'curso_id':'SQL-201','empleados':[eid]})
    assert r.status_code==201,r.text
    assert len(c.get('/mis-inscripciones',headers=h['empresa']).json())==1
    assert c.post('/empresas/inscripciones',headers=h['empresa'],json={'curso_id':'SQL-201','empleados':[eid,eid]}).status_code==422

def test_instructor_evaluations_and_authorization(env):
    c,h=env
    eid=c.get('/mis-inscripciones',headers=h['estudiante']).json()[0]['id']
    assert c.get('/inscripciones/'+eid,headers=h['empresa']).status_code==403
    assert c.post('/inscripciones/'+eid+'/asistencia',headers=h['control_escolar'],json={'presente':True}).status_code==403
    assert c.post('/inscripciones/'+eid+'/asistencia',headers=h['instructor'],json={'presente':True}).status_code==200
    assert c.post('/inscripciones/'+eid+'/evaluaciones',headers=h['instructor'],json={'tipo':'inventado','fecha':'2026-11-05','calificacion':85}).status_code==422
    r=c.post('/inscripciones/'+eid+'/evaluaciones',headers=h['instructor'],json={'tipo':'final','fecha':'2026-11-05','calificacion':85})
    assert r.status_code==201,r.text
    assert len(c.get('/inscripciones/'+eid+'/evaluaciones',headers=h['estudiante']).json())==1
    assert c.post('/inscripciones/'+eid+'/corregir-calificacion',headers=h['instructor'],json={'calificacion':90,'motivo':'Se corrigió captura'}).status_code==403
    assert c.post('/inscripciones/'+eid+'/corregir-calificacion',headers=h['control_escolar'],json={'calificacion':90,'motivo':'Se corrigió captura'}).status_code==200
    assert c.post('/inscripciones/'+eid+'/certificar',headers=h['control_escolar']).status_code==422
    assert c.post('/inscripciones/'+eid+'/pago',headers=h['estudiante']).status_code==200
    assert c.post('/inscripciones/'+eid+'/pago',headers=h['estudiante']).status_code==422

def test_group_change_workflow(env):
    c,h=env
    e=c.get('/mis-inscripciones',headers=h['estudiante']).json()[0]
    group_current=e['grupo_id']
    groups=c.get('/cursos/PY-101/grupos').json()
    dest=next(g['id'] for g in groups if g['id']!=group_current)
    r=c.post('/inscripciones/'+e['id']+'/solicitudes',headers=h['estudiante'],json={'tipo':'cambio_grupo','destino':dest,'motivo':'Cambiar al turno vespertino'})
    assert r.status_code==201,r.text
    rid=r.json()['id']
    assert c.post('/solicitudes/'+rid+'/resolver',headers=h['administracion'],json={'decision':'autorizada','observacion':'Aceptado por el director'}).status_code==403
    assert c.post('/solicitudes/'+rid+'/resolver',headers=h['control_escolar'],json={'decision':'autorizada','observacion':'Cambio autorizado'}).status_code==200
    assert c.get('/mis-inscripciones',headers=h['estudiante']).json()[0]['grupo_id']==dest
    assert c.post('/solicitudes/'+rid+'/resolver',headers=h['control_escolar'],json={'decision':'rechazada','observacion':'duplicado'}).status_code==422
    assert c.post('/inscripciones/'+e['id']+'/solicitudes',headers=h['estudiante'],json={'tipo':'reinscripcion','motivo':'Curso reprobado'}).status_code==422

def test_course_minimum_cancel_and_resolution(env):
    c,h=env
    assert c.post('/cursos/BI-301/iniciar',headers=h['administracion']).status_code==422
    assert c.post('/cursos/BI-301/cancelar',headers=h['administracion']).status_code==200
    assert c.post('/cursos/BI-301/iniciar',headers=h['administracion']).status_code==422
    assert c.post('/inscripciones',headers=h['estudiante'],json={'curso_id':'BI-301'}).status_code==422
    assert c.get('/solicitudes',headers=h['administracion']).status_code==200

def test_certificate_flow_and_audit(env):
    c,h=env
    users=c.get('/usuarios',headers=h['administracion']).json()
    # create 4 students to satisfy course minimum with existing EST-DEMO enrollment
    ids=[]
    for idx in range(4):
        user=c.post('/auth/registro',json={'nombre':'Alumno '+str(idx),'email':f'cert{idx}@example.test','password':'ContrasenaValida123','rol':'estudiante'}).json()
        token=c.post('/auth/login',json={'email':user['email'],'password':'ContrasenaValida123'}).json()['token']
        ids.append((user,{'Authorization':'Bearer '+token}))
        assert c.post('/inscripciones',headers=ids[-1][1],json={'curso_id':'PY-101'}).status_code==201
    assert c.post('/cursos/PY-101/iniciar',headers=h['administracion']).status_code==200
    assert c.post('/cursos/PY-101/concluir',headers=h['administracion']).status_code==200
    e=c.get('/mis-inscripciones',headers=h['estudiante']).json()[0]
    for _ in range(4):c.post('/inscripciones/'+e['id']+'/asistencia',headers=h['instructor'],json={'presente':True})
    assert c.post('/inscripciones/'+e['id']+'/certificar',headers=h['control_escolar']).status_code==200
    assert c.post('/inscripciones/'+e['id']+'/certificar',headers=h['control_escolar']).status_code==422
    assert len(c.get('/mis-certificados',headers=h['estudiante']).json())==1
    assert c.get('/mis-certificados',headers=h['empresa']).json()==[]
    audit=c.get('/bitacora',headers=h['administracion']).json()
    assert any(x['accion']=='CertificadoGenerado' for x in audit)
    assert any(x['accion']=='CalificacionCorregida' for x in audit)

def test_user_tokens_logout(env):
    c,h=env
    header=h['instructor']
    assert c.get('/auth/me',headers=header).status_code==200
    assert c.post('/auth/logout',headers=header).status_code==200
    assert c.get('/auth/me',headers=header).status_code==401
