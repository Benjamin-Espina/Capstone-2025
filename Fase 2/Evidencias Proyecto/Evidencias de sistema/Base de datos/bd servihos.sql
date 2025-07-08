Table servicio {
  id_servicio int [pk]
  nombre_servicio varchar(100)
  observacion varchar(500)
}

Table subservicio {
  id_subservicio int [pk]
  id_servicio int
  nombre_subservicio varchar(100)
}

Table tipo_discapacidad {
  id_discapacidad int [pk]
  tipo_discapacidad varchar(100)
  descripcion_discapacidad varchar(200)
}

Table comuna {
  id_comuna int [pk]
  nombre_comuna varchar(30)
}

Table hospederia {
  id_hospederia int [pk]
  nombre_hospederia varchar(100)
  direccion_hospederia varchar(100)
  id_comuna int
}

Table usuario_hospederia {
  rut_usuario_hospederia int [pk]
  pasaporte_usuario_hospederia varchar(9)
  primer_nombre_usuario_hospederia varchar(20)
  segundo_nombre_usuario_hospederia varchar(20)
  primer_apellido_usuario_hospederia varchar(20)
  segundo_apellido_usuario_hospederia varchar(20)
  fecha_nacimiento timestamp
  discapacidad boolean
  id_tipo_discapacidad int
  nacionalidad varchar(30)
  id_hospederia int
  mostrar_en_reportes boolean
}

Table usuario_encargado {
  id_encargado int [pk, increment]
  rut_usuario_encargado int [unique]
  primer_nombre_usuario_encargado varchar(20)
  primer_apellido_usuario_encargado varchar(20)
  usuario varchar(20)
  contrasena varchar(60)
  id_hospederia int
  id_cargo int
}

Table administrador {
  id_admin int [pk]
  primer_nombre_admin varchar(20)
  primer_apellido_admin varchar(20)
  segundo_apellido_admin varchar(20)
  usuario varchar(20)
  contrasena varchar(60)
  id_cargo int
}

Table cargo {
  id_cargo int [pk]
  nombre_cargo varchar(50)
  descripcion_cargo varchar(200)
}

Table registros {
  id_registro int [pk]
  hora_ingreso timestamp
  hora_salida timestamp
  rut_usuario_hospederia int
  id_reporte int
  id_encargado int
}

Table reportes {
  id_reporte int [pk]
  tipo_reporte int
  fecha_reporte timestamp
  id_encargado int
  id_admin int
}

Table registro_servicio {
  id_registro int
  id_servicio int
  Indexes {
    (id_registro, id_servicio) [pk]
  }
}

// Relaciones
Ref: subservicio.id_servicio > servicio.id_servicio
Ref: usuario_hospederia.id_tipo_discapacidad > tipo_discapacidad.id_discapacidad
Ref: usuario_hospederia.id_hospederia > hospederia.id_hospederia
Ref: hospederia.id_comuna > comuna.id_comuna
Ref: usuario_encargado.id_hospederia > hospederia.id_hospederia
Ref: usuario_encargado.id_cargo > cargo.id_cargo
Ref: administrador.id_cargo > cargo.id_cargo
Ref: registros.rut_usuario_hospederia > usuario_hospederia.rut_usuario_hospederia
Ref: registros.id_reporte > reportes.id_reporte
Ref: registros.id_encargado > usuario_encargado.id_encargado
Ref: reportes.id_encargado > usuario_encargado.id_encargado
Ref: reportes.id_admin > administrador.id_admin
Ref: registro_servicio.id_registro > registros.id_registro
Ref: registro_servicio.id_servicio > servicio.id_servicio