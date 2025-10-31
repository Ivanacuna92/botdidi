"""
Utilidades para autenticación y manejo de passwords
"""
import bcrypt
import jwt
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

from config.auth import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from backend.models import Usuario, Sesion


def hash_password(password):
    """Hashea una contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verificar_password(password, password_hash):
    """Verifica si una contraseña coincide con su hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generar_token(user_id, username, rol):
    """Genera un token JWT para un usuario"""
    expiracion = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)

    payload = {
        'user_id': user_id,
        'username': username,
        'rol': rol,
        'exp': expiracion,
        'iat': datetime.utcnow()
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    # Crear hash del token para almacenar en la base de datos
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Guardar sesión en la base de datos
    Sesion.crear(user_id, token_hash, expiracion)

    return token


def decodificar_token(token):
    """Decodifica y valida un token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Verificar que la sesión siga activa en la base de datos
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        user_id = Sesion.validar(token_hash)

        if user_id is None:
            return None

        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_requerido(f):
    """Decorador para proteger rutas que requieren autenticación"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Obtener token del header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Formato: "Bearer TOKEN"
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'status': 'error', 'message': 'Formato de token inválido'}), 401

        if not token:
            return jsonify({'status': 'error', 'message': 'Token faltante'}), 401

        # Decodificar token
        payload = decodificar_token(token)

        if payload is None:
            return jsonify({'status': 'error', 'message': 'Token inválido o expirado'}), 401

        # Obtener usuario de la base de datos
        usuario = Usuario.obtener_por_id(payload['user_id'])

        if usuario is None or not usuario.activo:
            return jsonify({'status': 'error', 'message': 'Usuario no encontrado o inactivo'}), 401

        # Pasar el usuario a la función protegida
        return f(usuario_actual=usuario, *args, **kwargs)

    return decorated


def rol_requerido(*roles_permitidos):
    """Decorador para proteger rutas que requieren un rol específico"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Este decorador debe usarse después de @token_requerido
            usuario_actual = kwargs.get('usuario_actual')

            if usuario_actual is None:
                return jsonify({'status': 'error', 'message': 'Usuario no autenticado'}), 401

            if usuario_actual.rol not in roles_permitidos:
                return jsonify({'status': 'error', 'message': 'Permisos insuficientes'}), 403

            return f(*args, **kwargs)

        return decorated
    return decorator


def invalidar_token(token):
    """Invalida un token (para logout)"""
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        Sesion.invalidar(token_hash)
        return True
    except Exception:
        return False
