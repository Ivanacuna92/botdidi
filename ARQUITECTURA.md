# Arquitectura Modular del Bot Didi

Este proyecto ha sido refactorizado de un único archivo de 1549 líneas a una arquitectura modular y mantenible.

## Estructura del Proyecto

```
botdidi/
├── Didi_GUI.pyw              # Punto de entrada principal (25 líneas)
├── Didi_GUI_OLD.pyw.backup   # Backup del archivo original
│
├── config/                   # Configuración global
│   ├── __init__.py
│   └── settings.py          # Configuraciones, variables globales, colas
│
├── backend/                  # Backend Flask
│   ├── __init__.py
│   └── flask_server.py      # Servidor Flask con endpoints REST
│
├── chrome/                   # Gestión de Chrome
│   ├── __init__.py
│   ├── manager.py           # Abrir, cerrar, conectar a Chrome
│   └── session.py           # Verificación de sesión de Didi
│
├── bot/                      # Lógica del bot
│   ├── __init__.py
│   ├── main.py              # Función principal de ejecución
│   ├── navigator.py         # Navegación en la plataforma
│   └── processor.py         # Procesamiento de registros individuales
│
└── gui/                      # Interfaz gráfica
    ├── __init__.py
    └── interface.py         # GUI con Tkinter
```

## Módulos

### 1. `config/settings.py`
Contiene todas las configuraciones globales:
- Rutas de Chrome y perfil
- Configuración de base de datos
- URLs de Didi
- Variables globales de estado
- Colas de comunicación entre threads

### 2. `backend/flask_server.py`
Servidor Flask que maneja:
- `/registrar` - Registrar clientes procesados
- `/registrar_cliente` - Registrar cliente individual
- `/health` - Verificación de salud del servidor
- `/estadisticas` - Obtener estadísticas históricas
- `/clientes_hoy` - Obtener clientes procesados hoy

### 3. `chrome/manager.py`
Gestión de Chrome:
- `cerrar_chrome_existente()` - Cierra instancias de Chrome
- `reiniciar_chrome_limpio()` - Reinicia Chrome completamente
- `abrir_chrome_con_perfil()` - Abre Chrome con perfil dedicado
- `conectar_a_chrome()` - Conecta Selenium a Chrome

### 4. `chrome/session.py`
Verificación de sesión:
- `verificar_sesion_didi()` - Verifica si el usuario está logueado
- Maneja recuperación de contexto perdido
- Navegación automática al dashboard

### 5. `bot/navigator.py`
Navegación en la plataforma:
- `navegar_a_mis_casos()` - Navega al menú "Mis casos"

### 6. `bot/processor.py`
Procesamiento de registros:
- `cerrar_pestanas_detalles_abiertas()` - Limpia pestañas previas
- `procesar_registro()` - Procesa un registro completo
- Captura datos del cliente (nombre, cfrnid, monto)
- Envía mensajes por WhatsApp
- Genera código de pago

### 7. `bot/main.py`
Lógica principal de ejecución:
- `ejecutar_bot()` - Función principal que orquesta todo el proceso
- Inicializa backend
- Gestiona Chrome
- Procesa registros página por página
- Registra resultados en BD

### 8. `gui/interface.py`
Interfaz gráfica:
- Clase `BotDidiGUI` con todos los elementos visuales
- Botones de control (Iniciar/Detener)
- Estadísticas en tiempo real
- Log de actividad
- Generación de reportes CSV

## Ventajas de la Nueva Arquitectura

1. **Mantenibilidad**: Cada módulo tiene una responsabilidad clara
2. **Legibilidad**: Archivos más pequeños y enfocados
3. **Reutilización**: Funciones pueden importarse fácilmente
4. **Testing**: Cada módulo puede probarse de forma independiente
5. **Escalabilidad**: Fácil agregar nuevas funcionalidades
6. **Debugging**: Más fácil identificar y corregir errores

## Cómo Ejecutar

El programa se ejecuta exactamente igual que antes:

```bash
python Didi_GUI.pyw
```

O simplemente haciendo doble clic en `Didi_GUI.pyw`

## Migración desde Versión Antigua

Si tienes problemas con la nueva versión, puedes volver a la anterior:

```bash
cp Didi_GUI_OLD.pyw.backup Didi_GUI.pyw
```

## Desarrollo Futuro

Con esta arquitectura es fácil:
- Agregar nuevos tipos de procesamiento en `bot/`
- Implementar diferentes navegadores en `chrome/`
- Cambiar el backend (por ejemplo, a FastAPI) en `backend/`
- Crear diferentes interfaces (CLI, Web) en paralelo a `gui/`

## Dependencias

Todas las dependencias siguen siendo las mismas del `requirements.txt`:
- selenium
- flask
- waitress
- pymysql
- psutil
- requests
