"""
Configuración de autenticación y JWT
"""
import secrets

# Clave secreta para JWT (en producción debería estar en variable de entorno)
# Esta clave se genera automáticamente, pero puedes cambiarla manualmente
JWT_SECRET_KEY = secrets.token_hex(32)  # Genera una clave aleatoria de 64 caracteres

# Tiempo de expiración del token (en horas)
JWT_EXPIRATION_HOURS = 24

# Algoritmo de encriptación para JWT
JWT_ALGORITHM = 'HS256'

# Configuración de sesiones
SESSION_EXPIRATION_DAYS = 7
