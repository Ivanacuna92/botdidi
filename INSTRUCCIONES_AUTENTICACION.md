# Sistema de Autenticación - Bot Didi

## Resumen de Cambios

Se ha implementado un sistema completo de autenticación con JWT para el Bot Didi. Ahora cada usuario debe iniciar sesión antes de usar el bot, y todas las operaciones quedan registradas por usuario.

## Instalación

### 1. Ejecutar el Script SQL

Primero, ejecuta el siguiente SQL en tu base de datos MySQL:

```sql
-- TABLA DE USUARIOS (para autenticación)
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100),
    rol ENUM('admin', 'operador') DEFAULT 'operador',
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- MODIFICACIÓN: Agregar user_id a bot_clientes_procesados
ALTER TABLE bot_clientes_procesados
ADD COLUMN user_id INT NULL AFTER id,
ADD INDEX idx_user_id (user_id),
ADD CONSTRAINT fk_clientes_user
    FOREIGN KEY (user_id) REFERENCES usuarios(id)
    ON DELETE SET NULL;

-- NUEVA TABLA: Ejecuciones diarias por usuario
CREATE TABLE bot_ejecuciones_usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    fecha DATE NOT NULL,
    clientes_procesados INT DEFAULT 0,
    clientes_exitosos INT DEFAULT 0,
    clientes_errores INT DEFAULT 0,
    tiempo_total_segundos INT DEFAULT 0,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_fecha (user_id, fecha),
    INDEX idx_user_id (user_id),
    INDEX idx_fecha (fecha),
    CONSTRAINT fk_ejecuciones_user
        FOREIGN KEY (user_id) REFERENCES usuarios(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- TABLA DE SESIONES (para gestión de tokens)
CREATE TABLE sesiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion TIMESTAMP NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    INDEX idx_user_id (user_id),
    INDEX idx_token_hash (token_hash),
    CONSTRAINT fk_sesiones_user
        FOREIGN KEY (user_id) REFERENCES usuarios(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

Las nuevas dependencias son:
- `PyJWT==2.8.0` - Para tokens JWT
- `bcrypt==4.1.2` - Para hash de contraseñas
- `waitress==3.0.0` - Servidor de producción (ya existía)

## Crear el Primer Usuario

Antes de poder usar el bot, necesitas crear al menos un usuario administrador:

```bash
python crear_usuario.py
```

El script te guiará interactivamente para crear usuarios:

1. Selecciona "1. Crear nuevo usuario"
2. Ingresa los datos:
   - Username (ej: admin)
   - Email (ej: admin@empresa.com)
   - Nombre completo (opcional)
   - Rol (1=Operador, 2=Admin)
   - Contraseña (mínimo 6 caracteres)

**Importante:** El primer usuario debe ser Admin para poder crear otros usuarios después.

## Uso del Sistema

### 1. Iniciar la Aplicación

```bash
python Didi_GUI.pyw
```

### 2. Login

Al iniciar, verás una pantalla de login:
- Ingresa tu username y contraseña
- Click en "INICIAR SESIÓN"

### 3. Uso Normal del Bot

Una vez logueado, la interfaz funciona exactamente igual que antes:
- El nombre del usuario logueado aparece en la parte superior
- Todas las operaciones quedan registradas bajo tu usuario
- Los estadísticos y reportes incluyen tus datos

## Gestión de Usuarios

### Crear Nuevos Usuarios (desde script)

```bash
python crear_usuario.py
```

Selecciona la opción 1 y sigue las instrucciones.

### Listar Usuarios Existentes

```bash
python crear_usuario.py
```

Selecciona la opción 2 para ver todos los usuarios del sistema.

### Crear Usuarios desde Dashboard Web (futuro)

Los endpoints están preparados para que un dashboard web pueda:
- Crear usuarios: `POST /auth/register` (requiere ser admin)
- Listar usuarios: `GET /auth/usuarios` (requiere ser admin)

## Roles de Usuario

### Operador
- Puede usar el bot normalmente
- Ve sus propias estadísticas
- No puede crear otros usuarios

### Admin
- Puede hacer todo lo que hace un operador
- Puede crear nuevos usuarios
- Puede ver usuarios del sistema
- (En futuro: puede ver estadísticas globales)

## Endpoints de API

### Autenticación

**Login**
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "tu_password"
}
```

Respuesta:
```json
{
  "status": "ok",
  "message": "Login exitoso",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "usuario": {
    "id": 1,
    "username": "admin",
    "email": "admin@empresa.com",
    "rol": "admin"
  }
}
```

**Logout**
```http
POST /auth/logout
Authorization: Bearer TOKEN_AQUI
```

**Verificar Token**
```http
GET /auth/verify
Authorization: Bearer TOKEN_AQUI
```

### Operaciones del Bot

Todos los endpoints existentes ahora requieren el header de autenticación:

```http
Authorization: Bearer TOKEN_AQUI
```

Endpoints protegidos:
- `POST /registrar` - Registrar ejecución diaria
- `POST /registrar_cliente` - Registrar cliente procesado
- `GET /estadisticas` - Ver estadísticas
- `GET /clientes_hoy` - Ver clientes de hoy

## Seguridad

### Tokens JWT
- Duración: 24 horas (configurable en `config/auth.py`)
- Se invalidan al hacer logout
- Se validan en cada petición

### Contraseñas
- Hasheadas con bcrypt (salt automático)
- Nunca se almacenan en texto plano
- Verificación segura

### Sesiones
- Se registran en base de datos
- Se pueden invalidar manualmente
- Expiran automáticamente

## Resolución de Problemas

### "Backend no disponible"
Asegúrate de que el puerto 5000 esté libre antes de iniciar.

### "Credenciales inválidas"
Verifica que el username y password sean correctos (case-sensitive).

### Error al crear usuario
- Verifica que el username no exista
- Verifica que el email no esté registrado
- Asegúrate de que las tablas SQL estén creadas

### Token expirado
El token dura 24 horas. Cierra sesión y vuelve a iniciar sesión.

## Estructura de Archivos Nuevos

```
botdidi/
├── backend/
│   ├── models.py           # Modelos de Usuario y Sesión
│   └── auth_utils.py       # Utilidades de autenticación
├── config/
│   └── auth.py            # Configuración JWT
├── gui/
│   └── login.py           # Pantalla de login
├── crear_usuario.py        # Script de administración
└── INSTRUCCIONES_AUTENTICACION.md
```

## Próximos Pasos (Opcional)

Para expandir el sistema en el futuro:

1. **Dashboard Web**: Crear una interfaz web para:
   - Ver estadísticas por usuario
   - Gestionar usuarios
   - Ver reportes históricos

2. **Roles Avanzados**: Agregar más roles como:
   - Supervisor (ve todo pero no edita)
   - Manager (gestiona operadores)

3. **Auditoría**: Registrar todas las acciones en una tabla de auditoría

4. **2FA**: Agregar autenticación de dos factores

## Contacto y Soporte

Para reportar problemas o sugerencias, contacta al administrador del sistema.
