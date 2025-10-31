"""
Script para crear usuarios del sistema Bot Didi
Permite crear usuarios admin y operadores desde la línea de comandos
"""
import getpass
from backend.models import Usuario
from backend.auth_utils import hash_password


def crear_usuario_interactivo():
    """Crea un usuario de forma interactiva"""
    print("=" * 60)
    print("CREADOR DE USUARIOS - BOT DIDI")
    print("=" * 60)
    print()

    # Solicitar datos
    print("Ingrese los datos del nuevo usuario:")
    print()

    username = input("Username (ej: jperez): ").strip()
    if not username:
        print("\nError: El username es obligatorio")
        return False

    email = input("Email (ej: jperez@empresa.com): ").strip()
    if not email:
        print("\nError: El email es obligatorio")
        return False

    nombre_completo = input("Nombre completo (opcional): ").strip()
    if not nombre_completo:
        nombre_completo = None

    # Seleccionar rol
    print("\nSeleccione el rol:")
    print("1. Operador (usuario normal)")
    print("2. Admin (puede crear otros usuarios)")
    rol_opcion = input("Opción (1 o 2): ").strip()

    if rol_opcion == "1":
        rol = "operador"
    elif rol_opcion == "2":
        rol = "admin"
    else:
        print("\nError: Opción inválida")
        return False

    # Solicitar contraseña
    print("\nIngrese la contraseña (no se mostrará al escribir):")
    password = getpass.getpass("Contraseña: ")

    if len(password) < 6:
        print("\nError: La contraseña debe tener al menos 6 caracteres")
        return False

    password_confirm = getpass.getpass("Confirmar contraseña: ")

    if password != password_confirm:
        print("\nError: Las contraseñas no coinciden")
        return False

    # Confirmar datos
    print("\n" + "=" * 60)
    print("CONFIRMAR DATOS:")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Nombre: {nombre_completo or 'N/A'}")
    print(f"Rol: {rol.upper()}")
    print("=" * 60)

    confirmar = input("\n¿Crear usuario con estos datos? (s/n): ").strip().lower()

    if confirmar != 's':
        print("\nOperación cancelada")
        return False

    # Crear usuario
    try:
        print("\nCreando usuario...")
        password_hash = hash_password(password)
        user_id = Usuario.crear(username, email, password_hash, nombre_completo, rol)

        print("\n" + "=" * 60)
        print("✓ USUARIO CREADO EXITOSAMENTE")
        print("=" * 60)
        print(f"ID: {user_id}")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Rol: {rol.upper()}")
        print("=" * 60)
        print()
        return True

    except ValueError as e:
        print(f"\n✗ Error: {str(e)}")
        return False
    except Exception as e:
        print(f"\n✗ Error inesperado: {str(e)}")
        return False


def listar_usuarios():
    """Lista todos los usuarios del sistema"""
    try:
        print("\n" + "=" * 80)
        print("USUARIOS DEL SISTEMA")
        print("=" * 80)

        usuarios = Usuario.listar_todos()

        if not usuarios:
            print("\nNo hay usuarios registrados en el sistema")
            print()
            return

        print(f"\n{'ID':<5} {'USERNAME':<15} {'EMAIL':<30} {'ROL':<10} {'ACTIVO':<8}")
        print("-" * 80)

        for user in usuarios:
            activo = "SÍ" if user.activo else "NO"
            print(f"{user.id:<5} {user.username:<15} {user.email:<30} {user.rol:<10} {activo:<8}")

        print("-" * 80)
        print(f"\nTotal de usuarios: {len(usuarios)}")
        print()

    except Exception as e:
        print(f"\n✗ Error al listar usuarios: {str(e)}")


def menu_principal():
    """Menú principal del script"""
    while True:
        print("\n" + "=" * 60)
        print("ADMINISTRACIÓN DE USUARIOS - BOT DIDI")
        print("=" * 60)
        print("\n1. Crear nuevo usuario")
        print("2. Listar usuarios existentes")
        print("3. Salir")
        print()

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            crear_usuario_interactivo()
        elif opcion == "2":
            listar_usuarios()
        elif opcion == "3":
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
        print(f"\n✗ Error fatal: {str(e)}")
