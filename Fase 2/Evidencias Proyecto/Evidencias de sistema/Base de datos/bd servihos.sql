CREATE TABLE `servicio` (
  `id_servicio` int PRIMARY KEY,
  `nombre_servicio` varchar(100),
  `observacion` varchar(500)
);

CREATE TABLE `subservicio` (
  `id_subservicio` int PRIMARY KEY,
  `id_servicio` int,
  `nombre_subservicio` varchar(100)
);

CREATE TABLE `tipo_discapacidad` (
  `id_discapacidad` int PRIMARY KEY,
  `tipo_discapacidad` varchar(100),
  `descripcion_discapacidad` varchar(200)
);

CREATE TABLE `comuna` (
  `id_comuna` int PRIMARY KEY,
  `nombre_comuna` varchar(30)
);

CREATE TABLE `hospederia` (
  `id_hospederia` int PRIMARY KEY,
  `nombre_hospederia` varchar(100),
  `direccion_hospederia` varchar(100),
  `id_comuna` int
);

CREATE TABLE `usuario_hospederia` (
  `rut_usuario_hospederia` int PRIMARY KEY,
  `pasaporte_usuario_hospederia` varchar(9),
  `primer_nombre_usuario_hospederia` varchar(20),
  `segundo_nombre_usuario_hospederia` varchar(20),
  `primer_apellido_usuario_hospederia` varchar(20),
  `segundo_apellido_usuario_hospederia` varchar(20),
  `fecha_nacimiento` timestamp,
  `discapacidad` boolean,
  `id_tipo_discapacidad` int,
  `nacionalidad` varchar(30),
  `id_hospederia` int,
  `mostrar_en_reportes` boolean
);

CREATE TABLE `usuario_encargado` (
  `rut_usuario_encargado` int PRIMARY KEY,
  `primer_nombre_usuario_encargado` varchar(20),
  `primer_apellido_usuario_encargado` varchar(20),
  `usuario` varchar(20),
  `contrasena` varchar(60),
  `id_hospederia` int
);

CREATE TABLE `administrador` (
  `id_admin` int PRIMARY KEY,
  `primer_nombre_admin` varchar(20),
  `primer_apellido_admin` varchar(20),
  `segundo_apellido_admin` varchar(20),
  `usuario` varchar(20),
  `contrasena` varchar(60)
);

CREATE TABLE `cargo` (
  `id_cargo` int PRIMARY KEY,
  `nombre_cargo` varchar(50),
  `descripcion_cargo` varchar(200)
);

CREATE TABLE `registros` (
  `id_registro` int PRIMARY KEY,
  `hora_ingreso` timestamp,
  `hora_salida` timestamp,
  `rut_usuario_hospederia` int,
  `id_reporte` int
);

CREATE TABLE `reportes` (
  `id_reporte` int PRIMARY KEY,
  `tipo_reporte` int,
  `fecha_reporte` timestamp,
  `rut_usuario_encargado` int,
  `id_admin` int
);

CREATE TABLE `registro_servicio` (
  `id_registro` int,
  `id_servicio` int,
  PRIMARY KEY (`id_registro`, `id_servicio`)
);

ALTER TABLE `subservicio` ADD FOREIGN KEY (`id_servicio`) REFERENCES `servicio` (`id_servicio`);

ALTER TABLE `usuario_hospederia` ADD FOREIGN KEY (`id_tipo_discapacidad`) REFERENCES `tipo_discapacidad` (`id_discapacidad`);

ALTER TABLE `usuario_hospederia` ADD FOREIGN KEY (`id_hospederia`) REFERENCES `hospederia` (`id_hospederia`);

ALTER TABLE `hospederia` ADD FOREIGN KEY (`id_comuna`) REFERENCES `comuna` (`id_comuna`);

ALTER TABLE `usuario_encargado` ADD FOREIGN KEY (`id_hospederia`) REFERENCES `hospederia` (`id_hospederia`);

ALTER TABLE `registros` ADD FOREIGN KEY (`rut_usuario_hospederia`) REFERENCES `usuario_hospederia` (`rut_usuario_hospederia`);

ALTER TABLE `registros` ADD FOREIGN KEY (`id_reporte`) REFERENCES `reportes` (`id_reporte`);

ALTER TABLE `reportes` ADD FOREIGN KEY (`rut_usuario_encargado`) REFERENCES `usuario_encargado` (`rut_usuario_encargado`);

ALTER TABLE `reportes` ADD FOREIGN KEY (`id_admin`) REFERENCES `administrador` (`id_admin`);

ALTER TABLE `registro_servicio` ADD FOREIGN KEY (`id_registro`) REFERENCES `registros` (`id_registro`);

ALTER TABLE `registro_servicio` ADD FOREIGN KEY (`id_servicio`) REFERENCES `servicio` (`id_servicio`);
