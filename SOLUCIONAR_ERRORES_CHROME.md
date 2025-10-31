# 🔧 Guía para Solucionar Errores de Chrome

## Problema: "no such execution context" o "frame does not have execution context"

### ¿Por qué ocurre?
Este error aparece cuando:
- Cerraste el bot pero Chrome quedó abierto con pestañas antiguas
- Las pestañas perdieron su "contexto de ejecución" de Selenium
- Chrome tiene pestañas "zombie" que no responden

### ✅ Soluciones Automáticas Implementadas

El bot ahora tiene **3 niveles de recuperación automática**:

#### Nivel 1: Limpieza de Pestañas al Conectar
- Detecta pestañas con contexto perdido
- Las cierra automáticamente
- Crea una nueva pestaña fresca

#### Nivel 2: Recuperación en Verificación
- Intenta navegar directamente al dashboard
- Aumenta el timeout a 30 segundos
- Prueba con todas las pestañas disponibles

#### Nivel 3: Última Oportunidad
- Crea una nueva pestaña desde cero
- Navega al dashboard en la pestaña nueva
- Continúa con el proceso normal

### 🛠️ Soluciones Manuales (si el bot no puede recuperarse)

#### Opción 1: Reiniciar el Proceso (Recomendado)
1. **Cierra el bot** (botón DETENER o X)
2. **Cierra Chrome completamente** (todas las ventanas)
3. **Vuelve a iniciar el bot**
4. Chrome se abrirá limpio y funcionará correctamente

#### Opción 2: Limpiar Pestañas Manualmente
1. En Chrome, cierra TODAS las pestañas excepto una
2. En la pestaña que dejaste, ve a: `about:blank`
3. Vuelve a presionar "INICIAR BOT" en la interfaz

#### Opción 3: Script de Limpieza (Nuclear)
Si Chrome está completamente bloqueado:
```bash
python cerrar_puerto_5000.py
```
Luego cierra Chrome manualmente y reinicia el bot.

## Otros Errores Comunes

### Error: "Backend no responde"
**Solución:**
```bash
python cerrar_puerto_5000.py
```
Reinicia el bot.

### Error: "Chrome no encontrado"
**Solución:**
Verifica que Chrome esté instalado en una de estas rutas:
- `C:\Program Files\Google\Chrome\Application\chrome.exe`
- `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`
- `%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe`

### Error: "Timeout esperando elemento"
**Posibles causas:**
- La página de Didi cambió su estructura
- Internet está lento
- No estás logueado en Didi

**Solución:**
1. Verifica tu conexión a internet
2. Asegúrate de estar logueado en Didi
3. Reinicia el bot

## 📋 Checklist Antes de Reportar un Bug

- [ ] Cerré Chrome completamente y reinicié el bot
- [ ] Ejecuté `cerrar_puerto_5000.py`
- [ ] Verifiqué que esté logueado en Didi
- [ ] Probé con una conexión de internet estable
- [ ] El error persiste después de intentar todo lo anterior

Si después de esto el error continúa, entonces sí es un bug del bot.
