from . import views
from django.urls import path

urlpatterns = [
    path("", views.index, name="index"),
    path("registrar_encargado", views.registrar_encargado, name="registrar_encargado"),
    path('lista_encargados/', views.lista_encargados, name='lista_encargados'),
    path('lista_encargados/eliminar/<int:usuario_id>/', views.eliminar_ecargados, name='eliminar_ecargados'),
    path("iniciar_sesion", views.iniciar_sesion, name="iniciar_sesion"),
    path('cerrar_sesion/', views.cerrar_sesion, name='cerrar_sesion'),
    path('subir_usuarios_hospederia/', views.subir_usuarios_hospederia, name='subir_usuarios_hospederia'),
    path('listar_hospedados/', views.listar_hospedados, name='listar_hospedados'),
    path('listar_hospedados/eliminar/<str:usuario_id>/', views.eliminar_hospedados, name='eliminar_hospedados'),
    path('listar_hospedados/editar/<str:usuario_id>/', views.editar_hospedado, name='editar_hospedado'),
    path('registrar_hospedado/', views.registrar_hospedado, name='registrar_hospedado'),
    path('perfil/<str:rut_usuario>/', views.perfil_usuario, name='perfil_usuario'),
    path('crear_servicio/', views.crear_servicio, name='crear_servicio'),
    path('listar_servicios/', views.listar_servicios, name='listar_servicios'),
    path('eliminar_servicio/<int:servicio_id>/', views.eliminar_servicio, name='eliminar_servicio'),
    path('listar_servicios/', views.listar_servicios, name='listar_servicios'),
    path('crear_subservicio/', views.crear_subservicio, name='crear_subservicio'),
    path('listar_subservicios/', views.listar_subservicios, name='listar_subservicios'),
    path('eliminar_subservicio/<int:subservicio_id>/', views.eliminar_subservicio, name='eliminar_subservicio'),
    path('listar_subservicios/', views.listar_subservicios, name='listar_subservicios'),   # path('hospedados/registrar_control_horario/<int:rut_usuario>/<str:tipo_evento>/', views.registrar_control_horario, name='registrar_control_horario'),
    path('registros_salida_entrada/', views.listar_registros_control_horario, name='listar_registros_control_horario'), 
    path('registro_usuario_hospederia/<str:usuario_id>/', views.registro_usuario_hospederia, name='registro_usuario_hospederia'),
    path('hospedados/historial_registros/<int:rut_usuario>/', views.historial_registros_usuario, name='historial_registros_usuario'),
    path('historial_registros/<int:rut_usuario>/', views.historial_registros_usuario, name='historial_registros_usuario'),
]
    