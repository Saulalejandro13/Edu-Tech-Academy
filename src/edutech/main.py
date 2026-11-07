"""EduTech Academy: multi-actor REST API and web application.

The source of truth is the BRD / Gherkin / BPMN; policy gaps remain configurable.
No external payments or automatic money transfers are performed.
"""
import os
from dataclasses import asdict
from datetime import date
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from edutech.application.services import EduTechService, NotFoundError
from edutech.domain.model import DomainError, Politicas, CupoSpecification, Inscripcion, CourseState, EnrollmentState, nuevo_id
from edutech.infrastructure.db import UnitOfWork, make_session_factory, EnrollmentRow
from edutech.infrastructure.identity import UserRow, SessionRow, ROLES, hash_password, check_password, safe_user, issue_token, lookup_token
from edutech.infrastructure.workflows import (GroupRow, AssignmentRow, RequestRow, EvaluationRow,
                                               CertificateRow, CompanyInviteRow, CourseProfileRow, new_id, request_dict)

class Register(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=180)
    password: str = Field(min_length=10)
    rol: str = 'estudiante'

class Login(BaseModel):
    email: str
    password: str

class NuevoCurso(BaseModel):
    id: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    precio: float = Field(ge=0)
    instructor_id: str = Field(min_length=1)
    modalidad: str = "por_definir"
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    cierre_inscripcion: date | None = None
    requisitos: str = ""

class NuevaInscripcion(BaseModel):
    curso_id: str
    grupo_id: str | None = None
    estudiante_id: str | None = None  # ignored for student users; server decides identity

class EmpresaInscripcion(BaseModel):
    curso_id: str
    grupo_id: str | None = None
    empleados: list[str] = Field(min_length=1, max_length=25)

class GrupoNuevo(BaseModel):
    nombre: str = Field(min_length=1)
    maximo: int = Field(default=25, ge=1, le=25)

class NuevaAsistencia(BaseModel):
    presente: bool

class NuevaEvaluacion(BaseModel):
    tipo: str
    fecha: date
    calificacion: float = Field(ge=0, le=100)

class NuevaCalificacion(BaseModel):
    calificacion: float = Field(ge=0, le=100)

class Correccion(BaseModel):
    calificacion: float = Field(ge=0, le=100)
    motivo: str = Field(min_length=5)

class Sustitucion(BaseModel):
    instructor_id: str = Field(min_length=1)
    motivo: str = Field(min_length=5)

class NuevaSolicitud(BaseModel):
    tipo: str
    destino: str | None = None
    motivo: str = Field(min_length=5)

class Resolucion(BaseModel):
    decision: str  # autorizada | rechazada
    observacion: str = Field(min_length=5)

class NuevaResolucion(BaseModel):
    tipo: str  # reembolso | reinscripcion
    motivo: str = Field(min_length=5)

ROLE_NAMES = {
    'estudiante':'Estudiante','empresa':'Cliente empresarial','instructor':'Instructor',
    'administracion':'Administración','control_escolar':'Control Escolar'
}


def create_app(database_url=None, politicas=None):
    database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///./edutech.db')
    sf = make_session_factory(database_url)
    service = EduTechService(lambda: UnitOfWork(sf), politicas or Politicas(
        asistencia_minima=float(os.getenv('ASISTENCIA_MINIMA', '80')),
        plazo_pago_dias=int(os.getenv('PLAZO_PAGO_DIAS', '7'))))
    app = FastAPI(title='EduTech Academy • API multiusuario', version='2.0.0',
                  description='BRD, BPMN, DDD: estudiantes, empresa, instructor, administración y control escolar. Cobros/reembolsos simulados.')

    @app.exception_handler(DomainError)
    async def domain_error(_, exc):
        return JSONResponse(status_code=404 if isinstance(exc, NotFoundError) else 422,
                            content={'detail':str(exc)})

    def require_user(authorization: str | None = Header(default=None)):
        token = authorization.split(' ',1)[1] if authorization and authorization.lower().startswith('bearer ') else ''
        with sf() as db:
            user = lookup_token(db, token)
            if not user:
                raise HTTPException(401, 'Inicia sesión para continuar')
            return safe_user(user)

    def access(*roles):
        def permitted(user=Depends(require_user)):
            if user['rol'] not in roles:
                raise HTTPException(403, 'Tu perfil no tiene permiso para esta operación')
            return user
        return permitted

    def ensure_course_instructor(course_id, user):
        if user['rol'] == 'instructor' and service.curso(course_id).instructor_id != user['id']:
            raise HTTPException(403, 'Solo puedes gestionar los cursos asignados a tu cuenta')

    def check_enrollment(eid, user, *allowed_staff):
        insc=service.inscripcion(eid)
        if user['rol']=='estudiante' and insc.estudiante_id!=user['id']:
            raise HTTPException(403,'Esta inscripción no te pertenece')
        if user['rol']=='empresa':
            with sf() as db:
                a=db.get(AssignmentRow,eid)
                if not a or a.empresa_id!=user['id']:
                    raise HTTPException(403,'La inscripción no pertenece a tu empresa')
        if user['rol']=='instructor':
            ensure_course_instructor(insc.curso_id,user)
        if user['rol'] not in {'estudiante','empresa','instructor',*allowed_staff}:
            raise HTTPException(403,'Permiso denegado')
        return insc

    def group_json(db, group):
        occupied=db.scalar(select(func.count()).select_from(AssignmentRow)
                           .where(AssignmentRow.grupo_id==group.id)) or 0
        return {'id':group.id,'curso_id':group.curso_id,'nombre':group.nombre,
                'maximo':int(group.maximo),'ocupados':occupied,'disponibles':int(group.maximo)-occupied}

    def default_group(db, cid):
        group=db.scalar(select(GroupRow).where(GroupRow.curso_id==cid).order_by(GroupRow.id))
        if group is None:
            group=GroupRow(id=new_id(),curso_id=cid,nombre='Grupo general',maximo=25)
            db.add(group)
            db.flush()
        return group

    # Demo accounts are created ONLY on an explicit opt-in. Never seed production passwords.
    if os.getenv('DEMO_SEED')=='1':
        accounts=[('EST-DEMO','Ana Estudiante','alumno@edutech.test','estudiante'),
                  ('EMP-DEMO','Empresa Ejemplo','empresa@edutech.test','empresa'),
                  ('INST-DEMO','Instructor Demo','instructor@edutech.test','instructor'),
                  ('ADM-DEMO','Administración Demo','admin@edutech.test','administracion'),
                  ('ESC-DEMO','Control Escolar Demo','escolar@edutech.test','control_escolar')]
        pass_demo=os.getenv('DEMO_PASSWORD','DemoSegura2026!')
        with sf.begin() as db:
            for uid,nombre,email,rol in accounts:
                if not db.get(UserRow,uid):
                    db.add(UserRow(id=uid,nombre=nombre,email=email,password_hash=hash_password(pass_demo),rol=rol))
        if not service.cursos():
            service.crear_curso('PY-101','Fundamentos de Python',1500,'INST-DEMO')
            service.crear_curso('SQL-201','SQL y Bases de Datos',1800,'INST-DEMO')
            service.crear_curso('BI-301','Inteligencia de Negocios',2200,'INST-DEMO')
    # Initial administrator must be configured explicitly for non-demo installations.
    if os.getenv('ADMIN_EMAIL') and os.getenv('ADMIN_PASSWORD'):
        with sf.begin() as db:
            email=os.environ['ADMIN_EMAIL'].strip().lower()
            if db.scalar(select(UserRow).where(UserRow.email==email)) is None:
                db.add(UserRow(id='ADM-'+new_id()[:10],nombre='Administrador',email=email,
                               password_hash=hash_password(os.environ['ADMIN_PASSWORD']),rol='administracion'))

    static_dir=Path(__file__).parent/'static'
    app.mount('/static',StaticFiles(directory=static_dir),name='static')

    @app.get('/',include_in_schema=False)
    def home():return FileResponse(static_dir/'index.html')

    @app.get('/health')
    def health():return {'status':'ok'}

    @app.post('/auth/registro',status_code=201)
    def register(data:Register):
        if data.rol not in ('estudiante','empresa'):
            raise HTTPException(403,'Solo estudiantes y empresas pueden registrarse públicamente')
        with sf.begin() as db:
            email=data.email.strip().lower()
            if db.scalar(select(UserRow.id).where(UserRow.email==email)):
                raise HTTPException(409,'El correo ya está registrado')
            user=UserRow(id=('EMP-' if data.rol=='empresa' else 'EST-')+new_id()[:12],
                         nombre=data.nombre.strip(),email=email,password_hash=hash_password(data.password),rol=data.rol)
            db.add(user)
            return safe_user(user)

    @app.post('/auth/login')
    def login(data:Login):
        with sf.begin() as db:
            user=db.scalar(select(UserRow).where(UserRow.email==data.email.strip().lower()))
            if not user or not check_password(data.password,user.password_hash):
                raise HTTPException(401,'Correo o contraseña incorrectos')
            token=issue_token(db,user)
            return {'token':token,'usuario':safe_user(user)}

    @app.get('/auth/me')
    def me(user=Depends(require_user)):return user

    @app.post('/auth/logout')
    def logout(authorization:str|None=Header(default=None),user=Depends(require_user)):
        token=authorization.split(' ',1)[1]
        from hashlib import sha256
        with sf.begin() as db:
            row=db.get(SessionRow,sha256(token.encode()).hexdigest())
            if row:db.delete(row)
        return {'mensaje':'Sesión cerrada'}

    @app.get('/usuarios')
    def usuarios(user=Depends(access('administracion','control_escolar'))):
        with sf() as db:return [safe_user(u) for u in db.scalars(select(UserRow).order_by(UserRow.rol)).all()]

    @app.post('/usuarios',status_code=201)
    def crear_usuario(data:Register,user=Depends(access('administracion'))):
        if data.rol not in ROLES:raise HTTPException(422,'Rol desconocido')
        with sf.begin() as db:
            email=data.email.strip().lower()
            if db.scalar(select(UserRow).where(UserRow.email==email)):raise HTTPException(409,'Correo ya registrado')
            row=UserRow(id=('INST-' if data.rol=='instructor' else 'USR-')+new_id()[:12],
                        nombre=data.nombre,email=email,password_hash=hash_password(data.password),rol=data.rol)
            db.add(row)
            return safe_user(row)

    def course_payload(c):
        with sf() as db:
            profile=db.get(CourseProfileRow,c.id)
            details={'modalidad':profile.modalidad,'fecha_inicio':profile.fecha_inicio,'fecha_fin':profile.fecha_fin,
                     'cierre_inscripcion':profile.cierre_inscripcion,'requisitos':profile.requisitos} if profile else {
                        'modalidad':'por_definir','fecha_inicio':None,'fecha_fin':None,
                        'cierre_inscripcion':None,'requisitos':''}
        return {**asdict(c),**details}

    @app.get('/cursos')
    def cursos():return [course_payload(c) for c in service.cursos()]

    @app.get('/cursos/{cid}')
    def curso(cid:str):return course_payload(service.curso(cid))

    @app.post('/cursos',status_code=201)
    def crear_curso(data:NuevoCurso,user=Depends(access('administracion'))):
        if data.modalidad not in {'presencial','en_linea','hibrida','por_definir'}:
            raise HTTPException(422,'Modalidad inválida')
        if data.fecha_inicio and data.fecha_fin and data.fecha_fin<data.fecha_inicio:
            raise HTTPException(422,'La fecha final es anterior a la inicial')
        c=service.crear_curso(data.id,data.nombre,data.precio,data.instructor_id)
        with sf.begin() as db:
            default_group(db,c.id)
            db.add(CourseProfileRow(curso_id=c.id,modalidad=data.modalidad,
                fecha_inicio=str(data.fecha_inicio) if data.fecha_inicio else None,
                fecha_fin=str(data.fecha_fin) if data.fecha_fin else None,
                cierre_inscripcion=str(data.cierre_inscripcion) if data.cierre_inscripcion else None,
                requisitos=data.requisitos))
        return course_payload(c)

    @app.get('/cursos/{cid}/grupos')
    def grupos(cid:str):
        service.curso(cid)
        with sf.begin() as db:
            group=default_group(db,cid)
            groups=db.scalars(select(GroupRow).where(GroupRow.curso_id==cid)).all()
            return [group_json(db,g) for g in groups]

    @app.post('/cursos/{cid}/grupos',status_code=201)
    def crear_grupo(cid:str,data:GrupoNuevo,user=Depends(access('administracion'))):
        service.curso(cid)
        with sf.begin() as db:
            group=GroupRow(id=new_id(),curso_id=cid,nombre=data.nombre,maximo=data.maximo)
            db.add(group);db.flush()
            return group_json(db,group)

    def do_bulk_inscribe(estudiantes,cid,group_id,empresa=None):
        if len(estudiantes)!=len(set(estudiantes)):
            raise HTTPException(422,'La lista contiene estudiantes repetidos')
        with UnitOfWork(sf) as uow:
            course=uow.cursos.get(cid)
            if course is None:raise NotFoundError('Curso no encontrado')
            profile=uow.session.get(CourseProfileRow,cid)
            if profile and profile.cierre_inscripcion and date.today().isoformat()>profile.cierre_inscripcion:
                raise DomainError('El periodo de inscripción finalizó')
            if not CupoSpecification(len(estudiantes)).is_satisfied_by(course):
                raise DomainError('Cupo insuficiente; no se confirmaron inscripciones parciales')
            group=uow.session.get(GroupRow,group_id) if group_id else default_group(uow.session,cid)
            if not group or group.curso_id!=cid:raise DomainError('Grupo no pertenece al curso')
            if group_json(uow.session,group)['disponibles']<len(estudiantes):
                raise DomainError('Grupo sin cupo suficiente; operación atómica')
            for sid in estudiantes:
                if uow.session.scalar(select(EnrollmentRow.id).where(
                       EnrollmentRow.estudiante_id==sid, EnrollmentRow.curso_id==cid)):
                    raise DomainError('Ya existe inscripción en este curso para: '+sid)
            course.inscribir(len(estudiantes))
            uow.cursos.save(course)
            results=[]
            for sid in estudiantes:
                insc=Inscripcion(nuevo_id(),sid,cid)
                uow.inscripciones.save(insc)
                uow.session.add(AssignmentRow(inscripcion_id=insc.id,grupo_id=group.id,empresa_id=empresa))
                uow.audit('Inscripcion',insc.id,'InscripcionRealizada',{'curso_id':cid,'grupo':group.id,'empresa':empresa})
                results.append(asdict(insc))
            return results

    @app.post('/inscripciones',status_code=201)
    def inscribir(data:NuevaInscripcion,user=Depends(access('estudiante'))):
        return do_bulk_inscribe([user['id']],data.curso_id,data.grupo_id)[0]

    @app.post('/empresas/inscripciones',status_code=201)
    def inscribir_empresa(data:EmpresaInscripcion,user=Depends(access('empresa','administracion'))):
        with sf() as db:
            rows=db.scalars(select(UserRow).where(UserRow.id.in_(data.empleados))).all()
            valid={u.id for u in rows if u.rol=='estudiante'}
            if set(data.empleados)!=valid:raise HTTPException(422,'Los empleados deben ser usuarios registrados como estudiantes')
        if user['rol']=='empresa':
            with sf() as db:
                accepted=set(db.scalars(select(CompanyInviteRow.estudiante_id).where(CompanyInviteRow.empresa_id==user['id'],CompanyInviteRow.estado=='aceptada')).all())
                if not set(data.empleados).issubset(accepted):
                    raise HTTPException(403,'Cada empleado debe aceptar la invitación de esta empresa antes de ser inscrito')
        return {'inscripciones':do_bulk_inscribe(data.empleados,data.curso_id,data.grupo_id,
                                                   user['id'] if user['rol']=='empresa' else None)}

    @app.post('/empresas/invitaciones/{estudiante_id}',status_code=201)
    def invitar_empleado(estudiante_id:str,user=Depends(access('empresa'))):
        with UnitOfWork(sf) as uow:
            student=uow.session.get(UserRow,estudiante_id)
            if not student or student.rol!='estudiante':
                raise HTTPException(404,'Estudiante no encontrado')
            existing=uow.session.scalar(select(CompanyInviteRow).where(
                CompanyInviteRow.empresa_id==user['id'],CompanyInviteRow.estudiante_id==estudiante_id))
            if existing:return {'id':existing.id,'estado':existing.estado}
            invite=CompanyInviteRow(id=new_id(),empresa_id=user['id'],estudiante_id=estudiante_id,estado='pendiente')
            uow.session.add(invite)
            uow.audit('Empresa',user['id'],'InvitacionEnviada',{'estudiante_id':estudiante_id})
            return {'id':invite.id,'estado':invite.estado}

    @app.get('/empresas/invitaciones')
    def invitaciones(user=Depends(access('estudiante','empresa'))):
        with sf() as db:
            query=select(CompanyInviteRow).where(CompanyInviteRow.estudiante_id==user['id']) if user['rol']=='estudiante' else select(CompanyInviteRow).where(CompanyInviteRow.empresa_id==user['id'])
            return [{'id':r.id,'empresa_id':r.empresa_id,'estudiante_id':r.estudiante_id,'estado':r.estado} for r in db.scalars(query).all()]

    @app.post('/empresas/invitaciones/{invite_id}/responder')
    def responder_invitacion(invite_id:str,decision:str,user=Depends(access('estudiante'))):
        if decision not in {'aceptada','rechazada'}:raise HTTPException(422,'Respuesta inválida')
        with UnitOfWork(sf) as uow:
            row=uow.session.get(CompanyInviteRow,invite_id)
            if not row or row.estudiante_id!=user['id']:raise HTTPException(404,'Invitación no encontrada')
            if row.estado!='pendiente':raise DomainError('Invitación resuelta')
            row.estado=decision
            uow.audit('Empresa',row.empresa_id,'InvitacionRespondida',{'estudiante':user['id'],'respuesta':decision})
            return {'id':row.id,'estado':row.estado}

    @app.get('/mis-inscripciones')
    def mis_inscripciones(user=Depends(require_user)):
        with sf() as db:
            if user['rol']=='estudiante':
                inscs=service.inscripciones(user['id'])
            elif user['rol']=='empresa':
                ids=set(db.scalars(select(AssignmentRow.inscripcion_id).where(AssignmentRow.empresa_id==user['id'])).all())
                inscs=[i for i in service.inscripciones() if i.id in ids]
            elif user['rol']=='instructor':
                courses={c.id for c in service.cursos() if c.instructor_id==user['id']}
                inscs=[i for i in service.inscripciones() if i.curso_id in courses]
            else:inscs=service.inscripciones()
            assignments={a.inscripcion_id:a for a in db.scalars(select(AssignmentRow)).all()}
           

            estudiante_ids = {i.estudiante_id for i in inscs}

            usuarios = {
                u.id: u
                for u in db.scalars(
                    select(UserRow).where(
                        UserRow.id.in_(estudiante_ids)
                    )
                ).all()
            } if estudiante_ids else {}

            return [
                {
                    **asdict(i),
                    'grupo_id': (
                        assignments[i.id].grupo_id
                        if i.id in assignments else None
                    ),
                    'estudiante_nombre': (
                        usuarios[i.estudiante_id].nombre
                        if i.estudiante_id in usuarios
                        else i.estudiante_id
                    )
                }
                for i in inscs
            ]



    @app.get('/inscripciones/{eid}')
    def inscripcion(eid: str, user=Depends(require_user)):
        return asdict(
            check_enrollment(
                eid, user, 'administracion', 'control_escolar'
            )
        )
    @app.post('/inscripciones/{eid}/pago')
    def pagar(eid:str,user=Depends(access('estudiante','administracion'))):
        insc=check_enrollment(eid,user,'administracion')
        # Demonstration-only registration; no real payment or external provider.
        return asdict(service.pagar(eid))

    @app.post('/inscripciones/{eid}/asistencia')
    def asistencia(eid:str,data:NuevaAsistencia,user=Depends(access('instructor'))):
        check_enrollment(eid,user)
        return asdict(service.asistencia(eid,data.presente))

    @app.post('/inscripciones/{eid}/evaluaciones',status_code=201)
    def evaluar(eid:str,data:NuevaEvaluacion,user=Depends(access('instructor'))):
        check_enrollment(eid,user)
        if data.tipo not in {'parcial','final','proyecto','participacion'}:
            raise HTTPException(422,'Tipo de evaluación no contemplado en el BRD')
        with UnitOfWork(sf) as uow:
            i=uow.inscripciones.get(eid)
            i.evaluar(data.calificacion)
            uow.inscripciones.save(i)
            evalrow=EvaluationRow(id=new_id(),inscripcion_id=eid,tipo=data.tipo,
                                  fecha=data.fecha.isoformat(),nota=data.calificacion,instructor_id=user['id'])
            uow.session.add(evalrow)
            uow.audit('Evaluacion',evalrow.id,'CalificacionRegistrada',{'inscripcion':eid,'tipo':data.tipo,'nota':data.calificacion,'responsable':user['id']})
            return {'evaluacion':evalrow.id,'inscripcion':asdict(i)}

    @app.get('/inscripciones/{eid}/evaluaciones')
    def evaluaciones(eid:str,user=Depends(require_user)):
        check_enrollment(eid,user,'administracion','control_escolar')
        with sf() as db:
            rows=db.scalars(select(EvaluationRow).where(EvaluationRow.inscripcion_id==eid)).all()
            return [{'id':r.id,'tipo':r.tipo,'fecha':r.fecha,'nota':r.nota} for r in rows]

    @app.post('/inscripciones/{eid}/corregir-calificacion')
    def corregir(eid:str,data:Correccion,user=Depends(access('control_escolar'))):
        return asdict(service.corregir_calificacion(eid,data.calificacion,user['id'],data.motivo))

    @app.post('/cursos/{cid}/sustituir-instructor')
    def sustituir(cid:str,data:Sustitucion,user=Depends(access('administracion'))):
        with sf() as db:
            instructor=db.get(UserRow,data.instructor_id)
            if not instructor or instructor.rol!='instructor':
                raise HTTPException(422,'El nuevo instructor debe tener una cuenta de instructor')
        return asdict(service.cambiar_instructor(cid,data.instructor_id,user['id'],data.motivo))

    @app.post('/cursos/{cid}/{accion}')
    def gestionar_estado(cid:str,accion:str,user=Depends(access('administracion'))):
        if accion not in {'iniciar','concluir','cancelar'}:raise HTTPException(404,'Acción desconocida')
        c=service.estado_curso(cid,accion)
        if accion=='cancelar':
            with UnitOfWork(sf) as uow:
                for i in uow.inscripciones.list_by_course(cid):
                    req=RequestRow(id=new_id(),inscripcion_id=i.id,tipo='resolucion_cancelacion',
                                   estado='pendiente',motivo='Curso cancelado: requiere revisión administrativa')
                    uow.session.add(req)
                    uow.audit('Solicitud',req.id,'CasoResolucionAbierto',{'curso':cid,'inscripcion':i.id})
        return asdict(c)

    @app.post('/inscripciones/{eid}/certificar')
    def certificar(eid:str,user=Depends(access('control_escolar'))):
        result=service.certificar(eid)
        with UnitOfWork(sf) as uow:
            if not uow.session.scalar(select(CertificateRow).where(CertificateRow.inscripcion_id==eid)):
                cert=CertificateRow(id='CERT-'+new_id()[:14].upper(),inscripcion_id=eid,emisor=user['id'])
                uow.session.add(cert)
                uow.audit('Certificado',cert.id,'CertificadoGenerado',{'inscripcion':eid,'emisor':user['id']})
        return asdict(result)

    @app.get('/mis-certificados')
    def certificados(user=Depends(require_user)):
        ids={i.id for i in service.inscripciones(user['id'])} if user['rol']=='estudiante' else set()
        with sf() as db:
            rows=db.scalars(select(CertificateRow)).all()
            return [{'id':r.id,'inscripcion_id':r.inscripcion_id,'fecha':r.emitido_en.isoformat()}
                    for r in rows if user['rol'] in {'administracion','control_escolar'} or r.inscripcion_id in ids]

    @app.post('/inscripciones/{eid}/solicitudes',status_code=201)
    def solicitar(eid:str,data:NuevaSolicitud,user=Depends(access('estudiante','empresa'))):
        i=check_enrollment(eid,user)
        if data.tipo not in {'cambio_grupo','reinscripcion','resolucion_cancelacion'}:
            raise HTTPException(422,'Tipo de solicitud inválido')
        if data.tipo=='cambio_grupo':
            if not data.destino:raise HTTPException(422,'Debes seleccionar grupo destino')
            with sf() as db:
                group=db.get(GroupRow,data.destino)
                if not group or group.curso_id!=i.curso_id:raise HTTPException(422,'Grupo destino inválido')
        if data.tipo=='reinscripcion' and (i.calificacion is None or i.calificacion>=70):
            raise HTTPException(422,'La reinscripción por reprobación requiere calificación menor a 70')
        if data.tipo=='resolucion_cancelacion' and i.estado!=EnrollmentState.CANCELLED:
            raise HTTPException(422,'No hay una cancelación de curso para resolver')
        with UnitOfWork(sf) as uow:
            req=RequestRow(id=new_id(),inscripcion_id=eid,tipo=data.tipo,estado='pendiente',
                           destino=data.destino,motivo=data.motivo)
            uow.session.add(req)
            uow.audit('Solicitud',req.id,'SolicitudCreada',{'tipo':req.tipo,'actor':user['id'],'inscripcion':eid})
            return request_dict(req)

    @app.get('/solicitudes')
    def solicitudes(user=Depends(require_user)):
        with sf() as db:
            rows=db.scalars(select(RequestRow).order_by(RequestRow.fecha.desc())).all()
            own={i.id for i in service.inscripciones(user['id'])} if user['rol']=='estudiante' else set()
            if user['rol']=='empresa':
                own=set(db.scalars(select(AssignmentRow.inscripcion_id).where(AssignmentRow.empresa_id==user['id'])).all())
            if user['rol']=='instructor':
                own={i.id for i in service.inscripciones() if service.curso(i.curso_id).instructor_id==user['id']}
            return [request_dict(r) for r in rows if user['rol'] in {'administracion','control_escolar'} or r.inscripcion_id in own]

    @app.post('/solicitudes/{rid}/resolver')
    def resolver(rid:str,data:Resolucion,user=Depends(access('control_escolar','administracion'))):
        if data.decision not in {'autorizada','rechazada'}:raise HTTPException(422,'Decisión inválida')
        with UnitOfWork(sf) as uow:
            req=uow.session.get(RequestRow,rid)
            if not req:raise NotFoundError('Solicitud no encontrada')
            if req.estado!='pendiente':raise DomainError('Solicitud ya resuelta')
            if req.tipo=='cambio_grupo' and user['rol']!='control_escolar':
                raise HTTPException(403,'Control Escolar autoriza cambios de grupo')
            if data.decision=='autorizada' and req.tipo=='cambio_grupo':
                assignment=uow.session.get(AssignmentRow,req.inscripcion_id)
                group=uow.session.get(GroupRow,req.destino)
                if not assignment or not group or group_json(uow.session,group)['disponibles']<=0:
                    raise DomainError('Grupo destino sin cupo')
                assignment.grupo_id=req.destino
            # Reimbursements and reenrollments require undefined business policies;
            # authorization records a decision, never transfers money or silently creates enrollments.
            req.estado=data.decision
            req.responsable=user['id']
            req.observacion=data.observacion
            uow.audit('Solicitud',rid,'SolicitudResuelta',{'decision':data.decision,'responsable':user['id'],
                                                            'observacion':data.observacion})
            return request_dict(req)

    @app.get('/bitacora')
    def bitacora(user=Depends(access('administracion','control_escolar'))):return service.bitacora()

    return app

app=create_app()
