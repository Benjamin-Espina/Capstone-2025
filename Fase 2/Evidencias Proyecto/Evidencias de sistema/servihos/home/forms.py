from django import forms
from .models import usuarioCustom, usuario_hospederia
from django.contrib.auth.forms import UserCreationForm

class customUserCreationForm(UserCreationForm):
    rut = forms.IntegerField(
        label='Rut',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
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