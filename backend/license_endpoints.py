"""
Endpoints de Flask para el sistema de licencias
- Activar licencia
- Validar licencia
- Obtener información de licencia
"""
import pymysql
from flask import request, jsonify
from datetime import datetime

from config.settings import DB_CONFIG
from backend.license_utils import generar_hardware_id, obtener_info_maquina, validar_formato_clave


def registrar_endpoints_licencias(app):
    """
    Registra todos los endpoints de licencias en la app Flask
    """

    @app.route('/licencias/activar', methods=['POST'])
    def activar_licencia():
        """
        Activa una licencia en esta máquina

        Body JSON:
        {
            "clave": "DIDI-XXXX-XXXX-XXXX",
            "hardware_id": "HW-XXXXXXXX-...",
            "nombre_maquina": "PC-01",
            "usuario_sistema": "Usuario"
        }

        Respuestas:
        200: Activación exitosa
        400: Error de validación (clave inválida, ya activada, etc.)
        500: Error del servidor
        """
        try:
            data = request.get_json()
            clave = data.get('clave', '').strip().upper()
            hardware_id = data.get('hardware_id', '').strip()
            nombre_maquina = data.get('nombre_maquina', '')
            usuario_sistema = data.get('usuario_sistema', '')
            hw_componentes = data.get('hw_componentes', {})
            ip_address = request.remote_addr

            # Validar formato de la clave
            if not validar_formato_clave(clave):
                return jsonify({
                    'status': 'error',
                    'message': 'Formato de clave inválido. Use: DIDI-XXXX-XXXX-XXXX'
                }), 400

            # Validar que se envió hardware_id
            if not hardware_id:
                return jsonify({
                    'status': 'error',
                    'message': 'Hardware ID es requerido'
                }), 400

            # Conectar a base de datos
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Buscar la licencia
            cursor.execute("""
                SELECT * FROM licencias
                WHERE clave = %s
            """, (clave,))

            licencia = cursor.fetchone()

            # Validar que la clave exista
            if not licencia:
                cursor.close()
                conn.close()
                return jsonify({
                    'status': 'error',
                    'message': 'Clave de licencia no válida'
                }), 400

            # Validar que la licencia esté activa (no revocada)
            if not licencia['activa']:
                cursor.close()
                conn.close()
                return jsonify({
                    'status': 'error',
                    'message': 'Esta licencia ha sido revocada. Contacte al administrador.'
                }), 400

            # CASO 1: Licencia ya activada
            if licencia['activada']:
                # Verificar si es la misma máquina
                if licencia['hardware_id'] == hardware_id:
                    # Misma máquina - actualizar última validación y componentes
                    cursor.execute("""
                        UPDATE licencias
                        SET ultima_validacion = NOW(),
                            hw_mac_address = %s,
                            hw_hostname = %s,
                            hw_os_info = %s,
                            hw_processor = %s,
                            hw_motherboard_uuid = %s,
                            hw_components_updated_at = NOW()
                        WHERE id = %s
                    """, (
                        hw_componentes.get('mac_address'),
                        hw_componentes.get('hostname'),
                        hw_componentes.get('os_info'),
                        hw_componentes.get('processor'),
                        hw_componentes.get('motherboard_uuid'),
                        licencia['id']
                    ))
                    conn.commit()

                    # Registrar en log
                    cursor.execute("""
                        INSERT INTO validaciones_log (licencia_id, hardware_id, exitosa, ip_address, mensaje)
                        VALUES (%s, %s, TRUE, %s, 'Reactivación en misma máquina')
                    """, (licencia['id'], hardware_id, ip_address))
                    conn.commit()

                    cursor.close()
                    conn.close()

                    return jsonify({
                        'status': 'ok',
                        'message': 'Licencia reactivada exitosamente',
                        'licencia': {
                            'clave': licencia['clave'],
                            'nombre_maquina': licencia['nombre_maquina'],
                            'fecha_activacion': licencia['fecha_activacion'].isoformat() if licencia['fecha_activacion'] else None
                        }
                    }), 200
                else:
                    # Máquina diferente - rechazar
                    # Registrar intento fallido
                    cursor.execute("""
                        INSERT INTO validaciones_log (licencia_id, hardware_id, exitosa, ip_address, mensaje)
                        VALUES (%s, %s, FALSE, %s, 'Intento de activación en máquina diferente')
                    """, (licencia['id'], hardware_id, ip_address))
                    conn.commit()

                    cursor.close()
                    conn.close()

                    return jsonify({
                        'status': 'error',
                        'message': f'Esta clave ya está activada en otra máquina: {licencia["nombre_maquina"]}'
                    }), 400

            # CASO 2: Licencia disponible - activar
            cursor.execute("""
                UPDATE licencias
                SET
                    activada = TRUE,
                    hardware_id = %s,
                    nombre_maquina = %s,
                    usuario_sistema = %s,
                    fecha_activacion = NOW(),
                    ultima_validacion = NOW(),
                    ip_activacion = %s,
                    hw_mac_address = %s,
                    hw_hostname = %s,
                    hw_os_info = %s,
                    hw_processor = %s,
                    hw_motherboard_uuid = %s,
                    hw_components_updated_at = NOW()
                WHERE id = %s
            """, (
                hardware_id,
                nombre_maquina,
                usuario_sistema,
                ip_address,
                hw_componentes.get('mac_address'),
                hw_componentes.get('hostname'),
                hw_componentes.get('os_info'),
                hw_componentes.get('processor'),
                hw_componentes.get('motherboard_uuid'),
                licencia['id']
            ))

            conn.commit()

            # Registrar en log
            cursor.execute("""
                INSERT INTO validaciones_log (licencia_id, hardware_id, exitosa, ip_address, mensaje)
                VALUES (%s, %s, TRUE, %s, 'Activación exitosa')
            """, (licencia['id'], hardware_id, ip_address))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({
                'status': 'ok',
                'message': 'Licencia activada exitosamente',
                'licencia': {
                    'clave': clave,
                    'nombre_maquina': nombre_maquina,
                    'fecha_activacion': datetime.now().isoformat()
                }
            }), 200

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error del servidor: {str(e)}'
            }), 500


    @app.route('/licencias/validar', methods=['POST'])
    def validar_licencia():
        """
        Valida que una licencia siga activa para esta máquina

        Body JSON:
        {
            "clave": "DIDI-XXXX-XXXX-XXXX",
            "hardware_id": "HW-XXXXXXXX-..."
        }

        Respuestas:
        200: Licencia válida
        400: Licencia inválida/revocada/vinculada a otra máquina
        500: Error del servidor
        """
        try:
            data = request.get_json()
            clave = data.get('clave', '').strip().upper()
            hardware_id = data.get('hardware_id', '').strip()
            ip_address = request.remote_addr

            if not clave or not hardware_id:
                return jsonify({
                    'status': 'error',
                    'message': 'Clave y hardware_id son requeridos'
                }), 400

            # Conectar a base de datos
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Buscar la licencia
            cursor.execute("""
                SELECT * FROM licencias
                WHERE clave = %s
            """, (clave,))

            licencia = cursor.fetchone()

            # Validar que exista
            if not licencia:
                cursor.close()
                conn.close()
                return jsonify({
                    'status': 'error',
                    'message': 'Licencia no encontrada'
                }), 400

            # Validar que esté activa (no revocada)
            if not licencia['activa']:
                # Registrar intento
                cursor.execute("""
                    INSERT INTO validaciones_log (licencia_id, hardware_id, exitosa, ip_address, mensaje)
                    VALUES (%s, %s, FALSE, %s, 'Licencia revocada')
                """, (licencia['id'], hardware_id, ip_address))
                conn.commit()

                cursor.close()
                conn.close()

                return jsonify({
                    'status': 'error',
                    'message': 'Licencia revocada. Contacte al administrador.'
                }), 400

            # Validar que esté activada
            if not licencia['activada']:
                cursor.close()
                conn.close()
                return jsonify({
                    'status': 'error',
                    'message': 'Licencia no activada. Debe activarla primero.'
                }), 400

            # Validar que el hardware_id coincida
            if licencia['hardware_id'] != hardware_id:
                # Registrar intento sospechoso
                cursor.execute("""
                    INSERT INTO validaciones_log (licencia_id, hardware_id, exitosa, ip_address, mensaje)
                    VALUES (%s, %s, FALSE, %s, 'Hardware ID no coincide')
                """, (licencia['id'], hardware_id, ip_address))
                conn.commit()

                cursor.close()
                conn.close()

                return jsonify({
                    'status': 'error',
                    'message': 'Esta licencia está vinculada a otra máquina'
                }), 400

            # TODO OK - actualizar última validación
            cursor.execute("""
                UPDATE licencias
                SET ultima_validacion = NOW()
                WHERE id = %s
            """, (licencia['id'],))
            conn.commit()

            # Registrar validación exitosa
            cursor.execute("""
                INSERT INTO validaciones_log (licencia_id, hardware_id, exitosa, ip_address, mensaje)
                VALUES (%s, %s, TRUE, %s, 'Validación exitosa')
            """, (licencia['id'], hardware_id, ip_address))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({
                'status': 'ok',
                'message': 'Licencia válida',
                'licencia': {
                    'clave': licencia['clave'],
                    'nombre_maquina': licencia['nombre_maquina'],
                    'fecha_activacion': licencia['fecha_activacion'].isoformat() if licencia['fecha_activacion'] else None,
                    'ultima_validacion': datetime.now().isoformat()
                }
            }), 200

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error del servidor: {str(e)}'
            }), 500


    @app.route('/licencias/info', methods=['GET'])
    def info_licencia():
        """
        Obtiene información de una licencia por clave

        Query params:
        ?clave=DIDI-XXXX-XXXX-XXXX

        Respuestas:
        200: Info de la licencia
        400: Licencia no encontrada
        500: Error del servidor
        """
        try:
            clave = request.args.get('clave', '').strip().upper()

            if not clave:
                return jsonify({
                    'status': 'error',
                    'message': 'Parámetro clave es requerido'
                }), 400

            # Conectar a base de datos
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Buscar la licencia
            cursor.execute("""
                SELECT
                    clave,
                    cliente_nombre,
                    activada,
                    activa,
                    nombre_maquina,
                    usuario_sistema,
                    fecha_activacion,
                    ultima_validacion
                FROM licencias
                WHERE clave = %s
            """, (clave,))

            licencia = cursor.fetchone()
            cursor.close()
            conn.close()

            if not licencia:
                return jsonify({
                    'status': 'error',
                    'message': 'Licencia no encontrada'
                }), 400

            return jsonify({
                'status': 'ok',
                'licencia': {
                    'clave': licencia['clave'],
                    'cliente': licencia['cliente_nombre'],
                    'activada': bool(licencia['activada']),
                    'activa': bool(licencia['activa']),
                    'nombre_maquina': licencia['nombre_maquina'],
                    'usuario_sistema': licencia['usuario_sistema'],
                    'fecha_activacion': licencia['fecha_activacion'].isoformat() if licencia['fecha_activacion'] else None,
                    'ultima_validacion': licencia['ultima_validacion'].isoformat() if licencia['ultima_validacion'] else None
                }
            }), 200

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error del servidor: {str(e)}'
            }), 500
