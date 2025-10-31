-- ============================================================================
-- SISTEMA DE LICENCIAS - BOT DIDI
-- Sistema: 1 clave = 1 máquina (activaciones ilimitadas en esa máquina)
--
-- INSTRUCCIONES:
-- 1. Copia este archivo completo
-- 2. Pégalo en phpMyAdmin (pestaña SQL)
-- 3. Ejecuta
-- ============================================================================

-- Tabla principal de licencias
CREATE TABLE licencias (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Clave única de activación (formato: DIDI-XXXX-XXXX-XXXX)
    clave VARCHAR(50) UNIQUE NOT NULL,

    -- Información del cliente
    cliente_nombre VARCHAR(100),
    notas TEXT,

    -- Vinculación a máquina (se llena al activar)
    hardware_id VARCHAR(255) NULL,
    nombre_maquina VARCHAR(100),
    usuario_sistema VARCHAR(100),

    -- Control de fechas
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_activacion TIMESTAMP NULL,
    ultima_validacion TIMESTAMP NULL,

    -- Control de estado
    activada BOOLEAN DEFAULT FALSE,  -- true cuando se activa por primera vez
    activa BOOLEAN DEFAULT TRUE,      -- false para revocar licencia

    -- Info adicional
    ip_activacion VARCHAR(45),

    -- Índices para búsquedas rápidas
    UNIQUE KEY unique_hardware (hardware_id),
    INDEX idx_clave (clave),
    INDEX idx_hardware (hardware_id),
    INDEX idx_activada (activada),
    INDEX idx_activa (activa)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Tabla de logs de validación (auditoría)
CREATE TABLE validaciones_log (
    id INT AUTO_INCREMENT PRIMARY KEY,

    licencia_id INT NOT NULL,
    hardware_id VARCHAR(255),

    fecha_validacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exitosa BOOLEAN DEFAULT TRUE,
    ip_address VARCHAR(45),
    mensaje VARCHAR(255),

    -- Índices
    INDEX idx_licencia (licencia_id),
    INDEX idx_fecha (fecha_validacion),

    -- Relación con tabla licencias
    CONSTRAINT fk_validaciones_licencia
        FOREIGN KEY (licencia_id) REFERENCES licencias(id)
        ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- CONSULTAS ÚTILES PARA GESTIÓN
-- ============================================================================

-- Ver todas las licencias y su estado
-- SELECT
--     id,
--     clave,
--     cliente_nombre,
--     activada,
--     activa,
--     nombre_maquina,
--     DATE(fecha_activacion) as activacion,
--     DATE(ultima_validacion) as ultima_validacion,
--     DATEDIFF(NOW(), ultima_validacion) as dias_sin_validar
-- FROM licencias
-- ORDER BY fecha_creacion DESC;

-- Ver solo licencias disponibles (no activadas)
-- SELECT clave, cliente_nombre, fecha_creacion
-- FROM licencias
-- WHERE activada = FALSE AND activa = TRUE
-- ORDER BY fecha_creacion DESC;

-- Ver solo licencias activadas
-- SELECT
--     clave,
--     nombre_maquina,
--     usuario_sistema,
--     DATE(fecha_activacion) as activada_el,
--     DATE(ultima_validacion) as ultima_validacion,
--     DATEDIFF(NOW(), ultima_validacion) as dias_sin_validar
-- FROM licencias
-- WHERE activada = TRUE
-- ORDER BY ultima_validacion DESC;

-- Contar licencias por estado
-- SELECT
--     COUNT(*) as total,
--     SUM(activada) as activadas,
--     SUM(CASE WHEN activada = FALSE THEN 1 ELSE 0 END) as disponibles,
--     SUM(CASE WHEN activa = FALSE THEN 1 ELSE 0 END) as revocadas
-- FROM licencias;

-- Ver intentos de validación recientes
-- SELECT
--     l.clave,
--     v.fecha_validacion,
--     v.exitosa,
--     v.mensaje,
--     v.ip_address
-- FROM validaciones_log v
-- JOIN licencias l ON v.licencia_id = l.id
-- ORDER BY v.fecha_validacion DESC
-- LIMIT 50;


-- ============================================================================
-- OPERACIONES ADMINISTRATIVAS (Ejecutar cuando sea necesario)
-- ============================================================================

-- REVOCAR una licencia (para que ya no funcione)
-- UPDATE licencias
-- SET activa = FALSE
-- WHERE clave = 'DIDI-XXXX-XXXX-XXXX';

-- DESVINCULAR una licencia (permitir reactivar en otra máquina)
-- Útil si cliente cambia de PC
-- UPDATE licencias
-- SET
--     activada = FALSE,
--     hardware_id = NULL,
--     nombre_maquina = NULL,
--     usuario_sistema = NULL,
--     fecha_activacion = NULL,
--     ultima_validacion = NULL
-- WHERE clave = 'DIDI-XXXX-XXXX-XXXX';

-- REACTIVAR una licencia revocada
-- UPDATE licencias
-- SET activa = TRUE
-- WHERE clave = 'DIDI-XXXX-XXXX-XXXX';


-- ============================================================================
-- EJEMPLO: Insertar licencias manualmente (si no usas el script Python)
-- ============================================================================

-- INSERT INTO licencias (clave, cliente_nombre, notas) VALUES
-- ('DIDI-A3F2-9B7E-4C12', 'Empresa XYZ', 'Licencia 1 de 15'),
-- ('DIDI-X9K1-2M5P-7L3Q', 'Empresa XYZ', 'Licencia 2 de 15'),
-- ('DIDI-M7N4-8P2R-5T6W', 'Empresa XYZ', 'Licencia 3 de 15');


-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
-- Ahora puedes usar el script generar_licencia.py para crear licencias
-- automáticamente.
-- ============================================================================
