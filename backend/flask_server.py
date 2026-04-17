"""
Backend Flask para el Bot Didi
Maneja el registro de clientes y estadísticas en la base de datos.
Usado tanto por la app de escritorio como por la extension de Chrome.
"""
from flask import Flask, request, jsonify
from waitress import serve
import pymysql
from datetime import datetime
import logging

from config.settings import DB_CONFIG, BACKEND_HOST, BACKEND_PORT, BACKEND_THREADS, log_queue
from config.paths import IS_FROZEN
from backend.models import Usuario, Sesion
from backend.auth_utils import (
    hash_password, verificar_password, generar_token,
    token_requerido, rol_requerido, invalidar_token
)
from backend.license_endpoints import registrar_endpoints_licencias


def crear_app():
    """Factory: crea la app Flask con todos los endpoints y CORS."""
    flask_app = Flask(__name__)

    try:
        from flask_cors import CORS
        CORS(flask_app, origins=[
            'chrome-extension://*',
            'http://localhost:*',
        ])
    except ImportError:
        pass

    registrar_endpoints_licencias(flask_app)

    # ==================================================================
    # HEALTH
    # ==================================================================

    @flask_app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok'}), 200

    # ==================================================================
    # ENDPOINTS DE DATOS
    # ==================================================================

    @flask_app.route('/registrar', methods=['POST'])
    @token_requerido
    def registrar(usuario_actual):
        try:
            data = request.get_json()
            clientes = data.get('clientes', 0)
            exitosos = data.get('exitosos', 0)
            errores = data.get('errores', 0)

            conn = pymysql.connect(**DB_CONFIG, connect_timeout=5)
            cursor = conn.cursor()

            fecha_hoy = datetime.now().strftime('%Y-%m-%d')

            cursor.execute("""
                INSERT INTO bot_ejecuciones (fecha, clientes_procesados)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                clientes_procesados = clientes_procesados + %s
            """, (fecha_hoy, clientes, clientes))

            cursor.execute("""
                INSERT INTO bot_ejecuciones_usuarios
                (user_id, fecha, clientes_procesados, clientes_exitosos, clientes_errores)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                clientes_procesados = clientes_procesados + %s,
                clientes_exitosos = clientes_exitosos + %s,
                clientes_errores = clientes_errores + %s
            """, (usuario_actual.id, fecha_hoy, clientes, exitosos, errores,
                  clientes, exitosos, errores))

            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({'status': 'ok', 'clientes': clientes}), 200

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @flask_app.route('/registrar_cliente', methods=['POST'])
    @token_requerido
    def registrar_cliente(usuario_actual):
        try:
            data = request.get_json()
            nombre = data.get('nombre', 'DESCONOCIDO')
            estado = data.get('estado', 'exitoso')
            cfrnid = data.get('cfrnid', 'DESCONOCIDO')
            monto_total = data.get('monto_total', '0.00')

            conn = pymysql.connect(**DB_CONFIG, connect_timeout=5)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO bot_clientes_procesados (user_id, nombre_cliente, estado, cfrnid, monto_total)
                VALUES (%s, %s, %s, %s, %s)
            """, (usuario_actual.id, nombre, estado, cfrnid, monto_total))

            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({'status': 'ok', 'nombre': nombre, 'estado': estado, 'cfrnid': cfrnid, 'monto_total': monto_total}), 200

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    # ==================================================================
    # ENDPOINTS DE AUTENTICACION
    # ==================================================================

    @flask_app.route('/auth/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return jsonify({
                    'status': 'error',
                    'message': 'Username y password son requeridos'
                }), 400

            usuario = Usuario.obtener_por_username(username)

            if usuario is None:
                return jsonify({
                    'status': 'error',
                    'message': 'Credenciales inválidas'
                }), 401

            if not usuario.activo:
                return jsonify({
                    'status': 'error',
                    'message': 'Usuario inactivo. Contacte al administrador.'
                }), 401

            if not verificar_password(password, usuario.password_hash):
                return jsonify({
                    'status': 'error',
                    'message': 'Credenciales inválidas'
                }), 401

            Sesion.invalidar_todas_del_usuario(usuario.id)
            usuario.actualizar_ultimo_login()
            token = generar_token(usuario.id, usuario.username, usuario.rol)

            return jsonify({
                'status': 'ok',
                'message': 'Login exitoso',
                'token': token,
                'usuario': usuario.to_dict()
            }), 200

        except pymysql.OperationalError:
            return jsonify({
                'status': 'error',
                'message': 'Error de conexión a la base de datos. Intente nuevamente.'
            }), 500
        except Exception:
            return jsonify({
                'status': 'error',
                'message': 'Error interno del servidor. Contacte al administrador.'
            }), 500

    @flask_app.route('/auth/register', methods=['POST'])
    @token_requerido
    @rol_requerido('admin')
    def register(usuario_actual):
        try:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            nombre_completo = data.get('nombre_completo')
            rol = data.get('rol', 'operador')

            if not username or not email or not password:
                return jsonify({
                    'status': 'error',
                    'message': 'Username, email y password son requeridos'
                }), 400

            if rol not in ['admin', 'operador']:
                return jsonify({
                    'status': 'error',
                    'message': 'Rol inválido. Use "admin" o "operador"'
                }), 400

            password_hash = hash_password(password)
            user_id = Usuario.crear(username, email, password_hash, nombre_completo, rol)

            return jsonify({
                'status': 'ok',
                'message': 'Usuario creado exitosamente',
                'user_id': user_id
            }), 201

        except ValueError as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @flask_app.route('/auth/logout', methods=['POST'])
    @token_requerido
    def logout(usuario_actual):
        try:
            auth_header = request.headers.get('Authorization')
            token = auth_header.split(' ')[1]
            invalidar_token(token)
            return jsonify({'status': 'ok', 'message': 'Logout exitoso'}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @flask_app.route('/auth/verify', methods=['GET'])
    @token_requerido
    def verify_token(usuario_actual):
        return jsonify({
            'status': 'ok',
            'message': 'Token válido',
            'usuario': usuario_actual.to_dict()
        }), 200

    @flask_app.route('/auth/usuarios', methods=['GET'])
    @token_requerido
    @rol_requerido('admin')
    def listar_usuarios(usuario_actual):
        try:
            usuarios = Usuario.listar_todos()
            return jsonify({
                'status': 'ok',
                'usuarios': [u.to_dict() for u in usuarios]
            }), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    # ==================================================================
    # ENDPOINTS DE ESTADISTICAS
    # ==================================================================

    @flask_app.route('/estadisticas', methods=['GET'])
    def estadisticas():
        try:
            dias = int(request.args.get('dias', 7))
            conn = pymysql.connect(**DB_CONFIG, connect_timeout=5)
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            cursor.execute("""
                SELECT fecha, clientes_procesados
                FROM bot_ejecuciones
                ORDER BY fecha DESC
                LIMIT %s
            """, (dias,))

            resultados = cursor.fetchall()
            cursor.close()
            conn.close()

            return jsonify({'status': 'ok', 'datos': resultados}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @flask_app.route('/clientes_hoy', methods=['GET'])
    def clientes_hoy():
        try:
            conn = pymysql.connect(**DB_CONFIG, connect_timeout=5)
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            fecha_hoy = datetime.now().strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT id, nombre_cliente, estado, fecha_procesado, cfrnid, monto_total
                FROM bot_clientes_procesados
                WHERE DATE(fecha_procesado) = %s
                ORDER BY fecha_procesado DESC
            """, (fecha_hoy,))

            clientes = cursor.fetchall()
            total = len(clientes)
            exitosos = sum(1 for c in clientes if c['estado'] == 'exitoso')
            errores = sum(1 for c in clientes if c['estado'] == 'error')

            cursor.close()
            conn.close()

            return jsonify({
                'status': 'ok',
                'clientes': clientes,
                'total': total,
                'exitosos': exitosos,
                'errores': errores
            }), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    return flask_app


def iniciar_backend():
    """Inicia el backend Flask en un hilo separado (modo escritorio)"""
    log_queue.put("[DEBUG] Thread del backend ejecutándose")

    flask_app = crear_app()
    log_queue.put("[DEBUG] Flask app creada con CORS")

    if IS_FROZEN:
        flask_app.config['DEBUG'] = False
        flask_app.config['PROPAGATE_EXCEPTIONS'] = False
        log_queue.put("[*] Modo .EXE: Flask en modo producción")

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    if not IS_FROZEN:
        log_queue.put(f"[DEBUG] Iniciando Waitress en {BACKEND_HOST}:{BACKEND_PORT}")

    try:
        serve(flask_app, host=BACKEND_HOST, port=BACKEND_PORT, threads=BACKEND_THREADS, _quiet=True)
    except Exception as e:
        log_queue.put(f"[ERROR] Waitress falló al arrancar: {str(e)}")
