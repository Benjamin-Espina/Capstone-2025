from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import usuarioCustom
from .forms import customUserCreationForm

class UsuarioCustomAdmin(UserAdmin):
    add_form = customUserCreationForm  # <--- Esta línea es clave

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

admin.site.register(usuarioCustom, UsuarioCustomAdmin)
