# Sistema de Licencias - Bot Didi

## 📋 Resumen

Sistema de licenciamiento para proteger el Bot Didi contra copia y réplicas no autorizadas.

**Características:**
- ✅ 1 clave = 1 máquina (vinculada por Hardware ID único)
- ✅ Activaciones ilimitadas en la MISMA máquina
- ✅ No se puede transferir a otra máquina
- ✅ Token local encriptado (válido 30 días)
- ✅ Validación online con el servidor

---

## 🚀 Instalación Inicial

### 1. Ejecutar SQL en la Base de Datos

Abre phpMyAdmin y ejecuta el archivo `SQL_LICENCIAS.sql` completo.

Esto creará:
- Tabla `licencias` (claves y vinculaciones)
- Tabla `validaciones_log` (auditoría)

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

Nueva dependencia agregada:
- `cryptography==41.0.7` (para encriptación de tokens)

---

## 🔑 Generar Licencias (Para Vender)

### Script: `generar_licencia.py`

```bash
python generar_licencia.py
```

**Flujo:**
1. Selecciona "1. Generar nuevas licencias"
2. Ingresa:
   - Cantidad (ej: 15)
   - Nombre del cliente (ej: Empresa XYZ)
   - Notas opcionales
3. Confirma
4. Se generan las claves y se insertan en BD
5. Opcionalmente guarda un archivo .txt para enviar al cliente

**Ejemplo de output:**
```
============================================================
LICENCIAS GENERADAS:
============================================================
1.  DIDI-A3F2-9B7E-4C12
2.  DIDI-X9K1-2M5P-7L3Q
3.  DIDI-M7N4-8P2R-5T6W
...
15. DIDI-Q9Z3-1Y5K-7H2M
============================================================
```

Envías estas claves al cliente.

---

## 👤 Activación del Cliente

### Primera Vez (Cliente nuevo)

1. Cliente ejecuta: `python Didi_GUI.pyw`
2. El bot inicia el backend automáticamente
3. **Pantalla de Activación aparece** (no hay token local)
4. Cliente ingresa su clave: `DIDI-A3F2-9B7E-4C12`
5. El bot:
   - Genera Hardware ID de esa máquina
   - Envía clave + Hardware ID al servidor
   - Servidor valida y vincula la clave a esa máquina
   - Guarda token local encriptado
6. Cliente continúa al login
7. ✅ Puede usar el bot normalmente

### Usos Posteriores (Máquina ya Activada)

1. Cliente ejecuta: `python Didi_GUI.pyw`
2. El bot lee token local
3. Valida con servidor (silenciosamente)
4. **NO pide clave otra vez**
5. Continúa directo al login
6. ✅ Usa el bot

### Si Reinstalan Windows / Formatean

1. Cliente ejecuta el bot
2. No encuentra token local
3. **Pide clave nuevamente**
4. Cliente ingresa la MISMA clave
5. Hardware ID es el mismo (misma máquina)
6. ✅ Servidor permite reactivar
7. Funciona normalmente

---

## 🛡️ Protección Contra Réplicas

### Escenario: Cliente intenta copiar a otra máquina

```
PC-01 (original):
- Clave activada: DIDI-A3F2-9B7E-4C12
- Hardware ID: HW-ABC123...

PC-02 (copia):
- Cliente copia el ejecutable
- Ejecuta el bot
- Pide clave de activación
- Cliente ingresa: DIDI-A3F2-9B7E-4C12
- Hardware ID: HW-XYZ789... (DIFERENTE)
- Servidor: "Esta clave ya está activada en otra máquina"
- ❌ RECHAZA
```

**Resultado:** Cliente necesita OTRA clave (comprar otra licencia).

### Escenario: Cliente intenta copiar el token local

```
PC-02:
- Copian bot.exe + .license_token
- Ejecutan el bot
- Bot lee .license_token
- Token dice: "válido para HW-ABC123..."
- Bot genera Hardware ID: HW-XYZ789...
- ❌ NO COINCIDE → Pide activación
```

**Resultado:** No funciona. El token está encriptado con el Hardware ID de PC-01.

---

## 🔧 Gestión de Licencias (Para Ti)

### Script: `gestionar_licencias.py`

```bash
python gestionar_licencias.py
```

**Opciones:**

### 1. Listar Todas las Licencias

Muestra todas las claves con su estado:
- ID, Clave, Cliente, Estado (Disponible/Activada/Revocada)
- Máquina vinculada, fechas

### 2. Ver Detalle de una Licencia

Muestra info completa de una clave:
- Hardware ID vinculado
- Fechas de activación/validación
- Historial de las últimas 10 validaciones

### 3. Revocar Licencia

**Uso:** Cliente no pagó, quieres desactivarlo

```
Ingrese la clave a revocar: DIDI-A3F2-9B7E-4C12
¿Está seguro? (s/n): s
✓ Licencia revocada
```

**Efecto:**
- En la próxima validación (máx 30 días), el bot del cliente se bloqueará
- Mensaje: "Licencia revocada. Contacte al administrador."

### 4. Desvincular Licencia

**Uso:** Cliente legítimamente cambió de PC

```
Ingrese la clave a desvincular: DIDI-A3F2-9B7E-4C12
⚠️  Advertencia: podrá activarse en OTRA máquina
¿Está seguro? (s/n): s
✓ Licencia desvinculada
```

**Efecto:**
- La clave queda disponible nuevamente
- Cliente puede activarla en su nueva PC

### 5. Reactivar Licencia Revocada

**Uso:** Cliente pagó, quieres reactivarlo

```
Ingrese la clave a reactivar: DIDI-A3F2-9B7E-4C12
¿Reactivar? (s/n): s
✓ Licencia reactivada
```

---

## 📊 Consultas SQL Útiles

### Ver licencias disponibles (no activadas)

```sql
SELECT clave, cliente_nombre
FROM licencias
WHERE activada = FALSE AND activa = TRUE;
```

### Ver licencias activas por cliente

```sql
SELECT clave, nombre_maquina, fecha_activacion
FROM licencias
WHERE cliente_nombre = 'Empresa XYZ' AND activada = TRUE;
```

### Ver licencias que no han validado en 30+ días

```sql
SELECT clave, nombre_maquina,
       DATEDIFF(NOW(), ultima_validacion) as dias_sin_validar
FROM licencias
WHERE activada = TRUE
  AND DATEDIFF(NOW(), ultima_validacion) > 30
ORDER BY dias_sin_validar DESC;
```

### Contar licencias por estado

```sql
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN activada = TRUE THEN 1 ELSE 0 END) as activadas,
    SUM(CASE WHEN activada = FALSE THEN 1 ELSE 0 END) as disponibles,
    SUM(CASE WHEN activa = FALSE THEN 1 ELSE 0 END) as revocadas
FROM licencias;
```

---

## 🔄 Flujo Completo del Sistema

```
[INICIO] Cliente ejecuta Didi_GUI.pyw
   │
   ├─> Backend Flask inicia en puerto 5000
   │
   ├─> ¿Existe token local?
   │   │
   │   ├─> NO → Pantalla de Activación
   │   │         ├─> Cliente ingresa clave
   │   │         ├─> Bot genera Hardware ID
   │   │         ├─> POST /licencias/activar
   │   │         │     ├─> ¿Clave existe? ✓
   │   │         │     ├─> ¿Clave activa? ✓
   │   │         │     ├─> ¿Ya activada?
   │   │         │     │   ├─> NO → Vincular y activar ✓
   │   │         │     │   ├─> SÍ → ¿Mismo Hardware?
   │   │         │     │         ├─> SÍ → Reactivar ✓
   │   │         │     │         └─> NO → RECHAZAR ❌
   │   │         │     └─> Guardar token local
   │   │         └─> Continuar a Login
   │   │
   │   └─> SÍ → Leer token local
   │            ├─> ¿Token válido?
   │            │   ├─> SÍ → POST /licencias/validar
   │            │   │        ├─> ¿Hardware coincide? ✓
   │            │   │        └─> Continuar a Login
   │            │   └─> NO → Pantalla de Activación
   │
   ├─> Pantalla de Login (autenticación de usuario)
   │   └─> Usuario ingresa credenciales
   │       └─> POST /auth/login
   │           └─> Token JWT generado
   │
   └─> GUI Principal del Bot
       └─> Cliente puede usar el bot
```

---

## ⚙️ Configuración Técnica

### Hardware ID

Generado con:
- MAC Address de la red
- Nombre de la máquina
- Sistema operativo
- Arquitectura del procesador
- UUID del motherboard (Windows)

**Hash SHA256** de todos los componentes → ID único de 32 caracteres.

Formato: `HW-XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX`

### Token Local

Archivo: `.license_token` (en la raíz del proyecto)

Contenido encriptado con Fernet (basado en Hardware ID):
```json
{
  "clave": "DIDI-A3F2-9B7E-4C12",
  "hardware_id": "HW-...",
  "fecha_creacion": "2025-01-31...",
  "expira": "2025-02-30..."  // 30 días después
}
```

**Seguridad:**
- Encriptado con clave derivada del Hardware ID
- Solo funciona en la máquina donde se generó
- Si se copia a otra PC → no se puede desencriptar

### Validación Online

**Cada vez que inicia el bot:**
1. Lee token local
2. Llama a `POST /licencias/validar`
3. Envía: clave + hardware_id
4. Servidor verifica:
   - ¿Clave existe?
   - ¿Está activa (no revocada)?
   - ¿Hardware ID coincide?
5. Si OK → actualiza `ultima_validacion` en BD
6. Si NO → pide activación

**Ventana de gracia:** 30 días (duración del token local)

---

## 🚨 Casos de Uso Comunes

### Cliente compra 15 licencias

1. Ejecutas: `python generar_licencia.py`
2. Generas 15 claves
3. Envías archivo .txt al cliente
4. Cliente distribuye a sus 15 máquinas
5. Cada máquina activa con su clave única

### Cliente pierde conectividad a internet

- Token local válido por 30 días
- Puede usar el bot sin problemas
- Después de 30 días: necesita conexión para revalidar

### Cliente formatea una PC

1. Reinstala el bot
2. Ejecuta `Didi_GUI.pyw`
3. Pide clave nuevamente
4. Ingresa la misma clave
5. Hardware ID coincide → reactiva sin problemas

### Cliente intenta usar en PC 16 (solo tiene 15 licencias)

1. Intenta activar con alguna clave ya usada
2. **RECHAZA:** "Esta clave ya está activada en otra máquina"
3. Cliente debe comprarte otra licencia

### Cliente cambia de PC legítimamente

**Opción A:** Tú desvincula la clave
```bash
python gestionar_licencias.py
# Opción 4: Desvincular licencia
```

**Opción B:** Cliente te contacta, tú haces el cambio manualmente en BD

---

## 📞 Soporte al Cliente

### "No puedo activar mi clave"

**Posibles causas:**
1. Clave incorrecta → Verificar formato y typos
2. Clave ya activada en otra máquina → Ver en gestionar_licencias.py
3. Backend no está corriendo → Reiniciar aplicación
4. Sin conexión a BD → Verificar credenciales en config/settings.py

### "Me pide activación cada vez"

**Causa:** Token local no se guarda/lee correctamente

**Solución:**
1. Verificar permisos de escritura en la carpeta del bot
2. Verificar que no haya antivirus bloqueando `.license_token`

### "Cambié de PC y no funciona"

**Solución:** Desvincular la clave de la PC vieja

```bash
python gestionar_licencias.py
# Opción 4: Desvincular
```

---

## 🔐 Seguridad

### Nivel Actual: MEDIO-ALTO

**Protecciones implementadas:**
- ✅ Hardware ID único por máquina
- ✅ Token encriptado con Hardware ID
- ✅ Validación online con servidor
- ✅ Logs de todos los intentos
- ✅ Detección de máquinas diferentes

**Nivel de seguridad:** Suficiente para uso comercial estándar

### Protecciones Futuras (Opcional)

Si detectas piratería, puedes agregar:
1. **Ofuscación del código** (PyArmor, Nuitka)
2. **Firma digital del ejecutable**
3. **Anti-debugging**
4. **Code splitting** (lógica crítica en servidor)

---

## 📝 Archivos del Sistema

```
botdidi/
├── SQL_LICENCIAS.sql              # SQL para crear tablas
├── generar_licencia.py            # Generar claves (para ti)
├── gestionar_licencias.py         # Gestionar licencias (para ti)
├── backend/
│   ├── license_utils.py           # Hardware ID, tokens, etc.
│   └── license_endpoints.py       # API endpoints
├── gui/
│   └── activation.py              # Pantalla de activación
├── Didi_GUI.pyw                   # Modificado con validación
└── .license_token                 # Token local (se crea al activar)
```

---

## ✅ Checklist de Implementación

- [x] SQL ejecutado en base de datos
- [x] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Generar licencias de prueba (`python generar_licencia.py`)
- [ ] Probar activación en una máquina
- [ ] Verificar que token local se crea
- [ ] Probar reabrir el bot (no debe pedir clave otra vez)
- [ ] Intentar copiar a otra máquina (debe rechazar)
- [ ] Probar desvincular una licencia
- [ ] Probar revocar una licencia

---

## 🎯 Resumen para Venta

**Cuando vendes al cliente:**

"Cada licencia es para UNA máquina. Una vez activada:
- ✓ Funciona en esa máquina para siempre
- ✓ Puede reinstalar Windows sin problemas
- ✓ No caduca (licencia perpetua)
- ✗ NO se puede transferir a otra máquina

Si necesitan más máquinas → compran más licencias."

---

¿Preguntas? Contacta al desarrollador del sistema.
