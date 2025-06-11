from django import forms
from .models import usuarioCustom, usuario_hospederia
from django.contrib.auth.forms import UserCreationForm
from .models import Servicio
from .models import SubServicio
from .models import HistorialServicioUsuario

class customUserCreationForm(UserCreationForm):
    rut = forms.CharField(
        label='Rut',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        label='Nombre',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Apellido',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Nombre de usuario'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'

    class Meta:
        model = usuarioCustom
        fields = ('username', 'first_name', 'last_name', 'rut', 'password1', 'password2')
        labels = {
            'username': 'Nombre de usuario',
            'password1': 'Contraseña',
            'password2': 'Confirmar contraseña',
        }

class subir_CSV_usr_hospederia(forms.Form):
    csv_file = forms.FileField(
        label='Seleccionar archivo CSV',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel',
        })
    )

class UsuarioHospederiaFormEdit(forms.ModelForm):
    class Meta:
        model = usuario_hospederia
        fields = '__all__'
        widgets = {
            'fecha_nacimiento_usr_hospederia': forms.DateInput(attrs={'type': 'date'}),
        }


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre_servicio']
        labels = {
            'nombre_servicio': 'Nombre del servicio',
        }

    def clean_nombre_servicio(self):
        nombre = self.cleaned_data['nombre_servicio'].strip().lower()
        if Servicio.objects.filter(nombre_servicio__iexact=nombre).exists():
            raise forms.ValidationError("Este servicio ya está registrado.")
        return self.cleaned_data['nombre_servicio']
    

class SubServicioForm(forms.ModelForm):
    class Meta:
        model = SubServicio
        fields = ['nombre_subservicio', 'servicio']
        labels = {
            'nombre_subservicio': 'Nombre del subservicio',
            'servicio': 'Servicio asociado'
        }

    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get('nombre_subservicio')
        servicio = cleaned_data.get('servicio')

        if nombre and servicio:
            existe = SubServicio.objects.filter(
                servicio=servicio,
                nombre_subservicio__iexact=nombre.strip()
            ).exists()
            if existe:
                raise forms.ValidationError(
                    f"Ya existe un subservicio llamado '{nombre}' para el servicio '{servicio}'."
                )
        return cleaned_data

class HistorialServicioUsuarioForm(forms.Form):
    fecha = forms.DateField(
        label='Salida',
        widget=forms.DateInput(attrs={'type': 'date', 'readonly': 'readonly'})
    )
    servicios_simples = forms.ModelMultipleChoiceField(
        queryset=Servicio.objects.filter(subservicios__isnull=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Servicios Simples"
    )
    # Un campo por cada servicio con subservicios
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        servicios_con_subs = Servicio.objects.filter(subservicios__isnull=False).distinct()
        for servicio in servicios_con_subs:
            self.fields[f'subservicios_{servicio.id}'] = forms.ModelMultipleChoiceField(
                queryset=SubServicio.objects.filter(servicio=servicio),
                required=False,
                widget=forms.CheckboxSelectMultiple,
                label=f"Subservicios de {servicio.nombre_servicio}"
            )
        # Seleccionar automáticamente 'Pernoctación' si existe
        try:
            pernoctacion = Servicio.objects.get(nombre_servicio__iexact='Pernoctación')
            if 'initial' in kwargs:
                if 'servicios_simples' in kwargs['initial']:
                    # Si ya hay valores iniciales, agregar 'Pernoctación' si no está
                    if pernoctacion not in kwargs['initial']['servicios_simples']:
                        kwargs['initial']['servicios_simples'].append(pernoctacion)
                else:
                    kwargs['initial']['servicios_simples'] = [pernoctacion]
                self.initial['servicios_simples'] = kwargs['initial']['servicios_simples']
            else:
                self.initial['servicios_simples'] = [pernoctacion]
        except Servicio.DoesNotExist:
            pass

