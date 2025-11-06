"""
Script de prueba para verificar los componentes de hardware
Ejecutar con: python test_hardware_components.py
"""
from backend.license_utils import generar_hardware_id, obtener_info_maquina

print("=" * 80)
print("PRUEBA DE COMPONENTES DE HARDWARE")
print("=" * 80)

# Generar Hardware ID
print("\n[1] Generando Hardware ID...")
hardware_id, componentes = generar_hardware_id()

print(f"\n✓ Hardware ID: {hardware_id}")

print("\n[2] Componentes individuales:")
print("-" * 80)
print(f"  MAC Address:      {componentes.get('mac_address', 'N/A')}")
print(f"  Hostname:         {componentes.get('hostname', 'N/A')}")
print(f"  OS Info:          {componentes.get('os_info', 'N/A')}")
print(f"  Processor:        {componentes.get('processor', 'N/A')}")
print(f"  Motherboard UUID: {componentes.get('motherboard_uuid', 'N/A')}")

print("\n[3] Información adicional de la máquina:")
print("-" * 80)
info = obtener_info_maquina()
for key, value in info.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 80)
print("PRUEBA COMPLETADA")
print("=" * 80)

# Mostrar formato JSON para enviar al servidor
import json
print("\n[4] Formato JSON para enviar al servidor:")
print("-" * 80)
payload = {
    'clave': 'DIDI-XXXX-XXXX-XXXX',
    'hardware_id': hardware_id,
    'nombre_maquina': info['nombre_maquina'],
    'usuario_sistema': info['usuario_sistema'],
    'hw_componentes': componentes
}
print(json.dumps(payload, indent=2, ensure_ascii=False))
print("-" * 80)
