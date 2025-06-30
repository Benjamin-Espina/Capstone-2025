from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db import transaction, IntegrityError
from datetime import date, timedelta
from django.db.models import Q, Count
from django.utils import timezone
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.forms.models import model_to_dict

#Importar modelos
from .models import (usuario_hospederia, tipo_discapacidad, hospederia, Servicio, SubServicio, 
                     registroHorarioHospederia, fun_HorarioEntrada, fun_HorarioSalida, HistorialServicioUsuario)

#Importar formularios
from .forms import ServicioForm, SubServicioForm, customUserCreationForm, subir_CSV_usr_hospederia, UsuarioHospederiaFormEdit, HistorialServicioUsuarioForm

#Importar ependencies externas
import pandas as pd
import io
from datetime import datetime
import re

obtener_usuarios= get_user_model()

#Decoradores
def es_administrador(user):
    return user.is_authenticated and (hasattr(user, 'tipo') and user.tipo == 'administrador' or user.is_superuser)

#Vistas
def cerrar_sesion(request):
    logout(request)
    return redirect('index')

def index(request):
    # Total de veces que se han usado servicios (sin subservicios)
    total_servicios_usados = HistorialServicioUsuario.objects.filter(subservicio=None).count()
    # Total de veces que se han usado subservicios
    total_subservicios_usados = HistorialServicioUsuario.objects.filter(servicio=None, subservicio__isnull=False).count()
    total_usuarios_hospederia = usuario_hospederia.objects.count()
    hoy = timezone.localdate()
    usuarios_ingresaron_hoy = registroHorarioHospederia.objects.filter(hora_entrada__date=hoy).values('usuario').distinct().count()
    usuarios_ingresaron_hoy = min(usuarios_ingresaron_hoy, 20)

    # Conteo individual de cada servicio y subservicio
    servicios = Servicio.objects.all()
    subservicios = SubServicio.objects.select_related('servicio').all()
    conteo_servicios = {}
    for servicio in servicios:
        if not servicio.subservicios.exists():
            conteo_servicios[servicio.nombre_servicio] = HistorialServicioUsuario.objects.filter(servicio=servicio, subservicio=None).count()
    for sub in subservicios:
        key = f"{sub.servicio.nombre_servicio} - {sub.nombre_subservicio}"
        conteo_servicios[key] = HistorialServicioUsuario.objects.filter(subservicio=sub, servicio=None).count()

    return render(request, "index.html", {
        'total_servicios': total_servicios_usados,
        'total_subservicios': total_subservicios_usados,
        'total_usuarios_hospederia': total_usuarios_hospederia,
        'usuarios_ingresaron_hoy': usuarios_ingresaron_hoy,
        'conteo_servicios': conteo_servicios,
    })

@login_required
@user_passes_test(es_administrador, login_url='iniciar_sesion')
def registrar_encargado(request):
    if hasattr(request.user, 'tipo') and request.user.tipo == 'encargado':
        return redirect('index')
    if request.method == 'POST':
        form = customUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.tipo = 'encargado' 
            user.save()
            return redirect('index')
    else:
        form = customUserCreationForm()
    return render(request, 'autenticacion/registrar_encargado.html', {'form': form})

def lista_encargados(request):
    if hasattr(request.user, 'tipo') and request.user.tipo == 'encargado':
        return redirect('index')
    usuarios = obtener_usuarios.objects.filter(tipo='encargado')
    return render(request, 'autenticacion/listar_encargados.html', {'usuarios': usuarios})


def eliminar_ecargados(request, usuario_id):
    if request.method == 'POST':
        usuario = get_object_or_404(obtener_usuarios, id=usuario_id)
        usuario.delete()
        messages.success(request, f'El usuario "{usuario.username}" ha sido eliminado correctamente.')
        return redirect('lista_encargados')
    else:
        # Si alguien intenta acceder a la eliminación por GET, puedes redirigirlo o mostrar un error.
        return redirect('lista_encargados')
    

def listar_hospedados(request):
    if request.user.is_superuser or (hasattr(request.user, 'tipo') and request.user.tipo == 'administrador'):
        return redirect('index')
    busqueda = request.GET.get("busqueda", "").strip()
    usuarios_hospedados = usuario_hospederia.objects.all()

    if busqueda:
        usuarios_hospedados = usuarios_hospedados.filter(
            Q(rut_usr_hospederia__icontains=busqueda) |
            Q(primer_nombre_usr_hospederia__icontains=busqueda) |
            Q(segundo_nombre_usr_hospederia__icontains=busqueda) |
            Q(primer_apellido_usr_hospederia__icontains=busqueda) |
            Q(segundo_apellido_usr_hospederia__icontains=busqueda)
        )

    # Para cada usuario, obtener los servicios y subservicios del último registro
    usuarios_servicios = []
    for usuario in usuarios_hospedados:
        # Buscar la última fecha de registro de servicios
        ultimo_registro = HistorialServicioUsuario.objects.filter(usuario=usuario).order_by('-fecha').first()
        if ultimo_registro:
            fecha_ultima = ultimo_registro.fecha
            servicios_simples = HistorialServicioUsuario.objects.filter(usuario=usuario, fecha=fecha_ultima, subservicio=None).select_related('servicio')
            subservicios = HistorialServicioUsuario.objects.filter(usuario=usuario, fecha=fecha_ultima, servicio=None).select_related('subservicio')
        else:
            servicios_simples = []
            subservicios = []
        usuarios_servicios.append({
            'usuario': usuario,
            'servicios_simples': servicios_simples,
            'subservicios': subservicios,
        })

    return render(request, 'servicios/listar_hospedados.html', {
        'usuarios_servicios': usuarios_servicios,
        'busqueda': busqueda,
    })

def eliminar_hospedados(request, usuario_id):
    if request.method == 'POST':
        usuarios_hospedados_eliminar = get_object_or_404(usuario_hospederia, rut_usr_hospederia=usuario_id)
        usuarios_hospedados_eliminar.delete()
        messages.success(request, f'El usuario "{usuarios_hospedados_eliminar.primer_nombre_usr_hospederia}" ha sido eliminado correctamente.')
        return redirect('listar_hospedados')
    else:
        # Si alguien intenta acceder a la eliminación por GET, puedes redirigirlo o mostrar un error.
        return redirect('listar_hospedados')
    

def editar_hospedado(request, usuario_id):
    if request.user.is_superuser or (hasattr(request.user, 'tipo') and request.user.tipo == 'administrador'):
        return redirect('index')
    usuario = get_object_or_404(usuario_hospederia, rut_usr_hospederia=usuario_id)

    if request.method == 'POST':
        form = UsuarioHospederiaFormEdit(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect('listar_hospedados')
    else:
        form = UsuarioHospederiaFormEdit(instance=usuario)

    return render(request, 'servicios/editar_hospedados.html', {'form': form, 'usuario': usuario})

def registrar_hospedado(request):
    if request.user.is_superuser or (hasattr(request.user, 'tipo') and request.user.tipo == 'administrador'):
        return redirect('index')
    if request.method == 'POST':
        form = UsuarioHospederiaFormEdit(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.tipo = 'encargado' 
            user.save()
            return redirect('index')
    else:
        form = UsuarioHospederiaFormEdit()

    return render(request, 'servicios/registrar_hospedado.html', {'form': form})

def iniciar_sesion(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                form.add_error(None, 'Nombre de usuario o contraseña incorrectos.')
        else:
            pass
    else:
        form = AuthenticationForm()
    return render(request, 'autenticacion/iniciar_sesion.html', {'form': form})

def calcular_edad(fecha_nacimiento):
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

def perfil_usuario(request, rut_usuario):
    if request.user.is_superuser or (hasattr(request.user, 'tipo') and request.user.tipo == 'administrador'):
        return redirect('index')
    usuario = get_object_or_404(usuario_hospederia, rut_usr_hospederia=rut_usuario)
    edad = calcular_edad(usuario.fecha_nacimiento_usr_hospederia)

    # Buscar el último registro de horario si existe
    ultimo_registro = registroHorarioHospederia.objects.filter(usuario=usuario).order_by('-hora_entrada').first()

    # Conteo total de servicios y subservicios
    historial_qs = HistorialServicioUsuario.objects.filter(usuario=usuario)
    servicios = list(Servicio.objects.all())
    subservicios = list(SubServicio.objects.select_related('servicio').all())
    conteo_servicios = {}
    for servicio in servicios:
        if not servicio.subservicios.exists():
            conteo_servicios[servicio.nombre_servicio] = historial_qs.filter(servicio=servicio, subservicio=None).count()
    for sub in subservicios:
        key = f"{sub.servicio.nombre_servicio} - {sub.nombre_subservicio}"
        conteo_servicios[key] = historial_qs.filter(subservicio=sub, servicio=None).count()

    context = {
        'usuario': usuario,
        'edad': edad,
        'ultimo_registro': ultimo_registro,
        'conteo_servicios': conteo_servicios,
    }

    return render(request, 'servicios/perfil_usuario.html', context)

def crear_servicio(request):
    if hasattr(request.user, 'tipo') and request.user.tipo == 'encargado':
        return redirect('index')
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('crear_servicio')  # o redirige a una lista si la tienes
    else:
        form = ServicioForm()
    return render(request, 'servicios/crear_servicio.html', {'form': form})

def listar_servicios(request):
    if hasattr(request.user, 'tipo') and request.user.tipo == 'encargado':
        return redirect('index')
    servicios = Servicio.objects.all()
    return render(request, 'servicios/listar_servicios.html', {'servicios': servicios})

def inhabilitar_servicio(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)
    servicio.activo = False
    servicio.save()
    messages.success(request, f"Servicio '{servicio.nombre_servicio}' inhabilitado correctamente.")
    return redirect('listar_servicios')

def habilitar_servicio(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)
    servicio.activo = True
    servicio.save()
    messages.success(request, f"Servicio '{servicio.nombre_servicio}' habilitado correctamente.")
    return redirect('listar_servicios')

def eliminar_servicio(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)
    if request.method == 'POST':
        servicio.activo = False
        servicio.save()
        messages.success(request, f"Servicio '{servicio.nombre_servicio}' inhabilitado correctamente.")
        return redirect('listar_servicios')
    return redirect('listar_servicios')

def crear_subservicio(request):
    if hasattr(request.user, 'tipo') and request.user.tipo == 'encargado':
        return redirect('index')
    if request.method == 'POST':
        form = SubServicioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_subservicios')  # o a donde tú necesites
    else:
        form = SubServicioForm()
    return render(request, 'servicios/crear_subservicio.html', {'form': form})

def listar_subservicios(request):
    if hasattr(request.user, 'tipo') and request.user.tipo == 'encargado':
        return redirect('index')
    subservicios = SubServicio.objects.select_related('servicio').all()
    return render(request, 'servicios/listar_subservicios.html', {'subservicios': subservicios})

def inhabilitar_subservicio(request, subservicio_id):
    sub = get_object_or_404(SubServicio, id=subservicio_id)
    sub.activo = False
    sub.save()
    messages.success(request, f"Subservicio '{sub.nombre_subservicio}' inhabilitado correctamente.")
    return redirect('listar_subservicios')

def habilitar_subservicio(request, subservicio_id):
    sub = get_object_or_404(SubServicio, id=subservicio_id)
    sub.activo = True
    sub.save()
    messages.success(request, f"Subservicio '{sub.nombre_subservicio}' habilitado correctamente.")
    return redirect('listar_subservicios')

def eliminar_subservicio(request, subservicio_id):
    sub = get_object_or_404(SubServicio, id=subservicio_id)
    if request.method == 'POST':
        sub.activo = False
        sub.save()
        messages.success(request, f"Subservicio '{sub.nombre_subservicio}' inhabilitado correctamente.")
    return redirect('listar_subservicios')

#Mostral el historial de registros de un usuario
def historial_registros_usuario(request, rut_usuario):
    if request.user.is_superuser or (hasattr(request.user, 'tipo') and request.user.tipo == 'administrador'):
        return redirect('index')
    usuario = get_object_or_404(usuario_hospederia, rut_usr_hospederia=rut_usuario)

    # Filtro por fecha
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    historial_qs = HistorialServicioUsuario.objects.filter(usuario=usuario)
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            historial_qs = historial_qs.filter(fecha__gte=fecha_desde_dt)
        except ValueError:
            messages.error(request, "Formato de fecha 'Desde' inválido. Use AAAA-MM-DD.")
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            historial_qs = historial_qs.filter(fecha__lte=fecha_hasta_dt)
        except ValueError:
            messages.error(request, "Formato de fecha 'Hasta' inválido. Use AAAA-MM-DD.")

    historial_qs = historial_qs.order_by('-fecha')

    # Para la tabla: agrupamos por fecha
    fechas = sorted(set(historial_qs.values_list('fecha', flat=True)), reverse=True)
    servicios = list(Servicio.objects.all())
    subservicios = list(SubServicio.objects.select_related('servicio').all())

    historial_con_servicios = []
    for fecha in fechas:
        servicios_dict = {}
        # Servicios simples (sin subservicios)
        for servicio in servicios:
            if not servicio.subservicios.exists():
                count = historial_qs.filter(fecha=fecha, servicio=servicio, subservicio=None).count()
                servicios_dict[servicio.nombre_servicio] = count
        # Subservicios
        for sub in subservicios:
            count = historial_qs.filter(fecha=fecha, subservicio=sub, servicio=None).count()
            key = f"{sub.servicio.nombre_servicio} - {sub.nombre_subservicio}"
            servicios_dict[key] = count
        historial_con_servicios.append({
            'fecha': fecha,
            'servicios': servicios_dict
        })

    # Conteo total por servicio y subservicio
    conteo_servicios = {}
    for servicio in servicios:
        if not servicio.subservicios.exists():
            conteo_servicios[servicio.nombre_servicio] = historial_qs.filter(servicio=servicio, subservicio=None).count()
    for sub in subservicios:
        key = f"{sub.servicio.nombre_servicio} - {sub.nombre_subservicio}"
        conteo_servicios[key] = historial_qs.filter(subservicio=sub, servicio=None).count()

    context = {
        'usuario': usuario,
        'historial_con_servicios': historial_con_servicios,
        'conteo_servicios': conteo_servicios,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    return render(request, 'servicios/historial_registros.html', context)

from .models import RegistroSubServicio, RegistroServicioSimple, Servicio, SubServicio, HistorialServicioUsuario

def registro_usuario_hospederia(request, rut_usuario):
    if request.user.is_superuser or (hasattr(request.user, 'tipo') and request.user.tipo == 'administrador'):
        return redirect('index')
    usuario = get_object_or_404(usuario_hospederia, rut_usr_hospederia=rut_usuario)
    preview_entrada = fun_HorarioEntrada()
    preview_salida = fun_HorarioSalida(preview_entrada)
    hoy = timezone.localdate()
    fecha_salida = hoy + timedelta(days=1)
    existe_registro_hoy = registroHorarioHospederia.objects.filter(
        usuario=usuario,
        hora_entrada__date=hoy
    ).exists()

    if request.method == 'POST':
        form = HistorialServicioUsuarioForm(request.POST)
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
            # Crear registro de entrada/salida
            registroHorarioHospederia.objects.create(
                usuario=usuario,
                hora_entrada=preview_entrada,
                hora_salida=fun_HorarioSalida(preview_entrada)
            )
            # Servicios simples
            servicios_simples = [s.pk if hasattr(s, 'pk') else s for s in form.cleaned_data['servicios_simples']]
            pernoctacion = Servicio.objects.filter(nombre_servicio__iexact='Pernoctación').first()
            if pernoctacion and pernoctacion.pk not in servicios_simples:
                servicios_simples.append(pernoctacion.pk)
            for servicio_id in servicios_simples:
                HistorialServicioUsuario.objects.get_or_create(
                    usuario=usuario,
                    fecha=fecha,
                    servicio_id=servicio_id,
                    subservicio=None
                )
            # Subservicios
            observacion = form.cleaned_data.get('observacion', '')
            for field_name in form.fields:
                if field_name.startswith('subservicios_'):
                    for subservicio in form.cleaned_data[field_name]:
                        subservicio_id = subservicio.pk if hasattr(subservicio, 'pk') else subservicio
                        subservicio_obj = SubServicio.objects.get(pk=subservicio_id)
                        if subservicio_obj.servicio.nombre_servicio == 'Asistencia Ambulatoria':
                            HistorialServicioUsuario.objects.get_or_create(
                                usuario=usuario,
                                fecha=fecha,
                                servicio=None,
                                subservicio_id=subservicio_id,
                                defaults={'observacion': observacion}
                            )
                        else:
                            HistorialServicioUsuario.objects.get_or_create(
                                usuario=usuario,
                                fecha=fecha,
                                servicio=None,
                                subservicio_id=subservicio_id
                            )
            messages.success(request, 'Servicios registrados correctamente.')
            return redirect('perfil_usuario', rut_usuario=usuario.rut_usr_hospederia)
    else:
        form = HistorialServicioUsuarioForm(initial={'fecha': fecha_salida})

    servicios = Servicio.objects.prefetch_related('subservicios').all()
    return render(request, 'servicios/registro_usuario_hospederia.html', {
        'usuario': usuario,
        'preview_entrada': preview_entrada,
        'preview_salida': preview_salida,
        'existe_registro_hoy': existe_registro_hoy,
        'servicios': servicios,
        'form': form,
    })



@login_required
@user_passes_test(es_administrador, login_url='iniciar_sesion')
def subir_usuarios_hospederia(request):
    if hasattr(request.user, 'tipo') and request.user.tipo == 'encargado':
        return redirect('index')
    if request.method == 'POST':
        form = subir_CSV_usr_hospederia(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['csv_file']
            file_extension = file.name.split('.')[-1].lower()

            if file_extension not in ['csv', 'xls', 'xlsx']:
                messages.error(request, "Tipo de archivo no soportado. Sube un archivo .csv, .xls o .xlsx.")
                return render(request, 'servicios/subir_usuarios.html', {'form': form})

            try:
                file_content = io.BytesIO(file.read())

                if file_extension == 'csv':
                    try:
                        df = pd.read_csv(file_content, encoding='utf-8')
                    except Exception:
                        try:
                            file_content.seek(0)
                            df = pd.read_csv(file_content, encoding='latin-1')
                        except Exception as e_latin1:
                            messages.error(f"Error al leer el archivo CSV. Asegúrate de que sea un CSV válido y esté codificado en UTF-8 o LATIN-1. Detalles: {e_latin1}")
                            return render(request, 'servicios/subir_usuarios.html', {'form': form})

                elif file_extension in ['xls', 'xlsx']:
                    try:
                        df = pd.read_excel(file_content)
                    except Exception as e:
                        messages.error(f"Error al leer el archivo Excel. Asegúrate de que sea un archivo .xls o .xlsx válido. Detalles: {e}")
                        return render(request, 'servicios/subir_usuarios.html', {'form': form})

                expected_columns = [
                    'rut_usr_hospederia', 'pasaporte_usr_hospederia',
                    'primer_nombre_usr_hospederia', 'segundo_nombre_usr_hospederia',
                    'primer_apellido_usr_hospederia', 'segundo_apellido_usr_hospederia',
                    'fecha_nacimiento_usr_hospederia', 'discapacidad_usr_hospederia',
                    'id_tipo_discapacidad', # Esperamos la descripción
                    'nacionalidad_usr_hospederia',
                    'id_hospederia', # Esperamos el nombre
                    'mostrar_en_reportes'
                ]

                if not all(col in df.columns for col in expected_columns):
                    missing_cols = [col for col in expected_columns if col not in df.columns]
                    messages.error(f"El archivo no contiene todas las columnas requeridas. Faltan: {', '.join(missing_cols)}")
                    return render(request, 'servicios/subir_usuarios.html', {'form': form})


                created_count = 0
                updated_count = 0
                errors = []
                # Keep track of created FKs within this import transaction if needed
                # created_disabilities = set()
                # created_hospederias = set()


                def parse_boolean(value):
                    if pd.isna(value):
                        return False
                    if isinstance(value, bool):
                        return value
                    value_str = str(value).lower().strip()
                    if value_str in ['true', 'verdadero', 'sí', 'si', 'yes', '1']:
                        return True
                    if value_str in ['false', 'falso', 'no', 'not', '0']:
                        return False
                    return False


                # Usar transacción para asegurar que la operación sea atómica (todo o nada)
                with transaction.atomic():
                    for index, row in df.iterrows():
                        row_num = index + 2 # Número de fila en el archivo

                        try:
                            # --- Procesar el RUT: Limpiar puntos y dígito verificador ---
                            raw_rut = row.get('rut_usr_hospederia')

                            if pd.isna(raw_rut) or str(raw_rut).strip() == '':
                                errors.append(f"Fila {row_num}: RUT vacío o inválido.")
                                continue

                            rut_str = str(raw_rut).strip()
                            rut_str = rut_str.replace('.', '')
                            rut_str = rut_str.split('-')[0]

                            try:
                                rut = int(rut_str)
                            except (ValueError, TypeError):
                                errors.append(f"Fila {row_num}: El RUT '{raw_rut}' ('{rut_str}' después de limpieza) no es un número válido.")
                                continue
                            # --- Fin procesamiento RUT ---


                            # Extraer otros datos (manejar posibles valores NaN/None de pandas)
                            pasaporte = str(row.get('pasaporte_usr_hospederia', '')).strip()
                            primer_nombre = str(row.get('primer_nombre_usr_hospederia', '')).strip()
                            segundo_nombre = str(row.get('segundo_nombre_usr_hospederia', '')).strip()
                            primer_apellido = str(row.get('primer_apellido_usr_hospederia', '')).strip()
                            segundo_apellido = str(row.get('segundo_apellido_usr_hospederia', '')).strip()
                            fecha_nacimiento_raw = row.get('fecha_nacimiento_usr_hospederia')
                            discapacidad_val = row.get('discapacidad_usr_hospederia')
                            tipo_discapacidad_desc = str(row.get('id_tipo_discapacidad', '')).strip()
                            nacionalidad = str(row.get('nacionalidad_usr_hospederia', '')).strip()
                            hospederia_nombre = str(row.get('id_hospederia', '')).strip()
                            mostrar_en_reportes_val = row.get('mostrar_en_reportes')


                            # Validaciones y Conversiones
                            if pasaporte == '':
                                errors.append(f"Fila {row_num}: Pasaporte vacío.")
                                continue
                            if primer_nombre == '':
                                errors.append(f"Fila {row_num}: Primer nombre vacío.")
                                continue
                            if segundo_nombre == '': # Según tu modelo, este es requerido
                                errors.append(f"Fila {row_num}: Segundo nombre vacío.")
                                continue

                            if primer_apellido == '':
                                errors.append(f"Fila {row_num}: Primer apellido vacío.")
                                continue
                            if segundo_apellido == '': # Según tu modelo, este es requerido
                                errors.append(f"Fila {row_num}: Segundo apellido vacío.")
                                continue


                            # Parsear Fecha de Nacimiento
                            fecha_nacimiento = None
                            if pd.isna(fecha_nacimiento_raw) or str(fecha_nacimiento_raw).strip() == '':
                                errors.append(f"Fila {row_num}: Fecha de nacimiento vacía.")
                                continue
                            try:
                                if isinstance(fecha_nacimiento_raw, datetime):
                                    fecha_nacimiento = fecha_nacimiento_raw.date()
                                else:
                                    # Intentar parsear string asumiendo formato

                                    # Intentar parsear string asumiendo formato YYYY-MM-DD (ajusta si es necesario)
                                    fecha_nacimiento = datetime.strptime(str(fecha_nacimiento_raw).split(' ')[0], '%Y-%m-%d').date()
                            except (ValueError, TypeError):
                                errors.append(f"Fila {row_num}: Formato de fecha de nacimiento inválido ('{fecha_nacimiento_raw}'). Esperado YYYY-MM-DD.")
                                continue

                            # Parsear Booleanos
                            discapacidad = parse_boolean(discapacidad_val)
                            mostrar_en_reportes = parse_boolean(mostrar_en_reportes_val)

                            # --- Buscar o Crear Tipo de Discapacidad (ForeignKey) ---
                            tipo_discapacidad_obj = None # Default a None
                            # Solo buscamos/creamos si la discapacidad está marcada como True Y se proporciona una descripción
                            if discapacidad:
                                tipo_discapacidad_desc = str(row.get('id_tipo_discapacidad', '')).strip()
                                if tipo_discapacidad_desc == '':
                                    # Mantener este error: si hay discapacidad, se debe especificar el tipo
                                    errors.append(f"Fila {row_num}: Discapacidad marcada como Sí, pero el tipo de discapacidad está vacío.")
                                    continue # Considera esto un error crítico para la fila
                                else:
                                    try:
                                        # Usar get_or_create para obtener o crear el TipoDiscapacidad
                                        # Usamos __iexact para buscar sin importar mayúsculas/minúsculas
                                        tipo_discapacidad_obj, created_discapacidad = tipo_discapacidad.objects.get_or_create(
                                            descripcion_tipo_discapacidad__iexact=tipo_discapacidad_desc,
                                            defaults={'descripcion_tipo_discapacidad': tipo_discapacidad_desc} # Usa la descripción exacta si se crea
                                        )
                                        # Opcional: agregar mensaje si se creó un nuevo tipo de discapacidad
                                        # if created_discapacidad:
                                        #      messages.info(request, f"Se creó nuevo tipo de discapacidad: '{tipo_discapacidad_desc}'")
                                    except Exception as e:
                                        errors.append(f"Fila {row_num}: Error al buscar/crear Tipo Discapacidad '{tipo_discapacidad_desc}'. Detalles: {e}")
                                        continue # Salta esta fila si falla la creación/búsqueda del FK

                            # --- Buscar o Crear Hospederia (ForeignKey) ---
                            hospederia_obj = None # Default a None
                            hospederia_nombre = str(row.get('id_hospederia', '')).strip()

                            # Solo buscamos/creamos si se proporciona un nombre de hospedería
                            if hospederia_nombre != '':
                                try:
                                    # Usar get_or_create para obtener o crear la Hospederia
                                    # Usamos __iexact para buscar sin importar mayúsculas/minúsculas
                                    # Necesitamos proporcionar un valor por defecto para 'direccion_hospederia' que es blank=False
                                    hospederia_obj, created_hospederia = hospederia.objects.get_or_create(
                                        nombre_hospederia__iexact=hospederia_nombre,
                                        defaults={
                                            'nombre_hospederia': hospederia_nombre, # Usa el nombre exacto si se crea
                                            'direccion_hospederia': 'Dirección no especificada en archivo' # Valor por defecto
                                            }
                                    )
                                    # Opcional: agregar mensaje si se creó una nueva hospedería
                                    # if created_hospederia:
                                    #      messages.info(request, f"Se creó nueva hospedería: '{hospederia_nombre}'")
                                except Exception as e:
                                    errors.append(f"Fila {row_num}: Error al buscar/crear Hospedería '{hospederia_nombre}'. Detalles: {e}")
                                    continue # Salta esta fila si falla la creación/búsqueda del FK


                            if nacionalidad == '':
                                errors.append(f"Fila {row_num}: Nacionalidad vacía.")
                                continue

                            # --- Crear o Actualizar el objeto usuario_hospederia ---
                            # Usamos el 'rut' entero limpio y los objetos FK encontrados o creados
                            obj, created = usuario_hospederia.objects.update_or_create(
                                rut_usr_hospederia=rut, # Usa el RUT entero limpio
                                defaults={
                                    'pasaporte_usr_hospederia': pasaporte,
                                    'primer_nombre_usr_hospederia': primer_nombre,
                                    'segundo_nombre_usr_hospederia': segundo_nombre,
                                    'primer_apellido_usr_hospederia': primer_apellido,
                                    'segundo_apellido_usr_hospederia': segundo_apellido,
                                    'fecha_nacimiento_usr_hospederia': fecha_nacimiento,
                                    'discapacidad_usr_hospederia': discapacidad,
                                    'id_tipo_discapacidad': tipo_discapacidad_obj, # Asigna el objeto o None
                                    'nacionalidad_usr_hospederia': nacionalidad,
                                    'id_hospederia': hospederia_obj, # Asigna el objeto o None
                                    'mostrar_en_reportes': mostrar_en_reportes,
                                }
                            )
                            if created:
                                created_count += 1
                            else:
                                updated_count += 1

                        except IntegrityError as e:
                            errors.append(f"Fila {row_num}: Error de integridad de datos (posible duplicado con RUT {rut} u otro error de base de datos). Detalles: {e}")
                        except Exception as e:
                            # Capturar cualquier otro error inesperado durante el procesamiento de la fila
                            errors.append(f"Fila {row_num}: Error inesperado al procesar la fila con RUT {rut}. Detalles: {e}")


                    # Si hay errores registrados, lanzar una excepción para activar el rollback de la transacción
                    if errors:
                        raise Exception("Errores encontrados durante la importación. Revirtiendo cambios.")


                # --- Mostrar resultados si la transacción fue exitosa ---
                if created_count > 0 or updated_count > 0:
                    success_message = f"Proceso de importación finalizado exitosamente: {created_count} usuarios creados"
                    if updated_count > 0:
                        success_message += f" y {updated_count} usuarios actualizados"
                    success_message += "."
                    messages.success(request, success_message)
                elif not errors: # Si no hubo errores y no se creó/actualizó nada
                    messages.info(request, "No se procesó ningún usuario (archivo vacío o sin datos válidos/nuevos).")


            except Exception as e:
                # Capturar errores generales (ej: lectura de archivo) o la excepción lanzada para el rollback
                messages.error(request, f"Ocurrió un error durante la importación. Detalles: {e}")
                # Si hubo errores de fila que causaron el rollback, mostrarlos también
                if errors:
                    messages.error(request, f"Se encontraron los siguientes errores de fila que causaron la reversión:")
                    # Mostrar solo los primeros errores para evitar una lista enorme
                    for error in errors[:10]:
                        messages.warning(request, error)
                    if len(errors) > 10:
                        messages.warning(request, f"...y {len(errors) - 10} errores más. Consulta los logs del servidor para ver todos los errores.")


            # Después de procesar (ya sea éxito o error con mensajes), mostrar la misma página
            return render(request, 'servicios/subir_usuarios.html', {'form': form})

    else:
        # Si es una solicitud GET, simplemente muestra el formulario vacío
        form = subir_CSV_usr_hospederia()

    return render(request, 'servicios/subir_usuarios.html', {'form': form})


@login_required
def listar_registros_control_horario(request):
    # Obtener todos los registros de control horario, ordenados por fecha y hora descendente
    registros = registroHorarioHospederia.objects.all().order_by('-fecha_hora')

    busqueda_rut = request.GET.get("rut_busqueda", "").strip()
    busqueda_nombre = request.GET.get("nombre_busqueda", "").strip()
    tipo_evento_filtro = request.GET.get("tipo_evento_filtro", "").strip()
    fecha_desde_str = request.GET.get("fecha_desde", "").strip()
    fecha_hasta_str = request.GET.get("fecha_hasta", "").strip()

    if busqueda_rut:
        registros = registros.filter(usuario__rut_usr_hospederia__icontains=busqueda_rut)
    
    if busqueda_nombre:
        # Se asume que buscará en primer nombre o primer apellido
        registros = registros.filter(
            Q(usuario__primer_nombre_usr_hospederia__icontains=busqueda_nombre) |
            Q(usuario__primer_apellido_usr_hospederia__icontains=busqueda_nombre)
        )

    if tipo_evento_filtro and tipo_evento_filtro != 'todos':
        registros = registros.filter(tipo_evento=tipo_evento_filtro)

    if fecha_desde_str:
        try:
            fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date()
            registros = registros.filter(fecha_hora__date__gte=fecha_desde)
        except ValueError:
            messages.error(request, "Formato de fecha 'Desde' inválido. Use AAAA-MM-DD.")
    
    if fecha_hasta_str:
        try:
            fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date()
            registros = registros.filter(fecha_hora__date__lte=fecha_hasta)
        except ValueError:
            messages.error(request, "Formato de fecha 'Hasta' inválido. Use AAAA-MM-DD.")

    context = {
        'registros': registros,
        'busqueda_rut': busqueda_rut,
        'busqueda_nombre': busqueda_nombre,
        'tipo_evento_filtro': tipo_evento_filtro,
        'fecha_desde': fecha_desde_str,
        'fecha_hasta': fecha_hasta_str,
    }
    return render(request, 'servicios/listar_registros_control_horario.html', context)

def historial_registros_usuario_pdf(request, rut_usuario):
    if request.user.is_superuser or (hasattr(request.user, 'tipo') and request.user.tipo == 'administrador'):
        return redirect('index')
    usuario = get_object_or_404(usuario_hospederia, rut_usr_hospederia=rut_usuario)
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    historial_qs = HistorialServicioUsuario.objects.filter(usuario=usuario)
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            historial_qs = historial_qs.filter(fecha__gte=fecha_desde_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            historial_qs = historial_qs.filter(fecha__lte=fecha_hasta_dt)
        except ValueError:
            pass
    historial_qs = historial_qs.order_by('-fecha')
    fechas = sorted(set(historial_qs.values_list('fecha', flat=True)), reverse=True)
    servicios = list(Servicio.objects.all())
    subservicios = list(SubServicio.objects.select_related('servicio').all())
    historial_con_servicios = []
    for fecha in fechas:
        servicios_dict = {}
        for servicio in servicios:
            if not servicio.subservicios.exists():
                count = historial_qs.filter(fecha=fecha, servicio=servicio, subservicio=None).count()
                servicios_dict[servicio.nombre_servicio] = count
        for sub in subservicios:
            count = historial_qs.filter(fecha=fecha, subservicio=sub, servicio=None).count()
            key = f"{sub.servicio.nombre_servicio} - {sub.nombre_subservicio}"
            servicios_dict[key] = count
        historial_con_servicios.append({
            'fecha': fecha,
            'servicios': servicios_dict
        })
    conteo_servicios = {}
    for servicio in servicios:
        if not servicio.subservicios.exists():
            conteo_servicios[servicio.nombre_servicio] = historial_qs.filter(servicio=servicio, subservicio=None).count()
    for sub in subservicios:
        key = f"{sub.servicio.nombre_servicio} - {sub.nombre_subservicio}"
        conteo_servicios[key] = historial_qs.filter(subservicio=sub, servicio=None).count()
    context = {
        'usuario': usuario,
        'historial_con_servicios': historial_con_servicios,
        'conteo_servicios': conteo_servicios,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'pdf_export': True,
    }
    template = get_template('servicios/historial_registros_pdf.html')
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="historial_{usuario.rut_usr_hospederia}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=500)
    return response

def historial_registros_totales(request, rut_usuario):
    usuario = get_object_or_404(usuario_hospederia, rut_usr_hospederia=rut_usuario)
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    historial_qs = HistorialServicioUsuario.objects.filter(usuario=usuario)
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            historial_qs = historial_qs.filter(fecha__gte=fecha_desde_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            historial_qs = historial_qs.filter(fecha__lte=fecha_hasta_dt)
        except ValueError:
            pass
    servicios = list(Servicio.objects.all())
    subservicios = list(SubServicio.objects.select_related('servicio').all())
    conteo_servicios = {}
    for servicio in servicios:
        if not servicio.subservicios.exists():
            conteo_servicios[servicio.nombre_servicio] = historial_qs.filter(servicio=servicio, subservicio=None).count()
    for sub in subservicios:
        key = f"{sub.servicio.nombre_servicio} - {sub.nombre_subservicio}"
        conteo_servicios[key] = historial_qs.filter(subservicio=sub, servicio=None).count()
    context = {
        'usuario': usuario,
        'conteo_servicios': conteo_servicios,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    return render(request, 'servicios/historial_registros_totales.html', context)

def historial_registros_totales_pdf(request, rut_usuario):
    usuario = get_object_or_404(usuario_hospederia, rut_usr_hospederia=rut_usuario)
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    historial_qs = HistorialServicioUsuario.objects.filter(usuario=usuario)
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            historial_qs = historial_qs.filter(fecha__gte=fecha_desde_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            historial_qs = historial_qs.filter(fecha__lte=fecha_hasta_dt)
        except ValueError:
            pass
    servicios = list(Servicio.objects.all())
    subservicios = list(SubServicio.objects.select_related('servicio').all())
    conteo_servicios = {}
    for servicio in servicios:
        if not servicio.subservicios.exists():
            conteo_servicios[servicio.nombre_servicio] = historial_qs.filter(servicio=servicio, subservicio=None).count()
    for sub in subservicios:
        key = f"{sub.servicio.nombre_servicio} - {sub.nombre_subservicio}"
        conteo_servicios[key] = historial_qs.filter(subservicio=sub, servicio=None).count()
    context = {
        'usuario': usuario,
        'conteo_servicios': conteo_servicios,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    template = get_template('servicios/historial_registros_pdf.html')
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="conteo_servicios_{usuario.rut_usr_hospederia}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=500)
    return response

def historial_registros_totales_general(request):
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    historial_qs = HistorialServicioUsuario.objects.all()
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            historial_qs = historial_qs.filter(fecha__gte=fecha_desde_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            historial_qs = historial_qs.filter(fecha__lte=fecha_hasta_dt)
        except ValueError:
            pass
    servicios = list(Servicio.objects.all())
    subservicios = list(SubServicio.objects.select_related('servicio').all())
    conteo_servicios = {}
    for servicio in servicios:
        if not servicio.subservicios.exists():
            conteo_servicios[servicio.nombre_servicio] = historial_qs.filter(servicio=servicio, subservicio=None).count()
    for sub in subservicios:
        key = f"{sub.servicio.nombre_servicio} - {sub.nombre_subservicio}"
        conteo_servicios[key] = historial_qs.filter(subservicio=sub, servicio=None).count()
    context = {
        'conteo_servicios': conteo_servicios,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    return render(request, 'servicios/historial_registros_totales_general.html', context)

def historial_registros_totales_general_pdf(request):
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    historial_qs = HistorialServicioUsuario.objects.all()
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            historial_qs = historial_qs.filter(fecha__gte=fecha_desde_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            historial_qs = historial_qs.filter(fecha__lte=fecha_hasta_dt)
        except ValueError:
            pass
    servicios = list(Servicio.objects.all())
    subservicios = list(SubServicio.objects.select_related('servicio').all())
    conteo_servicios = {}
    for servicio in servicios:
        if not servicio.subservicios.exists():
            conteo_servicios[servicio.nombre_servicio] = historial_qs.filter(servicio=servicio, subservicio=None).count()
    for sub in subservicios:
        key = f"{sub.servicio.nombre_servicio} - {sub.nombre_subservicio}"
        conteo_servicios[key] = historial_qs.filter(subservicio=sub, servicio=None).count()
    context = {
        'conteo_servicios': conteo_servicios,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    template = get_template('servicios/historial_registros_pdf_general.html')
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="conteo_servicios_general.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=500)
    return response

def actualizar_servicio_dia(request, rut_usuario):
    if request.user.is_superuser or (hasattr(request.user, 'tipo') and request.user.tipo == 'administrador'):
        return redirect('index')
    usuario = get_object_or_404(usuario_hospederia, rut_usr_hospederia=rut_usuario)
    hoy = timezone.localdate()
    fecha_salida = hoy + timedelta(days=1)
    registro_hoy = registroHorarioHospederia.objects.filter(usuario=usuario, hora_entrada__date=hoy).first()
    if not registro_hoy:
        messages.error(request, 'No existe un registro de ingreso para hoy. Primero debe registrar el ingreso.')
        return redirect('perfil_usuario', rut_usuario=usuario.rut_usr_hospederia)

    # Usar la fecha de salida real (la que se usó al registrar los servicios)
    fecha_salida_real = registro_hoy.hora_salida.date()
    servicios_hoy = HistorialServicioUsuario.objects.filter(usuario=usuario, fecha=fecha_salida_real)
    # IDs de servicios simples
    servicios_simples_ids = list(servicios_hoy.filter(subservicio=None).values_list('servicio_id', flat=True))
    # Diccionario de subservicios: {field_name: [ids]}
    subservicios_initial_dict = {}
    servicios_con_subs = Servicio.objects.filter(subservicios__isnull=False).distinct()
    for servicio in servicios_con_subs:
        field_name = f'subservicios_{servicio.id}'
        subservicios_ids = list(servicios_hoy.filter(servicio=None, subservicio__servicio=servicio).values_list('subservicio_id', flat=True))
        print(f"Para {servicio.nombre_servicio} ({field_name}): {subservicios_ids}")
        subservicios_initial_dict[field_name] = subservicios_ids
    print("SERVICIOS MARCADOS:", servicios_simples_ids)
    print("SUBSERVICIOS MARCADOS:", subservicios_initial_dict)
    if request.method == 'POST':
        form = HistorialServicioUsuarioForm(request.POST)
        if form.is_valid():
            servicios_hoy.delete()
            fecha = form.cleaned_data['fecha']
            # Guardar servicios simples
            servicios_simples = [s.pk if hasattr(s, 'pk') else s for s in form.cleaned_data['servicios_simples']]
            pernoctacion = Servicio.objects.filter(nombre_servicio__iexact='Pernoctación').first()
            if pernoctacion and pernoctacion.pk not in servicios_simples:
                servicios_simples.append(pernoctacion.pk)
            for servicio_id in servicios_simples:
                HistorialServicioUsuario.objects.get_or_create(
                    usuario=usuario,
                    fecha=fecha,
                    servicio_id=servicio_id,
                    subservicio=None
                )
            # Guardar subservicios
            observacion = form.cleaned_data.get('observacion', '')
            for field_name in form.fields:
                if field_name.startswith('subservicios_'):
                    for subservicio in form.cleaned_data[field_name]:
                        subservicio_id = subservicio.pk if hasattr(subservicio, 'pk') else subservicio
                        subservicio_obj = SubServicio.objects.get(pk=subservicio_id)
                        if subservicio_obj.servicio.nombre_servicio == 'Asistencia Ambulatoria':
                            HistorialServicioUsuario.objects.get_or_create(
                                usuario=usuario,
                                fecha=fecha,
                                servicio=None,
                                subservicio_id=subservicio_id,
                                defaults={'observacion': observacion}
                            )
                        else:
                            HistorialServicioUsuario.objects.get_or_create(
                                usuario=usuario,
                                fecha=fecha,
                                servicio=None,
                                subservicio_id=subservicio_id
                            )
            messages.success(request, 'Servicios del día actualizados correctamente.')
            return redirect('perfil_usuario', rut_usuario=usuario.rut_usr_hospederia)
    else:
        form = HistorialServicioUsuarioForm(
            servicios_simples_initial=servicios_simples_ids,
            subservicios_initial_dict=subservicios_initial_dict,
            initial={'fecha': fecha_salida}
        )
    servicios = Servicio.objects.prefetch_related('subservicios').all()
    return render(request, 'servicios/registro_usuario_hospederia.html', {
        'usuario': usuario,
        'preview_entrada': registro_hoy.hora_entrada if registro_hoy else None,
        'preview_salida': registro_hoy.hora_salida if registro_hoy else fecha_salida,
        'existe_registro_hoy': True,
        'servicios': servicios,
        'form': form,
        'modo_actualizacion': True,
    })

def actualizar_servicio_dia_aparte(request, rut_usuario):
    usuario = get_object_or_404(usuario_hospederia, rut_usr_hospederia=rut_usuario)
    hoy = timezone.localdate()
    fecha_salida = hoy + timedelta(days=1)
    registro_hoy = registroHorarioHospederia.objects.filter(usuario=usuario, hora_entrada__date=hoy).first()
    if not registro_hoy:
        messages.error(request, 'No existe un registro de ingreso para hoy. Primero debe registrar el ingreso.')
        return redirect('perfil_usuario', rut_usuario=usuario.rut_usr_hospederia)

    fecha_entrada = registro_hoy.hora_entrada.date()
    servicios_hoy = HistorialServicioUsuario.objects.filter(usuario=usuario, fecha=fecha_entrada)
    servicios_simples_objs = Servicio.objects.filter(pk__in=servicios_hoy.filter(subservicio=None).values_list('servicio_id', flat=True))
    subservicios_ids = servicios_hoy.filter(servicio=None).values_list('subservicio_id', flat=True)
    observacion = servicios_hoy.filter(subservicio__servicio__nombre_servicio='Asistencia Ambulatoria').first()
    initial = {
        'fecha': fecha_salida,
        'servicios_simples': list(servicios_simples_objs),
    }
    if observacion:
        initial['observacion'] = observacion.observacion
    servicios_con_subs = Servicio.objects.filter(subservicios__isnull=False).distinct()
    for servicio in servicios_con_subs:
        key = f'subservicios_{servicio.id}'
        subservicios_qs = SubServicio.objects.filter(servicio=servicio)
        subservicios_objs = subservicios_qs.filter(
            pk__in=servicios_hoy.filter(subservicio__servicio=servicio).values_list('subservicio_id', flat=True)
        )
        initial[key] = list(subservicios_objs)

    if request.method == 'POST':
        form = HistorialServicioUsuarioForm(request.POST)
        if form.is_valid():
            servicios_hoy.delete()
            fecha = form.cleaned_data['fecha']
            servicios_simples = list(form.cleaned_data['servicios_simples'])
            pernoctacion = Servicio.objects.filter(nombre_servicio__iexact='Pernoctación').first()
            if pernoctacion and pernoctacion not in servicios_simples:
                servicios_simples.append(pernoctacion)
            for servicio in servicios_simples:
                HistorialServicioUsuario.objects.get_or_create(
                    usuario=usuario,
                    fecha=fecha,
                    servicio=servicio,
                    subservicio=None
                )
            observacion = form.cleaned_data.get('observacion', '')
            for field_name in form.fields:
                if field_name.startswith('subservicios_'):
                    for subservicio in form.cleaned_data[field_name]:
                        subservicio_id = subservicio.pk if hasattr(subservicio, 'pk') else subservicio
                        subservicio_obj = SubServicio.objects.get(pk=subservicio_id)
                        if subservicio_obj.servicio.nombre_servicio == 'Asistencia Ambulatoria':
                            HistorialServicioUsuario.objects.get_or_create(
                                usuario=usuario,
                                fecha=fecha,
                                servicio=None,
                                subservicio_id=subservicio_id,
                                defaults={'observacion': observacion}
                            )
                        else:
                            HistorialServicioUsuario.objects.get_or_create(
                                usuario=usuario,
                                fecha=fecha,
                                servicio=None,
                                subservicio_id=subservicio_id
                            )
            messages.success(request, 'Servicios del día actualizados correctamente.')
            return redirect('perfil_usuario', rut_usuario=usuario.rut_usr_hospederia)
    else:
        form = HistorialServicioUsuarioForm(initial=initial)

    servicios = Servicio.objects.prefetch_related('subservicios').all()
    return render(request, 'servicios/actualizar_servicio_dia.html', {
        'usuario': usuario,
        'preview_entrada': registro_hoy.hora_entrada if registro_hoy else None,
        'preview_salida': registro_hoy.hora_salida if registro_hoy else fecha_salida,
        'existe_registro_hoy': True,
        'servicios': servicios,
        'form': form,
        'modo_actualizacion': True,
    })
