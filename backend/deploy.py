"""
Entry point para desplegar el backend de forma standalone.
Reutiliza la misma app que la version de escritorio.

Uso:
    # Desarrollo local
    python backend/deploy.py

    # Produccion con gunicorn
    gunicorn backend.deploy:app --bind 0.0.0.0:5000 --workers 4

Requiere:
    pip install flask flask-cors pymysql bcrypt pyjwt waitress
"""
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.flask_server import crear_app

app = crear_app()

if __name__ == '__main__':
    print("=" * 60)
    print("  BACKEND BOT DIDI - Modo Servidor")
    print("=" * 60)
    print("  Host: 0.0.0.0:5000")
    print("  CORS: habilitado")
    print("=" * 60)

    from waitress import serve
    logging.getLogger('waitress').setLevel(logging.ERROR)
    serve(app, host='0.0.0.0', port=5000, threads=4)
