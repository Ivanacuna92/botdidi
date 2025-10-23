-- Tabla para registrar cuántos clientes procesa el bot diariamente
CREATE TABLE IF NOT EXISTS `bot_ejecuciones` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `fecha` DATE NOT NULL,
  `clientes_procesados` INT(11) NOT NULL DEFAULT 0,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_fecha` (`fecha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
