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
        exclude = ['fecha_registro']
        widgets = {
            'fecha_nacimiento_usr_hospederia': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'rut_usr_hospederia': 'RUT',
            'pasaporte_usr_hospederia': 'Pasaporte',
            'primer_nombre_usr_hospederia': 'Primer nombre',
            'segundo_nombre_usr_hospederia': 'Segundo nombre',
            'primer_apellido_usr_hospederia': 'Primer apellido',
            'segundo_apellido_usr_hospederia': 'Segundo apellido',
            'fecha_nacimiento_usr_hospederia': 'Fecha de nacimiento',
            'discapacidad_usr_hospederia': 'Discapacidad',
            'id_tipo_discapacidad': 'Tipo de discapacidad',
            'nacionalidad_usr_hospederia': 'Nacionalidad',
            'id_hospederia': 'Hospedería',
            'mostrar_en_reportes': 'Mostrar en reportes',
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
    fecha = forms.DateField(label="Salida", widget=forms.DateInput(attrs={'type': 'date'}))
    servicios_simples = forms.ModelMultipleChoiceField(
        queryset=Servicio.objects.filter(subservicios__isnull=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Selecciona el/los servicios"
    )
    observacion = forms.CharField(
        label="Observación de Asistencia Ambulatoria",
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe lo realizado en Asistencia Ambulatoria...'}),
        required=False
    )
    # Un campo por cada servicio con subservicios
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].widget.attrs['readonly'] = True
        # Seleccionar y deshabilitar 'Pernoctación'
        pernoctacion = Servicio.objects.filter(nombre_servicio__iexact='Pernoctación').first()
        if pernoctacion:
            self.initial['servicios_simples'] = [pernoctacion.pk]
        # Personalizar los widgets para deshabilitar 'Pernoctación'
        choices = []
        for servicio in self.fields['servicios_simples'].queryset:
            if pernoctacion and servicio.pk == pernoctacion.pk:
                choices.append((servicio.pk, {'label': servicio.nombre_servicio, 'disabled': True}))
            else:
                choices.append((servicio.pk, {'label': servicio.nombre_servicio}))
        self.fields['servicios_simples'].widget.choices = [
            (pk, d['label']) for pk, d in choices
        ]
        self.pernoctacion_id = pernoctacion.pk if pernoctacion else None
        servicios_con_subs = Servicio.objects.filter(subservicios__isnull=False).distinct()
        for servicio in servicios_con_subs:
            self.fields[f'subservicios_{servicio.id}'] = forms.ModelMultipleChoiceField(
                queryset=SubServicio.objects.filter(servicio=servicio),
                required=False,
                widget=forms.CheckboxSelectMultiple,
                label=f"Subservicios de {servicio.nombre_servicio}"
            )

