"""
Entry point para desplegar el backend de forma standalone.
Reutiliza la misma app que la version de escritorio.

Uso:
    # Desarrollo local
    python backend/deploy.py

    # Produccion con gunicorn
    gunicorn backend.deploy:app --bind 0.0.0.0:5005 --workers 4

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
    port = int(os.environ.get('PORT', 5005))

    print("=" * 60)
    print("  BACKEND BOT DIDI - Modo Servidor")
    print("=" * 60)
    print(f"  Host: 0.0.0.0:{port}")
    print("  CORS: habilitado")
    print("=" * 60)

    from waitress import serve
    logging.getLogger('waitress').setLevel(logging.ERROR)
    serve(app, host='0.0.0.0', port=port, threads=4)
