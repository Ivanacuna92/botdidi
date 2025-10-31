"""
Utilidades para el sistema de licencias
- Generación de Hardware ID único
- Generación de claves de licencia
- Encriptación de tokens locales
"""
import uuid
import platform
import hashlib
import secrets
import string
import json
import os
from cryptography.fernet import Fernet
from datetime import datetime, timedelta


# ============================================================================
# HARDWARE ID - Identificador único de la máquina
# ============================================================================

def generar_hardware_id():
    """
    Genera un ID único basado en el hardware de la máquina
    Este ID es SIEMPRE EL MISMO para la misma máquina física
    """
    componentes = []

    # 1. MAC Address de la interfaz de red (determinístico)
    try:
        mac = uuid.getnode()
        mac_hex = ':'.join(['{:02x}'.format((mac >> elements) & 0xff)
                           for elements in range(0, 2*6, 2)][::-1])
        componentes.append(f"MAC:{mac_hex}")
    except:
        componentes.append("MAC:unknown")

    # 2. Nombre de la máquina (determinístico)
    try:
        hostname = platform.node()
        componentes.append(f"HOST:{hostname}")
    except:
        componentes.append("HOST:unknown")

    # 3. Información del sistema operativo (determinístico)
    try:
        sistema = f"{platform.system()}-{platform.release()}"
        componentes.append(f"OS:{sistema}")
    except:
        componentes.append("OS:unknown")

    # 4. Arquitectura del procesador (determinístico)
    try:
        procesador = platform.machine()
        componentes.append(f"PROC:{procesador}")
    except:
        componentes.append("PROC:unknown")

    # 5. ID de la máquina de Windows (si está disponible)
    try:
        import subprocess
        # En Windows, usar wmic para obtener UUID del motherboard
        if platform.system() == 'Windows':
            result = subprocess.run(['wmic', 'csproduct', 'get', 'UUID'],
                                  capture_output=True, text=True, timeout=5)
            uuid_str = result.stdout.strip().split('\n')[-1].strip()
            if uuid_str and uuid_str != 'UUID':
                componentes.append(f"WMIC:{uuid_str}")
    except:
        pass

    # Combinar todos los componentes (siempre en el mismo orden)
    data = "|".join(componentes)

    # Generar hash SHA256 (siempre el mismo para los mismos componentes)
    hash_obj = hashlib.sha256(data.encode('utf-8'))
    hardware_hash = hash_obj.hexdigest()[:32]  # Primeros 32 caracteres

    # Formatear como HW-XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX
    formatted = f"HW-{hardware_hash[:8]}-{hardware_hash[8:16]}-{hardware_hash[16:24]}-{hardware_hash[24:32]}"

    return formatted.upper()


def obtener_info_maquina():
    """
    Obtiene información adicional de la máquina para registro
    """
    try:
        return {
            'nombre_maquina': platform.node(),
            'usuario_sistema': os.getlogin() if hasattr(os, 'getlogin') else 'unknown',
            'sistema_operativo': f"{platform.system()} {platform.release()}",
            'arquitectura': platform.machine()
        }
    except:
        return {
            'nombre_maquina': 'unknown',
            'usuario_sistema': 'unknown',
            'sistema_operativo': 'unknown',
            'arquitectura': 'unknown'
        }


# ============================================================================
# GENERACIÓN DE CLAVES DE LICENCIA
# ============================================================================

def generar_clave_licencia():
    """
    Genera una clave de licencia única en formato DIDI-XXXX-XXXX-XXXX
    Usa caracteres seguros (sin O/0, I/1/l para evitar confusión)
    """
    # Caracteres permitidos (sin ambiguos)
    caracteres = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')

    # Generar 3 bloques de 4 caracteres
    bloques = []
    for _ in range(3):
        bloque = ''.join(secrets.choice(caracteres) for _ in range(4))
        bloques.append(bloque)

    # Formatear como DIDI-XXXX-XXXX-XXXX
    clave = f"DIDI-{'-'.join(bloques)}"

    return clave


# ============================================================================
# TOKEN LOCAL (Archivo encriptado para no pedir clave cada vez)
# ============================================================================

def obtener_clave_encriptacion():
    """
    Genera una clave de encriptación basada en el hardware
    Así el token solo funciona en esta máquina específica
    """
    hardware_id = generar_hardware_id()
    # Crear clave Fernet válida basada en el hardware ID
    # Usar base64 para que sea compatible con Fernet
    import base64
    clave_base = hashlib.sha256(hardware_id.encode()).digest()
    clave_fernet = base64.urlsafe_b64encode(clave_base)
    return Fernet(clave_fernet)


# Archivo donde se guarda el token local
TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.license_token')


def guardar_token_local(clave_licencia, hardware_id):
    """
    Guarda el token de activación localmente (encriptado)
    Para no pedir la clave cada vez que abren el bot
    """
    try:
        # Crear datos del token
        token_data = {
            'clave': clave_licencia,
            'hardware_id': hardware_id,
            'fecha_creacion': datetime.now().isoformat(),
            'expira': (datetime.now() + timedelta(days=30)).isoformat()  # Token válido 30 días
        }

        # Convertir a JSON
        json_data = json.dumps(token_data)

        # Encriptar usando clave basada en hardware
        fernet = obtener_clave_encriptacion()
        token_encriptado = fernet.encrypt(json_data.encode('utf-8'))

        # Guardar en archivo
        with open(TOKEN_FILE, 'wb') as f:
            f.write(token_encriptado)

        return True
    except Exception as e:
        print(f"Error guardando token: {e}")
        return False


def leer_token_local():
    """
    Lee el token de activación local
    Retorna: (clave_licencia, hardware_id, fecha_expiracion) o None si no existe/inválido
    """
    try:
        # Verificar si existe el archivo
        if not os.path.exists(TOKEN_FILE):
            return None

        # Leer archivo encriptado
        with open(TOKEN_FILE, 'rb') as f:
            token_encriptado = f.read()

        # Desencriptar usando clave basada en hardware
        fernet = obtener_clave_encriptacion()
        json_data = fernet.decrypt(token_encriptado).decode('utf-8')
        token_data = json.loads(json_data)

        # Verificar expiración
        expira = datetime.fromisoformat(token_data['expira'])
        if datetime.now() > expira:
            print("Token local expirado")
            return None

        # Verificar que el hardware ID coincida
        hardware_actual = generar_hardware_id()
        if token_data['hardware_id'] != hardware_actual:
            print("Token no corresponde a esta máquina")
            return None

        return (
            token_data['clave'],
            token_data['hardware_id'],
            expira
        )

    except Exception as e:
        import traceback
        print(f"Error leyendo token: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        traceback.print_exc()
        return None


def eliminar_token_local():
    """Elimina el token local (útil para desactivar)"""
    try:
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        return True
    except:
        return False


# ============================================================================
# VALIDACIÓN DE FORMATO
# ============================================================================

def validar_formato_clave(clave):
    """
    Valida que una clave tenga el formato correcto: DIDI-XXXX-XXXX-XXXX
    """
    import re
    patron = r'^DIDI-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$'
    return bool(re.match(patron, clave))


# ============================================================================
# UTILIDADES DE DEPURACIÓN
# ============================================================================

if __name__ == "__main__":
    """Pruebas rápidas"""
    print("=" * 60)
    print("PRUEBAS DE UTILIDADES DE LICENCIA")
    print("=" * 60)

    # Test Hardware ID
    print("\n1. Hardware ID de esta máquina:")
    hw_id = generar_hardware_id()
    print(f"   {hw_id}")

    # Test Info de máquina
    print("\n2. Información de la máquina:")
    info = obtener_info_maquina()
    for k, v in info.items():
        print(f"   {k}: {v}")

    # Test generación de claves
    print("\n3. Generar 5 claves de ejemplo:")
    for i in range(5):
        clave = generar_clave_licencia()
        print(f"   {i+1}. {clave}")

    # Test token local
    print("\n4. Guardar y leer token local:")
    clave_test = generar_clave_licencia()
    print(f"   Guardando clave: {clave_test}")
    guardar_token_local(clave_test, hw_id)
    print(f"   Token guardado en: {TOKEN_FILE}")

    token_leido = leer_token_local()
    if token_leido:
        print(f"   ✓ Token leído correctamente")
        print(f"   Clave: {token_leido[0]}")
        print(f"   Hardware ID: {token_leido[1]}")
        print(f"   Expira: {token_leido[2]}")
    else:
        print(f"   ✗ No se pudo leer el token")

    print("\n" + "=" * 60)
