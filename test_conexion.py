import pymysql
import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=== Test de Conexion a Base de Datos ===\n")

DB_CONFIG = {
    'host': 'datenbanken.aloia.dev',
    'port': 3306,
    'user': 'aloiaMariaDB',
    'password': 'aloiaMariaDB-17.59*2025!',
    'database': 'DidiMonitoreo',
    'charset': 'utf8mb4'
}

try:
    print("1. Intentando conectar a la base de datos...")
    conn = pymysql.connect(**DB_CONFIG)
    print("✓ Conexión exitosa!\n")

    cursor = conn.cursor()

    # Verificar si la tabla existe
    print("2. Verificando si existe la tabla 'bot_ejecuciones'...")
    cursor.execute("SHOW TABLES LIKE 'bot_ejecuciones'")
    result = cursor.fetchone()

    if result:
        print("✓ La tabla 'bot_ejecuciones' existe\n")

        # Ver estructura de la tabla
        print("3. Estructura de la tabla:")
        cursor.execute("DESCRIBE bot_ejecuciones")
        for row in cursor.fetchall():
            print(f"   - {row[0]}: {row[1]}")

        # Ver datos existentes
        print("\n4. Datos existentes en la tabla:")
        cursor.execute("SELECT * FROM bot_ejecuciones ORDER BY fecha DESC LIMIT 5")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"   ID: {row[0]}, Fecha: {row[1]}, Clientes: {row[2]}, Created: {row[3]}")
        else:
            print("   (No hay datos todavía)")

    else:
        print("✗ ERROR: La tabla 'bot_ejecuciones' NO EXISTE")
        print("\n⚠ SOLUCIÓN:")
        print("   1. Ve a: https://datenbanken.aloia.dev")
        print("   2. Loguéate con tus credenciales")
        print("   3. Selecciona la base de datos 'DidiMonitoreo'")
        print("   4. Ve a la pestaña 'SQL'")
        print("   5. Copia y pega el contenido de 'tabla_conteo.sql'")
        print("   6. Haz click en 'Ejecutar'")

    cursor.close()
    conn.close()

except pymysql.err.OperationalError as e:
    print(f"✗ ERROR DE CONEXIÓN: {e}")
    print("\nVerifica:")
    print("  - Host: datenbanken.aloia.dev")
    print("  - Puerto: 3306")
    print("  - Usuario: aloiaMariaDB")
    print("  - Base de datos: DidiMonitoreo")

except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test completado ===")
