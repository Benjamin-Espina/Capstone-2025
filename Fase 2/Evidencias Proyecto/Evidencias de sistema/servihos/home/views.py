from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db import transaction, IntegrityError
from datetime import date
from django.db.models import Q

#Importar modelos
from .models import usuario_hospederia, tipo_discapacidad, hospederia, Servicio, SubServicio, RegistroControlHorario

#Importar formularios
from .forms import ServicioForm, SubServicioForm, customUserCreationForm, subir_CSV_usr_hospederia, UsuarioHospederiaFormEdit

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
    return render(request, "index.html")

@login_required
@user_passes_test(es_administrador, login_url='iniciar_sesion')
def registrar_encargado(request):
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

    context = {
        'usuarios': usuarios_hospedados,
        'busqueda': busqueda,
    }



    return render(request, 'servicios/listar_hospedados.html', {'usuarios': usuarios_hospedados})

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
    usuario = get_object_or_404(usuario_hospederia, rut_usr_hospederia=rut_usuario)
    edad = calcular_edad(usuario.fecha_nacimiento_usr_hospederia)

    context = {
        'usuario': usuario,
        'edad': edad,
    }

    return render(request, 'servicios/perfil_usuario.html', context)

def crear_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('crear_servicio')  # o redirige a una lista si la tienes
    else:
        form = ServicioForm()
    return render(request, 'servicios/crear_servicio.html', {'form': form})

def listar_servicios(request):
    servicios = Servicio.objects.all()
    return render(request, 'servicios/listar_servicios.html', {'servicios': servicios})

def eliminar_servicio(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)
    if request.method == 'POST':
        servicio.delete()
        messages.success(request, 'Servicio eliminado correctamente.')
        return redirect('listar_servicios')
    return redirect('listar_servicios')

def crear_subservicio(request):
    if request.method == 'POST':
        form = SubServicioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_subservicios')  # o a donde tú necesites
    else:
        form = SubServicioForm()
    return render(request, 'servicios/crear_subservicio.html', {'form': form})

def listar_subservicios(request):
    subservicios = SubServicio.objects.select_related('servicio').all()
    return render(request, 'servicios/listar_subservicios.html', {'subservicios': subservicios})

def eliminar_subservicio(request, subservicio_id):
    sub = get_object_or_404(SubServicio, id=subservicio_id)
    if request.method == 'POST':
        sub.delete()
        messages.success(request, f"Subservicio '{sub.nombre_subservicio}' eliminado correctamente.")
    return redirect('listar_subservicios')


@login_required
@user_passes_test(es_administrador, login_url='iniciar_sesion')
def subir_usuarios_hospederia(request):
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
def registrar_control_horario(request, rut_usuario, tipo_evento):
    if request.method == 'POST':
        usuario = get_object_or_404(usuario_hospederia, rut_usr_hospederia=rut_usuario)
        
        # Validación básica para evitar registros duplicados rápidos o ilógicos
        ultimo_registro = RegistroControlHorario.objects.filter(usuario=usuario).order_by('-fecha_hora').first()

        if ultimo_registro and ultimo_registro.tipo_evento == tipo_evento:
            messages.warning(request, f"El usuario ya tiene un registro de {tipo_evento} reciente.")
            return redirect('perfil_usuario', rut_usuario=rut_usuario)


        RegistroControlHorario.objects.create(
            usuario=usuario,
            tipo_evento=tipo_evento,
            # fecha_hora se autocompleta por auto_now_add=True
        )
        messages.success(request, f"Registro de {tipo_evento} para {usuario.primer_nombre_usr_hospederia} guardado exitosamente.")
        return redirect('perfil_usuario', rut_usuario=rut_usuario)
    messages.error(request, "Método de solicitud no permitido.")
    return redirect('perfil_usuario', rut_usuario=rut_usuario)

@login_required
def listar_registros_control_horario(request):
    # Obtener todos los registros de control horario, ordenados por fecha y hora descendente
    registros = RegistroControlHorario.objects.all().order_by('-fecha_hora')

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