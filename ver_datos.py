import pymysql
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_CONFIG = {
    'host': 'datenbanken.aloia.dev',
    'port': 3306,
    'user': 'aloiaMariaDB',
    'password': 'aloiaMariaDB-17.59*2025!',
    'database': 'DidiMonitoreo',
    'charset': 'utf8mb4'
}

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("=== Datos en la base de datos ===\n")
cursor.execute("SELECT * FROM bot_ejecuciones ORDER BY fecha DESC")
rows = cursor.fetchall()

if rows:
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Fecha: {row[1]}")
        print(f"Clientes procesados: {row[2]}")
        print(f"Created at: {row[3]}")
        print("-" * 40)
else:
    print("No hay datos")

cursor.close()
conn.close()
