"""
Backend Flask para el Bot Didi
Maneja el registro de clientes y estadísticas en la base de datos
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


def iniciar_backend():
    """Inicia el backend Flask en un hilo separado"""
    log_queue.put("[DEBUG] Thread del backend ejecutándose")

    flask_app = Flask(__name__)
    log_queue.put("[DEBUG] Flask app creada")

    # Registrar endpoints de licencias
    registrar_endpoints_licencias(flask_app)
    log_queue.put("[DEBUG] Endpoints de licencias registrados")

    @flask_app.route('/registrar', methods=['POST'])
    @token_requerido
    def registrar(usuario_actual):
        try:
            data = request.get_json()
            clientes = data.get('clientes', 0)
            exitosos = data.get('exitosos', 0)
            errores = data.get('errores', 0)

            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()

            fecha_hoy = datetime.now().strftime('%Y-%m-%d')

            # Registrar en tabla global
            cursor.execute("""
                INSERT INTO bot_ejecuciones (fecha, clientes_procesados)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                clientes_procesados = clientes_procesados + %s
            """, (fecha_hoy, clientes, clientes))

            # Registrar en tabla por usuario
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

            conn = pymysql.connect(**DB_CONFIG)
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

    @flask_app.route('/health', methods=['GET'])
    def health():
        log_queue.put("[DEBUG] Endpoint /health llamado - respondiendo OK")
        return jsonify({'status': 'ok'}), 200

    # ========================================================================
    # ENDPOINTS DE AUTENTICACIÓN
    # ========================================================================

    @flask_app.route('/auth/login', methods=['POST'])
    def login():
        """Endpoint de login - valida credenciales y retorna token JWT"""
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return jsonify({
                    'status': 'error',
                    'message': 'Username y password son requeridos'
                }), 400

            # Buscar usuario
            usuario = Usuario.obtener_por_username(username)

            if usuario is None:
                return jsonify({
                    'status': 'error',
                    'message': 'Credenciales inválidas'
                }), 401

            # Verificar si el usuario está activo
            if not usuario.activo:
                return jsonify({
                    'status': 'error',
                    'message': 'Usuario inactivo. Contacte al administrador.'
                }), 401

            # Verificar contraseña
            if not verificar_password(password, usuario.password_hash):
                return jsonify({
                    'status': 'error',
                    'message': 'Credenciales inválidas'
                }), 401

            # Invalidar todas las sesiones anteriores del usuario
            sesiones_invalidadas = Sesion.invalidar_todas_del_usuario(usuario.id)
            if sesiones_invalidadas > 0:
                log_queue.put(f"[INFO] Se invalidaron {sesiones_invalidadas} sesión(es) anterior(es) del usuario {username}")

            # Actualizar último login
            usuario.actualizar_ultimo_login()

            # Generar token JWT
            token = generar_token(usuario.id, usuario.username, usuario.rol)

            return jsonify({
                'status': 'ok',
                'message': 'Login exitoso',
                'token': token,
                'usuario': usuario.to_dict()
            }), 200

        except Exception as e:
            log_queue.put(f"[ERROR] Error en login: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @flask_app.route('/auth/register', methods=['POST'])
    @token_requerido
    @rol_requerido('admin')
    def register(usuario_actual):
        """Endpoint para registrar nuevos usuarios (solo admin)"""
        try:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            nombre_completo = data.get('nombre_completo')
            rol = data.get('rol', 'operador')

            # Validar datos requeridos
            if not username or not email or not password:
                return jsonify({
                    'status': 'error',
                    'message': 'Username, email y password son requeridos'
                }), 400

            # Validar rol
            if rol not in ['admin', 'operador']:
                return jsonify({
                    'status': 'error',
                    'message': 'Rol inválido. Use "admin" o "operador"'
                }), 400

            # Hashear password
            password_hash = hash_password(password)

            # Crear usuario
            user_id = Usuario.crear(username, email, password_hash, nombre_completo, rol)

            return jsonify({
                'status': 'ok',
                'message': 'Usuario creado exitosamente',
                'user_id': user_id
            }), 201

        except ValueError as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        except Exception as e:
            log_queue.put(f"[ERROR] Error en registro: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @flask_app.route('/auth/logout', methods=['POST'])
    @token_requerido
    def logout(usuario_actual):
        """Endpoint de logout - invalida el token"""
        try:
            # Obtener token del header
            auth_header = request.headers.get('Authorization')
            token = auth_header.split(' ')[1]

            # Invalidar token
            invalidar_token(token)

            return jsonify({
                'status': 'ok',
                'message': 'Logout exitoso'
            }), 200

        except Exception as e:
            log_queue.put(f"[ERROR] Error en logout: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @flask_app.route('/auth/verify', methods=['GET'])
    @token_requerido
    def verify_token(usuario_actual):
        """Endpoint para verificar si un token es válido"""
        return jsonify({
            'status': 'ok',
            'message': 'Token válido',
            'usuario': usuario_actual.to_dict()
        }), 200

    @flask_app.route('/auth/usuarios', methods=['GET'])
    @token_requerido
    @rol_requerido('admin')
    def listar_usuarios(usuario_actual):
        """Endpoint para listar todos los usuarios (solo admin)"""
        try:
            usuarios = Usuario.listar_todos()
            return jsonify({
                'status': 'ok',
                'usuarios': [u.to_dict() for u in usuarios]
            }), 200
        except Exception as e:
            log_queue.put(f"[ERROR] Error listando usuarios: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @flask_app.route('/estadisticas', methods=['GET'])
    def estadisticas():
        try:
            dias = int(request.args.get('dias', 7))
            conn = pymysql.connect(**DB_CONFIG)
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
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            fecha_hoy = datetime.now().strftime('%Y-%m-%d')

            # Obtener todos los clientes procesados hoy
            cursor.execute("""
                SELECT id, nombre_cliente, estado, fecha_procesado, cfrnid, monto_total
                FROM bot_clientes_procesados
                WHERE DATE(fecha_procesado) = %s
                ORDER BY fecha_procesado DESC
            """, (fecha_hoy,))

            clientes = cursor.fetchall()

            # Contar totales
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

    # Configurar Flask para modo .exe
    if IS_FROZEN:
        # En .exe: deshabilitar debug y propagación de excepciones
        flask_app.config['DEBUG'] = False
        flask_app.config['PROPAGATE_EXCEPTIONS'] = False
        log_queue.put("[*] Modo .EXE: Flask en modo producción")

    # Ejecutar Flask con Waitress (servidor de producción)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    if not IS_FROZEN:
        # Solo mostrar logs detallados en desarrollo
        log_queue.put("[DEBUG] Todos los endpoints registrados")
        log_queue.put("[DEBUG] Intentando arrancar servidor con Waitress en puerto 5000...")
        log_queue.put(f"[DEBUG] Host: {BACKEND_HOST}, Puerto: {BACKEND_PORT}")

    try:
        if not IS_FROZEN:
            log_queue.put("[DEBUG] Iniciando waitress.serve()...")

        # _quiet=True silencia logs de Waitress siempre (incluso en desarrollo)
        serve(flask_app, host=BACKEND_HOST, port=BACKEND_PORT, threads=BACKEND_THREADS, _quiet=True)

        if not IS_FROZEN:
            log_queue.put("[DEBUG] Waitress terminó de ejecutarse")
    except Exception as e:
        log_queue.put(f"[ERROR] Waitress falló al arrancar: {str(e)}")
        if not IS_FROZEN:
            import traceback
            log_queue.put(f"[ERROR] Traceback: {traceback.format_exc()}")
