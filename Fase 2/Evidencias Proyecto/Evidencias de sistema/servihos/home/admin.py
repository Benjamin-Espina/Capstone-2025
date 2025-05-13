from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from .forms import customUserCreationForm

class UsuarioCustomAdmin(UserAdmin):
    add_form = customUserCreationForm

    list_display = ('username', 'email', 'first_name', 'last_name', 'rut', 'tipo', 'is_staff', 'is_superuser', 'is_active')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email', 'rut', 'tipo')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'rut', 'tipo', 'password1', 'password2'),
        }),
    )

    search_fields = ('username', 'first_name', 'last_name', 'rut')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')

class TipoDiscapacidadAdmin(admin.ModelAdmin):
    list_display = ('id_tipo_discapacidad', 'descripcion_tipo_discapacidad')

admin.site.register(usuarioCustom, UsuarioCustomAdmin)
admin.site.register(tipo_discapacidad, TipoDiscapacidadAdmin)
admin.site.register(hospederia)
class UsuarioHospederiaAdmin(admin.ModelAdmin):
    # __str__ del modelo se usa como primera columna por defecto, pero list_display
    # sobreescribe esto y te permite especificar todas las columnas a mostrar.
    list_display = [
        'rut_usr_hospederia',
        'pasaporte_usr_hospederia',
        'primer_nombre_usr_hospederia',
        'segundo_nombre_usr_hospederia',
        'primer_apellido_usr_hospederia',
        'segundo_apellido_usr_hospederia',
        'fecha_nacimiento_usr_hospederia',
        'discapacidad_usr_hospederia',
        'id_tipo_discapacidad', # Esto mostrará la representación string (el __str__) del tipo de discapacidad
        'nacionalidad_usr_hospederia',
        'id_hospederia', # Esto mostrará la representación string (el __str__) de la hospedería
        'mostrar_en_reportes',
    ]

    # Opcional: Añade campos para búsqueda
    search_fields = [
        'rut_usr_hospederia',
        'pasaporte_usr_hospederia',
        'primer_nombre_usr_hospederia',
        'primer_apellido_usr_hospederia',
        'nacionalidad_usr_hospederia',
    ]

    # Opcional: Añade filtros en la barra lateral derecha
    list_filter = [
        'discapacidad_usr_hospederia',
        'id_tipo_discapacidad',
        'id_hospederia',
        'mostrar_en_reportes',
        'fecha_nacimiento_usr_hospederia',
    ]

# Registra tu modelo con la clase ModelAdmin personalizada
admin.site.register(usuario_hospederia, UsuarioHospederiaAdmin)
