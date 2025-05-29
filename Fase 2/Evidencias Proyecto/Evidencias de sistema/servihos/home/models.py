from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
import re

def validate_rut(value):
    rut = str(value).upper()
    if not re.match(r'^\d{7,8}-[0-9K]$', rut):
        raise ValidationError("El RUT debe tener el formato 12345678-9 o 12345678-K (con guion).")

    body, dv = rut.split('-')
    reverse_digits = map(int, reversed(body))
    factors = [2, 3, 4, 5, 6, 7] * 2
    s = sum(d * f for d, f in zip(reverse_digits, factors))
    res = 11 - (s % 11)
    if res == 11:
        expected_dv = '0'
    elif res == 10:
        expected_dv = 'K'
    else:
        expected_dv = str(res)

    if dv != expected_dv:
        raise ValidationError("RUT inválido, dígito verificador incorrecto.")

class usuarioCustom(AbstractUser):
    rut = models.CharField(
        max_length=10,
        unique=True,
        validators=[validate_rut, MinLengthValidator(8)],
        blank=False
    )

    REQUIRED_FIELDS = ['rut']

    TIPO_CHOICES = [
        ('administrador', 'Administrador'),
        ('encargado', 'Encargado'),
    ]

    tipo = models. CharField(
        max_length=25,
        choices=TIPO_CHOICES,
        default='encargado',
        blank= True,
        verbose_name="Tipo de usuario"
    )

    def es_administrador(self):
        return self.tipo == 'administrador'

    def es_encargado(self):
        return self.tipo == 'encargado'
    pass

class tipo_discapacidad(models.Model):
    id_tipo_discapacidad = models.AutoField(primary_key=True)
    descripcion_tipo_discapacidad = models.CharField(max_length=150, blank=False)

    def __str__(self):
        return self.descripcion_tipo_discapacidad
    
class hospederia(models.Model):
    id_hospederia = models.AutoField(primary_key=True)
    nombre_hospederia = models.CharField(max_length=50, blank=False)
    direccion_hospederia = models.CharField(max_length=100, blank=False)

    def __str__(self):
        return self.nombre_hospederia    

class usuario_hospederia(models.Model):
    rut_usr_hospederia = models.IntegerField(primary_key=True,blank=False, unique=True)
    pasaporte_usr_hospederia = models.CharField(max_length=25, blank=False)
    primer_nombre_usr_hospederia = models.CharField(max_length=25, blank=False)
    segundo_nombre_usr_hospederia = models.CharField(max_length=25, blank=False)
    primer_apellido_usr_hospederia = models.CharField(max_length=25, blank=False)
    segundo_apellido_usr_hospederia = models.CharField(max_length=25, blank=False)
    fecha_nacimiento_usr_hospederia = models.DateField(blank=False)
    discapacidad_usr_hospederia = models.BooleanField(blank=False)
    id_tipo_discapacidad = models.ForeignKey(tipo_discapacidad, on_delete=models.CASCADE, blank=True, null=True)
    nacionalidad_usr_hospederia = models.CharField(max_length=25, blank=False)
    id_hospederia = models.ForeignKey(hospederia, on_delete=models.CASCADE, blank=True, null=True)
    mostrar_en_reportes = models.BooleanField(blank=False)

    def __str__(self):
        return self.primer_nombre_usr_hospederia


class Servicio(models.Model):
    nombre_servicio = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre_servicio

class SubServicio(models.Model):
    nombre_subservicio = models.CharField(max_length=100)
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='subservicios')

    def __str__(self):
        return f"{self.nombre_subservicio} ({self.servicio.nombre_servicio})"

class RegistroControlHorario(models.Model):
    usuario = models.ForeignKey(
        'usuario_hospederia',
        on_delete=models.CASCADE,
        related_name='registros_control_horario'
    )

    fecha_hora = models.DateTimeField(
        auto_now_add=True, # ¡Cambio aquí!
        blank=False,
        help_text="Fecha y hora exactas del registro (entrada o salida)."
    )

    TIPO_EVENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]
    tipo_evento = models.CharField(
        max_length=10,
        choices=TIPO_EVENTO_CHOICES,
        blank=False,
        help_text="Indica si es un registro de entrada o salida."
    )

    notas = models.TextField(
        blank=True,
        null=True,
        help_text="Añade notas adicionales en caso de ser necesario."
    )

    class Meta:
        ordering = ['fecha_hora']

    def __str__(self):
        return f"{self.get_tipo_evento_display()} de {self.usuario.primer_nombre_usr_hospederia} (RUT: {self.usuario.rut_usr_hospederia}) - {self.fecha_hora.strftime('%d-%m-%Y %H:%M')}"