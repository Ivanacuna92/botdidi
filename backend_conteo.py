from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app)

# Configuración de base de datos
DB_CONFIG = {
    'host': 'datenbanken.aloia.dev',
    'port': 3306,
    'user': 'aloiaMariaDB',
    'password': 'aloiaMariaDB-17.59*2025!',
    'database': 'DidiMonitoreo',
    'charset': 'utf8mb4'
}

def get_db():
    """Obtiene conexión a la base de datos"""
    return pymysql.connect(**DB_CONFIG)

@app.route('/', methods=['GET'])
def inicio():
    """Página de inicio"""
    return jsonify({
        'mensaje': 'Backend Bot Didi - Registro de clientes procesados',
        'status': 'OK',
        'endpoints': {
            'POST /registrar': 'Registrar clientes procesados (body: {"clientes": numero})',
            'POST /registrar_cliente': 'Registrar cliente individual (body: {"nombre": "...", "estado": "exitoso|error"})',
            'GET /estadisticas': 'Obtener estadísticas',
            'GET /hoy': 'Obtener clientes procesados hoy',
            'GET /clientes_hoy': 'Obtener lista de clientes procesados hoy'
        }
    })

@app.route('/registrar', methods=['POST'])
def registrar_clientes():
    """Registra cuántos clientes fueron procesados exitosamente"""
    data = request.json

    if not data or 'clientes' not in data:
        return jsonify({'error': 'Falta parámetro: clientes'}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()

        sql = """
            INSERT INTO bot_ejecuciones (fecha, clientes_procesados)
            VALUES (CURDATE(), %s)
            ON DUPLICATE KEY UPDATE clientes_procesados = clientes_procesados + %s
        """

        clientes = int(data['clientes'])
        cursor.execute(sql, (clientes, clientes))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'{clientes} clientes registrados para hoy'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/registrar_cliente', methods=['POST'])
def registrar_cliente_individual():
    """Registra un cliente procesado individualmente con su nombre"""
    data = request.json

    if not data or 'nombre' not in data:
        return jsonify({'error': 'Falta parámetro: nombre'}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()

        sql = """
            INSERT INTO bot_clientes_procesados (nombre_cliente, estado)
            VALUES (%s, %s)
        """

        nombre = data['nombre']
        estado = data.get('estado', 'exitoso')  # Por defecto 'exitoso'
        cursor.execute(sql, (nombre, estado))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Cliente {nombre} registrado como {estado}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/hoy', methods=['GET'])
def obtener_hoy():
    """Obtiene cuántos clientes se procesaron hoy"""
    try:
        conn = get_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql = "SELECT * FROM bot_ejecuciones WHERE fecha = CURDATE()"
        cursor.execute(sql)
        resultado = cursor.fetchone()

        cursor.close()
        conn.close()

        if resultado:
            return jsonify(resultado)
        else:
            return jsonify({'clientes_procesados': 0, 'mensaje': 'No hay registros para hoy'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/estadisticas', methods=['GET'])
def obtener_estadisticas():
    """Obtiene estadísticas de los últimos días"""
    dias = request.args.get('dias', 7, type=int)

    try:
        conn = get_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT fecha, clientes_procesados, created_at
            FROM bot_ejecuciones
            WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY fecha DESC
        """
        cursor.execute(sql, (dias,))
        resultado = cursor.fetchall()

        # Calcular totales
        total_clientes = sum(r['clientes_procesados'] for r in resultado)
        promedio = total_clientes / len(resultado) if resultado else 0

        cursor.close()
        conn.close()

        return jsonify({
            'registros': resultado,
            'total_clientes': total_clientes,
            'promedio_diario': round(promedio, 2),
            'dias_analizados': len(resultado)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clientes_hoy', methods=['GET'])
def obtener_clientes_hoy():
    """Obtiene la lista de clientes procesados hoy"""
    try:
        conn = get_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT id, nombre_cliente, estado, fecha_procesado
            FROM bot_clientes_procesados
            WHERE DATE(fecha_procesado) = CURDATE()
            ORDER BY fecha_procesado DESC
        """
        cursor.execute(sql)
        clientes = cursor.fetchall()

        # Contar por estado
        exitosos = sum(1 for c in clientes if c['estado'] == 'exitoso')
        errores = sum(1 for c in clientes if c['estado'] == 'error')

        cursor.close()
        conn.close()

        return jsonify({
            'clientes': clientes,
            'total': len(clientes),
            'exitosos': exitosos,
            'errores': errores
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
