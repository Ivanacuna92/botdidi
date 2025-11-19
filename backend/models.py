"""
Modelos de base de datos para el sistema de autenticación
"""
from datetime import datetime
import pymysql
from config.settings import DB_CONFIG


class Usuario:
    """Modelo para representar un usuario del sistema"""

    def __init__(self, id=None, username=None, email=None, password_hash=None,
                 nombre_completo=None, rol='operador', activo=True,
                 fecha_creacion=None, ultimo_login=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.nombre_completo = nombre_completo
        self.rol = rol
        self.activo = activo
        self.fecha_creacion = fecha_creacion
        self.ultimo_login = ultimo_login

    @staticmethod
    def obtener_por_username(username):
        """Obtiene un usuario por su username"""
        # Agregar timeout de conexión
        db_config_with_timeout = {**DB_CONFIG, 'connect_timeout': 5}
        conn = pymysql.connect(**db_config_with_timeout)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT id, username, email, password_hash, nombre_completo,
                   rol, activo, fecha_creacion, ultimo_login
            FROM usuarios
            WHERE username = %s
        """, (username,))

        resultado = cursor.fetchone()
        cursor.close()
        conn.close()

        if resultado:
            return Usuario(**resultado)
        return None

    @staticmethod
    def obtener_por_id(user_id):
        """Obtiene un usuario por su ID"""
        db_config_with_timeout = {**DB_CONFIG, 'connect_timeout': 5}
        conn = pymysql.connect(**db_config_with_timeout)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT id, username, email, password_hash, nombre_completo,
                   rol, activo, fecha_creacion, ultimo_login
            FROM usuarios
            WHERE id = %s
        """, (user_id,))

        resultado = cursor.fetchone()
        cursor.close()
        conn.close()

        if resultado:
            return Usuario(**resultado)
        return None

    @staticmethod
    def crear(username, email, password_hash, nombre_completo=None, rol='operador'):
        """Crea un nuevo usuario en la base de datos"""
        db_config_with_timeout = {**DB_CONFIG, 'connect_timeout': 5}
        conn = pymysql.connect(**db_config_with_timeout)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO usuarios (username, email, password_hash, nombre_completo, rol)
                VALUES (%s, %s, %s, %s, %s)
            """, (username, email, password_hash, nombre_completo, rol))

            user_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()

            return user_id
        except pymysql.IntegrityError as e:
            conn.rollback()
            cursor.close()
            conn.close()
            raise ValueError(f"Usuario o email ya existe: {str(e)}")

    def actualizar_ultimo_login(self):
        """Actualiza la fecha de último login del usuario"""
        db_config_with_timeout = {**DB_CONFIG, 'connect_timeout': 5}
        conn = pymysql.connect(**db_config_with_timeout)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE usuarios
            SET ultimo_login = NOW()
            WHERE id = %s
        """, (self.id,))

        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def listar_todos():
        """Lista todos los usuarios del sistema"""
        db_config_with_timeout = {**DB_CONFIG, 'connect_timeout': 5}
        conn = pymysql.connect(**db_config_with_timeout)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT id, username, email, nombre_completo, rol, activo,
                   fecha_creacion, ultimo_login
            FROM usuarios
            ORDER BY fecha_creacion DESC
        """)

        resultados = cursor.fetchall()
        cursor.close()
        conn.close()

        return [Usuario(**r) for r in resultados]

    def to_dict(self):
        """Convierte el usuario a diccionario (sin password_hash)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nombre_completo': self.nombre_completo,
            'rol': self.rol,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'ultimo_login': self.ultimo_login.isoformat() if self.ultimo_login else None
        }


class Sesion:
    """Modelo para manejar sesiones de usuario"""

    @staticmethod
    def crear(user_id, token_hash, fecha_expiracion):
        """Crea una nueva sesión"""
        db_config_with_timeout = {**DB_CONFIG, 'connect_timeout': 5}
        conn = pymysql.connect(**db_config_with_timeout)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sesiones (user_id, token_hash, fecha_expiracion)
            VALUES (%s, %s, %s)
        """, (user_id, token_hash, fecha_expiracion))

        sesion_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return sesion_id

    @staticmethod
    def validar(token_hash):
        """Valida si una sesión es activa y no ha expirado"""
        db_config_with_timeout = {**DB_CONFIG, 'connect_timeout': 5}
        conn = pymysql.connect(**db_config_with_timeout)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT user_id, fecha_expiracion
            FROM sesiones
            WHERE token_hash = %s AND activa = TRUE
        """, (token_hash,))

        resultado = cursor.fetchone()
        cursor.close()
        conn.close()

        if resultado:
            # Verificar si no ha expirado
            if resultado['fecha_expiracion'] > datetime.now():
                return resultado['user_id']

        return None

    @staticmethod
    def invalidar(token_hash):
        """Invalida una sesión (logout)"""
        db_config_with_timeout = {**DB_CONFIG, 'connect_timeout': 5}
        conn = pymysql.connect(**db_config_with_timeout)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE sesiones
            SET activa = FALSE
            WHERE token_hash = %s
        """, (token_hash,))

        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def invalidar_todas_del_usuario(user_id):
        """Invalida todas las sesiones activas de un usuario"""
        db_config_with_timeout = {**DB_CONFIG, 'connect_timeout': 5}
        conn = pymysql.connect(**db_config_with_timeout)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE sesiones
            SET activa = FALSE
            WHERE user_id = %s AND activa = TRUE
        """, (user_id,))

        filas_afectadas = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        return filas_afectadas
