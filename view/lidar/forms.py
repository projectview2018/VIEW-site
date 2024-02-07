from django import forms
from .models import Scan


class ScanForm(forms.ModelForm):
    class Meta:
        model = Scan
        widgets = {
            'eye_y_ft': forms.TextInput(attrs={
                'class': 'data-upload-textinput Body input',
                'type': 'text',
                'name': 'eye height (ft) input',
                'required': 'true',
                'placeholder': '000'
            }),
            'eye_y_in': forms.TextInput(attrs={
                'type': 'text',
                'name': 'eye height (in) input',
                'required': 'true',
                'placeholder': '00.00',
                'class': 'data-upload-textinput1 Body input'
            }),
            'eye_z_ft': forms.TextInput(attrs={
                'type': "text",
                'name': "eye to hood distance (ft) input",
                'required': "true",
                'placeholder': "000",
                'class': "data-upload-textinput2 Body input"
            }),
            'eye_z_in': forms.TextInput(attrs={
                'type': "text",
                'name': "eye to hood distance (in) input",
                'required': "true",
                'placeholder': "00.00",
                'class': "data-upload-textinput3 Body input",
            }),
            'eye_x_ft': forms.TextInput(attrs={
                'type': "text",
                'name': "eye to door distance (ft) input",
                'required': "true",
                'placeholder': "000",
                'class': "data-upload-textinput4 Body input",
            }),
            'eye_x_in': forms.TextInput(attrs={
                'type': "text",
                'name': "eye to door distance (in) input",
                'required': "true",
                'placeholder': "00.00",
                'class': "data-upload-textinput5 input Body",
            }),
            'lidar_scan': forms.FileInput(attrs={
                'type': "file",
                'id': "lidar-file-selector",
                'name': "LiDAR Scan File Selector",
                'required': "true",
                'placeholder': "placeholder",
                'class': "data-upload-textinput6 Body input",
            }),
        }
        fields = ['vehicle', 'driver_side_start', 'eye_x_ft', 'eye_x_in', 'eye_y_ft', 'eye_y_in', 'eye_z_ft', 'eye_z_in', 'lidar_scan']
