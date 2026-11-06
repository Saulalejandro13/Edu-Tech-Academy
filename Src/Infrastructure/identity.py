"""Real credentials and server-side session tokens (educational single-tenant installation)."""
from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac, sha256
from hmac import compare_digest
from secrets import token_hex, token_urlsafe
from sqlalchemy import Column, String, DateTime, select
from .db import Base

ROLES = {'estudiante', 'empresa', 'instructor', 'administracion', 'control_escolar'}

class UserRow(Base):
    __tablename__ = 'usuarios'
    id = Column(String(100), primary_key=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(180), unique=True, nullable=False)
    password_hash = Column(String(250), nullable=False)
    rol = Column(String(30), nullable=False)

class SessionRow(Base):
    __tablename__ = 'sesiones'
    token_hash = Column(String(64), primary_key=True)
    usuario_id = Column(String(100), nullable=False)
    expira = Column(DateTime(timezone=True), nullable=False)

def hash_password(password):
    if len(password) < 10:
        raise ValueError('La contraseña debe tener al menos 10 caracteres')
    salt = token_hex(16)
    digest = pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 260000)
    return f'pbkdf2_sha256$260000${salt}${digest.hex()}'

def check_password(password, stored):
    try:
        algorithm, rounds, salt, digest = stored.split('$')
        if algorithm != 'pbkdf2_sha256':
            return False
        actual = pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(rounds))
        return compare_digest(actual.hex(), digest)
    except (ValueError, TypeError):
        return False

def safe_user(user):
    return {'id': user.id, 'nombre': user.nombre, 'email': user.email, 'rol': user.rol}

def issue_token(session, user):
    token = token_urlsafe(40)
    session.add(SessionRow(token_hash=sha256(token.encode()).hexdigest(), usuario_id=user.id,
                           expira=datetime.now(timezone.utc) + timedelta(hours=8)))
    return token

def lookup_token(session, token):
    if not token:
        return None
    row = session.get(SessionRow, sha256(token.encode()).hexdigest())
    if not row:
        return None
    expiry = row.expira.replace(tzinfo=timezone.utc) if row.expira.tzinfo is None else row.expira
    if expiry <= datetime.now(timezone.utc):
        session.delete(row)
        session.commit()
        return None
    return session.get(UserRow, row.usuario_id)
