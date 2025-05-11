from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from .forms import customUserCreationForm
from django.contrib import messages

# Create your views here.

obtener_usuarios= get_user_model()

def es_administrador(user):
    return user.is_authenticated and (hasattr(user, 'tipo') and user.tipo == 'administrador' or user.is_superuser)

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
    usuarios = obtener_usuarios.objects.all()
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
