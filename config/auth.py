"""
Configuración de autenticación y JWT
"""
import os
import secrets

# Clave secreta para JWT
# En produccion: definir variable de entorno JWT_SECRET_KEY
# Si no existe, genera una aleatoria (se pierde al reiniciar)
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)

# Tiempo de expiración del token (en horas)
JWT_EXPIRATION_HOURS = 24

# Algoritmo de encriptación para JWT
JWT_ALGORITHM = 'HS256'

# Configuración de sesiones
SESSION_EXPIRATION_DAYS = 7
