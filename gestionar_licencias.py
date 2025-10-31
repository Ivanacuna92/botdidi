"""
Script para gestionar licencias del Bot Didi
Permite ver, revocar, desvincular y reactivar licencias
"""
import pymysql
from datetime import datetime
from config.settings import DB_CONFIG


def listar_licencias():
    """Lista todas las licencias con su estado"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT
                id,
                clave,
                cliente_nombre,
                activada,
                activa,
                nombre_maquina,
                usuario_sistema,
                DATE(fecha_creacion) as fecha_creacion,
                DATE(fecha_activacion) as fecha_activacion,
                DATE(ultima_validacion) as ultima_validacion,
                DATEDIFF(NOW(), ultima_validacion) as dias_sin_validar
            FROM licencias
            ORDER BY fecha_creacion DESC
        """)

        licencias = cursor.fetchall()
        cursor.close()
        conn.close()

        if not licencias:
            print("\nNo hay licencias en el sistema")
            return

        print("\n" + "=" * 120)
        print(f"{'ID':<5} {'CLAVE':<22} {'CLIENTE':<20} {'ESTADO':<12} {'MÁQUINA':<20} {'ACTIVACIÓN':<12} {'VALIDACIÓN':<12}")
        print("=" * 120)

        for lic in licencias:
            # Estado
            if not lic['activa']:
                estado = "REVOCADA"
            elif not lic['activada']:
                estado = "DISPONIBLE"
            else:
                estado = "ACTIVADA"

            # Días sin validar
            dias = lic['dias_sin_validar'] if lic['dias_sin_validar'] else "-"

            print(
                f"{lic['id']:<5} "
                f"{lic['clave']:<22} "
                f"{(lic['cliente_nombre'] or 'N/A')[:20]:<20} "
                f"{estado:<12} "
                f"{(lic['nombre_maquina'] or '-')[:20]:<20} "
                f"{str(lic['fecha_activacion'] or '-'):<12} "
                f"{str(lic['ultima_validacion'] or '-'):<12}"
            )

        print("=" * 120)
        print(f"\nTotal: {len(licencias)} licencia(s)")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def ver_detalle_licencia():
    """Muestra el detalle completo de una licencia"""
    clave = input("\nIngrese la clave de licencia: ").strip().upper()

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT * FROM licencias
            WHERE clave = %s
        """, (clave,))

        licencia = cursor.fetchone()

        if not licencia:
            print("\n✗ Licencia no encontrada")
            cursor.close()
            conn.close()
            return

        # Mostrar detalle
        print("\n" + "=" * 70)
        print(" " * 20 + "DETALLE DE LICENCIA")
        print("=" * 70)
        print(f"ID:                  {licencia['id']}")
        print(f"Clave:               {licencia['clave']}")
        print(f"Cliente:             {licencia['cliente_nombre'] or 'N/A'}")
        print(f"Notas:               {licencia['notas'] or 'N/A'}")
        print()
        print(f"Estado:              {'ACTIVA' if licencia['activa'] else 'REVOCADA'}")
        print(f"Activada:            {'SÍ' if licencia['activada'] else 'NO'}")
        print()
        print(f"Hardware ID:         {licencia['hardware_id'] or 'No vinculada'}")
        print(f"Nombre máquina:      {licencia['nombre_maquina'] or '-'}")
        print(f"Usuario sistema:     {licencia['usuario_sistema'] or '-'}")
        print()
        print(f"Fecha creación:      {licencia['fecha_creacion']}")
        print(f"Fecha activación:    {licencia['fecha_activacion'] or 'No activada'}")
        print(f"Última validación:   {licencia['ultima_validacion'] or 'Nunca'}")
        print(f"IP activación:       {licencia['ip_activacion'] or '-'}")
        print("=" * 70)

        # Ver historial de validaciones
        cursor.execute("""
            SELECT
                fecha_validacion,
                exitosa,
                mensaje,
                ip_address
            FROM validaciones_log
            WHERE licencia_id = %s
            ORDER BY fecha_validacion DESC
            LIMIT 10
        """, (licencia['id'],))

        validaciones = cursor.fetchall()

        if validaciones:
            print("\nÚltimas 10 validaciones:")
            print("-" * 70)
            for val in validaciones:
                estado = "✓" if val['exitosa'] else "✗"
                print(f"  {estado} {val['fecha_validacion']}  -  {val['mensaje']} ({val['ip_address']})")
            print("-" * 70)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n✗ Error: {e}")


def revocar_licencia():
    """Revoca una licencia (la desactiva permanentemente)"""
    clave = input("\nIngrese la clave a revocar: ").strip().upper()

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Verificar que existe
        cursor.execute("SELECT * FROM licencias WHERE clave = %s", (clave,))
        licencia = cursor.fetchone()

        if not licencia:
            print("\n✗ Licencia no encontrada")
            cursor.close()
            conn.close()
            return

        if not licencia['activa']:
            print("\n✗ La licencia ya está revocada")
            cursor.close()
            conn.close()
            return

        # Mostrar info
        print(f"\nLicencia: {clave}")
        print(f"Cliente: {licencia['cliente_nombre'] or 'N/A'}")
        if licencia['activada']:
            print(f"Máquina: {licencia['nombre_maquina']}")

        confirmar = input("\n¿Está seguro de revocar esta licencia? (s/n): ").strip().lower()
        if confirmar != 's':
            print("\nOperación cancelada")
            cursor.close()
            conn.close()
            return

        # Revocar
        cursor.execute("""
            UPDATE licencias
            SET activa = FALSE
            WHERE id = %s
        """, (licencia['id'],))

        conn.commit()
        cursor.close()
        conn.close()

        print("\n✓ Licencia revocada exitosamente")
        print("El usuario ya no podrá usar el bot con esta licencia")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def desvincular_licencia():
    """Desvincula una licencia de su máquina (permite reactivar en otra)"""
    clave = input("\nIngrese la clave a desvincular: ").strip().upper()

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Verificar que existe
        cursor.execute("SELECT * FROM licencias WHERE clave = %s", (clave,))
        licencia = cursor.fetchone()

        if not licencia:
            print("\n✗ Licencia no encontrada")
            cursor.close()
            conn.close()
            return

        if not licencia['activada']:
            print("\n✗ La licencia no está activada (no hay nada que desvincular)")
            cursor.close()
            conn.close()
            return

        # Mostrar info
        print(f"\nLicencia: {clave}")
        print(f"Cliente: {licencia['cliente_nombre'] or 'N/A'}")
        print(f"Máquina vinculada: {licencia['nombre_maquina']}")
        print(f"Hardware ID: {licencia['hardware_id']}")

        print("\n⚠️  ADVERTENCIA:")
        print("Al desvincular, esta licencia podrá activarse en OTRA máquina.")
        print("Use esto solo si el cliente cambió de PC legítimamente.")

        confirmar = input("\n¿Está seguro de desvincular? (s/n): ").strip().lower()
        if confirmar != 's':
            print("\nOperación cancelada")
            cursor.close()
            conn.close()
            return

        # Desvincular
        cursor.execute("""
            UPDATE licencias
            SET
                activada = FALSE,
                hardware_id = NULL,
                nombre_maquina = NULL,
                usuario_sistema = NULL,
                fecha_activacion = NULL,
                ultima_validacion = NULL,
                ip_activacion = NULL
            WHERE id = %s
        """, (licencia['id'],))

        conn.commit()
        cursor.close()
        conn.close()

        print("\n✓ Licencia desvinculada exitosamente")
        print("El cliente puede activarla en una nueva máquina")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def reactivar_licencia():
    """Reactiva una licencia revocada"""
    clave = input("\nIngrese la clave a reactivar: ").strip().upper()

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Verificar que existe
        cursor.execute("SELECT * FROM licencias WHERE clave = %s", (clave,))
        licencia = cursor.fetchone()

        if not licencia:
            print("\n✗ Licencia no encontrada")
            cursor.close()
            conn.close()
            return

        if licencia['activa']:
            print("\n✗ La licencia ya está activa")
            cursor.close()
            conn.close()
            return

        # Confirmar
        print(f"\nLicencia: {clave}")
        print(f"Cliente: {licencia['cliente_nombre'] or 'N/A'}")

        confirmar = input("\n¿Reactivar esta licencia? (s/n): ").strip().lower()
        if confirmar != 's':
            print("\nOperación cancelada")
            cursor.close()
            conn.close()
            return

        # Reactivar
        cursor.execute("""
            UPDATE licencias
            SET activa = TRUE
            WHERE id = %s
        """, (licencia['id'],))

        conn.commit()
        cursor.close()
        conn.close()

        print("\n✓ Licencia reactivada exitosamente")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def menu_principal():
    """Menú principal"""
    while True:
        print("\n" + "=" * 70)
        print(" " * 15 + "GESTIÓN DE LICENCIAS - BOT DIDI")
        print("=" * 70)
        print("\n1. Listar todas las licencias")
        print("2. Ver detalle de una licencia")
        print("3. Revocar licencia (desactivar permanentemente)")
        print("4. Desvincular licencia (permitir reactivar en otra máquina)")
        print("5. Reactivar licencia revocada")
        print("6. Salir")
        print()

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            listar_licencias()
        elif opcion == "2":
            ver_detalle_licencia()
        elif opcion == "3":
            revocar_licencia()
        elif opcion == "4":
            desvincular_licencia()
        elif opcion == "5":
            reactivar_licencia()
        elif opcion == "6":
            print("\n¡Hasta luego!")
            break
        else:
            print("\n✗ Opción inválida")


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario")
    except Exception as e:
        print(f"\n✗ Error fatal: {e}")
