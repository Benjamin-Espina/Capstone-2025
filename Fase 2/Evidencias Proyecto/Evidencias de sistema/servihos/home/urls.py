from . import views
from django.urls import path
urlpatterns = [
    path("", views.index, name="index"),
    path("registrar_encargado", views.registrar_encargado, name="registrar_encargado"),
    path('lista_encargados/', views.lista_encargados, name='lista_encargados'),
    path('lista_encargados/eliminar/<int:usuario_id>/', views.eliminar_ecargados, name='eliminar_ecargados'),
    path("iniciar_sesion", views.iniciar_sesion, name="iniciar_sesion"),
    path('cerrar_sesion/', views.cerrar_sesion, name='cerrar_sesion'),


]