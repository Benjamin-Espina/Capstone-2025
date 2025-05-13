from django.db import models
from django.contrib.auth.models import AbstractUser

class usuarioCustom(AbstractUser):
    rut = models.IntegerField (blank=False, unique=True)

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


