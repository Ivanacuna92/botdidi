-- ============================================================================
-- MIGRACIÓN: Agregar componentes de hardware a tabla de licencias
-- Fecha: 2025-11-06
-- Propósito: Guardar componentes individuales del Hardware ID para diagnóstico
-- ============================================================================

USE didibot;

-- Agregar columnas para componentes de hardware
ALTER TABLE licencias
ADD COLUMN hw_mac_address VARCHAR(100) DEFAULT NULL COMMENT 'MAC Address del adaptador de red',
ADD COLUMN hw_hostname VARCHAR(255) DEFAULT NULL COMMENT 'Nombre de la máquina (hostname)',
ADD COLUMN hw_os_info VARCHAR(100) DEFAULT NULL COMMENT 'Sistema operativo y versión',
ADD COLUMN hw_processor VARCHAR(100) DEFAULT NULL COMMENT 'Arquitectura del procesador',
ADD COLUMN hw_motherboard_uuid VARCHAR(100) DEFAULT NULL COMMENT 'UUID de la motherboard (WMIC)',
ADD COLUMN hw_components_updated_at DATETIME DEFAULT NULL COMMENT 'Última vez que se actualizaron los componentes';

-- Agregar índices para búsqueda rápida
CREATE INDEX idx_mac_address ON licencias(hw_mac_address);
CREATE INDEX idx_hostname ON licencias(hw_hostname);
CREATE INDEX idx_motherboard ON licencias(hw_motherboard_uuid);

-- Ver estructura actualizada
DESCRIBE licencias;

-- ============================================================================
-- CONSULTAS ÚTILES PARA DIAGNÓSTICO
-- ============================================================================

-- Ver todas las licencias con sus componentes de hardware
SELECT
    id,
    clave,
    cliente_nombre,
    nombre_maquina,
    hardware_id,
    hw_mac_address,
    hw_hostname,
    hw_os_info,
    hw_processor,
    hw_motherboard_uuid,
    hw_components_updated_at,
    activada,
    fecha_activacion
FROM licencias
ORDER BY fecha_activacion DESC;

-- Detectar posibles cambios de MAC Address
-- (licencias con mismo hostname pero diferente MAC)
SELECT
    hw_hostname,
    COUNT(DISTINCT hw_mac_address) as diferentes_macs,
    GROUP_CONCAT(DISTINCT hw_mac_address) as macs_detectados,
    GROUP_CONCAT(DISTINCT clave) as claves
FROM licencias
WHERE hw_hostname IS NOT NULL
GROUP BY hw_hostname
HAVING COUNT(DISTINCT hw_mac_address) > 1;

-- Detectar posibles cambios de OS
-- (licencias con mismo hardware pero diferente OS)
SELECT
    hw_motherboard_uuid,
    COUNT(DISTINCT hw_os_info) as diferentes_os,
    GROUP_CONCAT(DISTINCT hw_os_info) as os_detectados,
    GROUP_CONCAT(DISTINCT clave) as claves
FROM licencias
WHERE hw_motherboard_uuid IS NOT NULL AND hw_motherboard_uuid != 'unknown'
GROUP BY hw_motherboard_uuid
HAVING COUNT(DISTINCT hw_os_info) > 1;

-- Ver licencias que han cambiado algún componente
-- (para esto necesitas tener datos históricos, se puede implementar después)

-- ============================================================================
-- ROLLBACK (en caso de necesitar revertir los cambios)
-- ============================================================================

-- DESCOMENTA ESTAS LÍNEAS SOLO SI NECESITAS REVERTIR:
-- ALTER TABLE licencias
-- DROP COLUMN hw_mac_address,
-- DROP COLUMN hw_hostname,
-- DROP COLUMN hw_os_info,
-- DROP COLUMN hw_processor,
-- DROP COLUMN hw_motherboard_uuid,
-- DROP COLUMN hw_components_updated_at;
--
-- DROP INDEX idx_mac_address ON licencias;
-- DROP INDEX idx_hostname ON licencias;
-- DROP INDEX idx_motherboard ON licencias;
