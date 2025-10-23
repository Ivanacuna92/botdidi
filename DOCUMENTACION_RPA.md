# RPA - Sistema de Notificaciones Automatizadas Didi

## Descripción del Proyecto

Este es un RPA (Robotic Process Automation) desarrollado con Selenium que automatiza el proceso de envío de notificaciones de pago a clientes en el dashboard de Didi.

## Funcionalidad Principal

El bot automatiza el siguiente flujo completo para TODOS los registros de la tabla de "Mis casos":

1. **Navegación al módulo**:
   - Mesa de trabajo para llamada de cobranza → Mis casos → Mis casos

2. **Procesamiento de cada registro**:
   - Click en botón "Detalles" del cliente
   - Click en botón "WhatsApp"
   - Click en "Seleccionar plantilla de comunicación"
   - Seleccionar plantilla de mensaje
   - Click en "Enviar"
   - Click en "Código del pago"
   - Seleccionar opción con radio button
   - Click en "Confirmar"
   - Cerrar pestaña del lead automáticamente

3. **Paginación**:
   - Procesa TODOS los registros de la página actual (20 por defecto)
   - Navega automáticamente a la siguiente página
   - Continúa hasta procesar todas las páginas disponibles

## Estructura del Código

### Archivos principales:
- `Didi.py` - Script principal del RPA
- `abrir_chrome_debug.bat` - Batch para abrir Chrome en modo debug
- `reporte.txt` - Log de ejecución (se genera automáticamente)

### Funciones principales:

#### `procesar_registro(driver, indice_registro)`
Procesa un registro individual ejecutando todo el flujo de envío de notificación.

**Parámetros:**
- `driver`: Instancia de Selenium WebDriver
- `indice_registro`: Índice del registro en la tabla actual (0-based)

**Retorna:**
- `True` si se procesó exitosamente
- `False` si hubo error

#### `automate_didi_dashboard()`
Función principal que:
- Se conecta a Chrome en modo debug
- Navega al módulo "Mis casos"
- Ejecuta el loop de procesamiento por páginas
- Genera estadísticas finales

## Configuración Inicial

### Requisitos:
- Python 3.x
- Selenium
- ChromeDriver compatible con tu versión de Chrome

### Instalación:
```bash
pip install selenium
```

### Configuración de Chrome (SOLO UNA VEZ):
1. Cierra TODAS las ventanas de Chrome
2. Ejecuta: `abrir_chrome_debug.bat`
3. En el Chrome que se abre, navega a Didi y haz login
4. MANTÉN ESE CHROME ABIERTO siempre

### Contenido de `abrir_chrome_debug.bat`:
```batch
start chrome --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
```

## Ejecución

### Ejecución normal (ver en consola):
```powershell
python Didi.py
```

### Ejecución con log a archivo:
```powershell
python Didi.py > reporte.txt 2>&1
```

## Salida del Script

El script muestra en tiempo real:
- Página actual siendo procesada
- Número de registros encontrados
- Progreso de cada registro individual
- Estadísticas finales:
  - Total de registros procesados
  - Exitosos
  - Con errores
  - Páginas procesadas

### Ejemplo de salida:
```
[OK] Conectado a Chrome exitosamente!
[*] Paso 1: Esperando carga del menu vertical...
[OK] Menu principal cargado
...
======================================================================
[*] INICIANDO PROCESAMIENTO MASIVO DE REGISTROS
======================================================================

######################################################################
[*] PAGINA 1
######################################################################
[OK] 20 registros encontrados en esta pagina

============================================================
[*] PROCESANDO REGISTRO #0
============================================================
[OK] Boton 'Detalles' #0 encontrado, haciendo click...
[OK] Click en 'Detalles' exitoso
[*] Clickeando boton WhatsApp...
...
[OK] REGISTRO #0 COMPLETADO

[*] Buscando siguiente pagina...
[OK] Hay mas paginas, navegando a pagina 2...

######################################################################
[*] PAGINA 2
######################################################################
...

======================================================================
[OK] PROCESAMIENTO COMPLETADO
======================================================================
[*] ESTADISTICAS:
   - Total de registros procesados: 45
   - Exitosos: 43
   - Con errores: 2
   - Paginas procesadas: 3
======================================================================
```

## Problemas Resueltos Durante el Desarrollo

### 1. Encoding de emojis en Windows
**Problema:** La consola de Windows no soportaba emojis UTF-8
**Solución:** Se removieron todos los emojis y se usaron prefijos ASCII:
- `[OK]` para éxito
- `[*]` para información
- `[!]` para advertencias
- `[ERROR]` para errores

### 2. Botones duplicados en tabla
**Problema:** Element UI crea tablas duplicadas (una fija, una con scroll), encontraba 40 botones en vez de 20
**Solución:** Filtrar solo elementos visibles con XPath: `//td[not(contains(@class, 'is-hidden'))]//button`

### 3. Pestañas acumulándose
**Problema:** Cada lead procesado abría una pestaña que no se cerraba
**Solución:** Implementar cierre automático de pestaña usando el botón X del tag:
```python
# HTML: <span class="tags-view-item">Detalles del lead<span class="el-icon-close"></span></span>
boton_cerrar_tab = driver.find_element(By.XPATH, "//span[contains(@class, 'tags-view-item') and contains(., 'Detalles del lead')]//span[contains(@class, 'el-icon-close')]")
```

### 4. Botones con espacios en el texto
**Problema:** XPath con `text()='Enviar'` fallaba por espacios invisibles en HTML
**Solución:** Buscar todos los botones con las clases correctas y filtrar por texto con Python:
```python
botones = driver.find_elements(By.XPATH, "//button[@type='button' and contains(@class, 'el-button--primary')]")
for boton in botones:
    if "Enviar" in boton.text:
        boton_enviar = boton
        break
```

### 5. Paginación
**Problema:** Necesitaba navegar entre páginas automáticamente
**Solución:** Buscar el botón de flecha derecha que no esté deshabilitado:
```python
# HTML: <button class="btn-next"><i class="el-icon-arrow-right"></i></button>
boton_siguiente = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-next') and not(@disabled)]//i[contains(@class, 'el-icon-arrow-right')]")
```

## XPaths Importantes Utilizados

### Navegación del menú:
```python
# Menú principal
"//ul[@role='menubar' and contains(@class, 'el-menu')]"

# Mesa de trabajo
"//div[@class='el-submenu__title']//span[contains(@title, 'Mesa de trabajo')]"

# Submenu Mis casos
"//div[@class='nest-menu']//div[@class='el-submenu__title']//span[@title='Mis casos']"

# Link final Mis casos
"//a[@href='/pixiu/#/my_case/my_case_index']//li[@class='el-menu-item']"
```

### Tabla y acciones:
```python
# Botones Detalles (solo visibles)
"//td[not(contains(@class, 'is-hidden'))]//button[contains(@class, 'el-button') and .//span[text()='Detalles']]"

# Botón WhatsApp
"//button[contains(@class, 'el-button') and contains(., 'whatsapp')]"

# Botón plantilla
"//button[contains(@class, 'check-template80')]"

# Contenido plantilla
"//div[contains(@class, 'wa-template-content')]"

# Radio button código de pago
"//table//input[@type='radio']"

# Cerrar pestaña lead
"//span[contains(@class, 'tags-view-item') and contains(., 'Detalles del lead')]//span[contains(@class, 'el-icon-close')]"

# Botón siguiente página
"//button[contains(@class, 'btn-next') and not(@disabled)]//i[contains(@class, 'el-icon-arrow-right')]"
```

## Notas Técnicas

### Element UI Framework
El dashboard usa Element UI (framework de Vue.js), características:
- Los modales son `<div class="el-dialog">`
- Los botones tienen clases como `el-button--primary`, `el-button--mini`, etc.
- Las tablas se duplican para fixed columns (necesario filtrar `is-hidden`)
- Los tabs son `<span class="tags-view-item">`

### Tiempos de espera
Se usan varios `time.sleep()` para dar tiempo a que:
- Los modales se abran/cierren
- Los botones se habiliten después de selecciones
- Las páginas carguen después de navegación
- Típicamente: 0.5s para scroll, 1-2s para modales

### Manejo de errores
- Cada registro tiene try/except individual
- Si un registro falla, intenta volver a la tabla y continuar con el siguiente
- Al final muestra estadísticas de éxito/error

## Próximas Mejoras Potenciales

1. ~~Implementar paginación automática~~ ✅ COMPLETADO
2. Agregar logging más detallado con módulo `logging`
3. Permitir configuración de qué plantilla seleccionar
4. Añadir capturas de pantalla en caso de error
5. Implementar reintentos automáticos en caso de fallo
6. Crear interfaz gráfica simple para configuración
7. Agregar validaciones de datos antes de enviar

## Fecha de Creación
2025-01-XX (actualizar con fecha real)

## Versión Actual
1.0

## Última Actualización
Implementación completa con paginación automática y cierre de pestañas.
