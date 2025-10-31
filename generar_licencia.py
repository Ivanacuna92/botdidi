"""
Script para generar licencias del Bot Didi
Permite generar múltiples claves y guardarlas en la base de datos
"""
import pymysql
from datetime import datetime
from backend.license_utils import generar_clave_licencia
from config.settings import DB_CONFIG


def generar_licencias_interactivo():
    """Genera licencias de forma interactiva"""
    print("=" * 70)
    print(" " * 15 + "GENERADOR DE LICENCIAS - BOT DIDI")
    print("=" * 70)
    print()

    # Solicitar datos
    try:
        cantidad = int(input("Cantidad de licencias a generar: ").strip())
        if cantidad < 1 or cantidad > 100:
            print("\n✗ Error: La cantidad debe estar entre 1 y 100")
            return False
    except ValueError:
        print("\n✗ Error: Debe ingresar un número válido")
        return False

    cliente_nombre = input("Nombre del cliente: ").strip()
    if not cliente_nombre:
        cliente_nombre = "Sin nombre"

    notas = input("Notas (opcional): ").strip()
    if not notas:
        notas = None

    # Confirmar
    print("\n" + "=" * 70)
    print("RESUMEN:")
    print("=" * 70)
    print(f"Cantidad: {cantidad} licencia(s)")
    print(f"Cliente: {cliente_nombre}")
    print(f"Notas: {notas or 'N/A'}")
    print("=" * 70)

    confirmar = input("\n¿Generar licencias? (s/n): ").strip().lower()
    if confirmar != 's':
        print("\nOperación cancelada")
        return False

    # Generar claves
    print(f"\nGenerando {cantidad} clave(s) única(s)...")
    claves_generadas = []

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    intentos_max = cantidad * 10  # Por si hay colisiones
    intentos = 0

    while len(claves_generadas) < cantidad and intentos < intentos_max:
        intentos += 1
        clave = generar_clave_licencia()

        # Verificar que no exista en BD
        cursor.execute("SELECT id FROM licencias WHERE clave = %s", (clave,))
        if cursor.fetchone() is None:
            # Insertar en BD
            try:
                cursor.execute("""
                    INSERT INTO licencias (clave, cliente_nombre, notas)
                    VALUES (%s, %s, %s)
                """, (clave, cliente_nombre, notas))
                conn.commit()
                claves_generadas.append(clave)
            except pymysql.IntegrityError:
                # Clave duplicada (muy raro), intentar otra
                continue

    cursor.close()
    conn.close()

    if len(claves_generadas) < cantidad:
        print(f"\n✗ Advertencia: Solo se pudieron generar {len(claves_generadas)} de {cantidad} licencias")

    # Mostrar claves generadas
    print("\n" + "=" * 70)
    print(" " * 20 + "✓ LICENCIAS GENERADAS")
    print("=" * 70)
    for i, clave in enumerate(claves_generadas, 1):
        print(f"{i:2}. {clave}")
    print("=" * 70)
    print(f"\n✓ {len(claves_generadas)} licencia(s) insertada(s) en la base de datos")

    # Preguntar si quiere guardar en archivo
    guardar = input("\n¿Guardar claves en archivo de texto? (s/n): ").strip().lower()
    if guardar == 's':
        fecha_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        cliente_safe = cliente_nombre.replace(' ', '_').replace('/', '_')
        archivo = f"licencias_{cliente_safe}_{fecha_str}.txt"

        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write(f"LICENCIAS PARA: {cliente_nombre}\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Cantidad: {len(claves_generadas)}\n")
                if notas:
                    f.write(f"Notas: {notas}\n")
                f.write("=" * 70 + "\n\n")

                for i, clave in enumerate(claves_generadas, 1):
                    f.write(f"{i}. {clave}\n")

                f.write("\n" + "=" * 70 + "\n")
                f.write("INSTRUCCIONES:\n")
                f.write("1. Cada clave solo puede activarse en UNA máquina\n")
                f.write("2. Una vez activada, la clave queda vinculada a esa máquina\n")
                f.write("3. La clave puede reactivarse en la MISMA máquina ilimitadas veces\n")
                f.write("4. NO se puede transferir a otra máquina\n")
                f.write("=" * 70 + "\n")

            print(f"\n✓ Archivo guardado: {archivo}")
        except Exception as e:
            print(f"\n✗ Error guardando archivo: {e}")

    print()
    return True


def menu_principal():
    """Menú principal del generador"""
    while True:
        print("\n" + "=" * 70)
        print(" " * 15 + "GENERADOR DE LICENCIAS - BOT DIDI")
        print("=" * 70)
        print("\n1. Generar nuevas licencias")
        print("2. Ver estadísticas de licencias")
        print("3. Salir")
        print()

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            generar_licencias_interactivo()
        elif opcion == "2":
            ver_estadisticas()
        elif opcion == "3":
            print("\n¡Hasta luego!")
            break
        else:
            print("\n✗ Opción inválida")


def ver_estadisticas():
    """Muestra estadísticas de licencias en la base de datos"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Contar licencias
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN activada = TRUE THEN 1 ELSE 0 END) as activadas,
                SUM(CASE WHEN activada = FALSE THEN 1 ELSE 0 END) as disponibles,
                SUM(CASE WHEN activa = FALSE THEN 1 ELSE 0 END) as revocadas
            FROM licencias
        """)

        stats = cursor.fetchone()

        print("\n" + "=" * 70)
        print(" " * 20 + "ESTADÍSTICAS DE LICENCIAS")
        print("=" * 70)
        print(f"Total de licencias:       {stats['total']}")
        print(f"Activadas:                {stats['activadas']}")
        print(f"Disponibles:              {stats['disponibles']}")
        print(f"Revocadas:                {stats['revocadas']}")
        print("=" * 70)

        # Licencias activadas recientemente
        cursor.execute("""
            SELECT clave, nombre_maquina, DATE(fecha_activacion) as fecha
            FROM licencias
            WHERE activada = TRUE
            ORDER BY fecha_activacion DESC
            LIMIT 10
        """)

        recientes = cursor.fetchall()

        if recientes:
            print("\nÚltimas 10 activaciones:")
            print("-" * 70)
            for lic in recientes:
                print(f"  {lic['clave']}  →  {lic['nombre_maquina']}  ({lic['fecha']})")
            print("-" * 70)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n✗ Error obteniendo estadísticas: {e}")


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario")
    except Exception as e:
        print(f"\n✗ Error fatal: {e}")
