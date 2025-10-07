"""
Forms for virtual device management
"""

from django import forms

from .models import VirtualBACnetDevice


class VirtualDeviceCreateForm(forms.ModelForm):
    """Form for creating virtual BACnet devices"""

    class Meta:
        model = VirtualBACnetDevice
        fields = ["device_id", "device_name", "description", "port"]
        widgets = {
            "device_id": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., 999",
                    "min": 0,
                    "max": 4194303,
                }
            ),
            "device_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Virtual Temperature Sensor",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional description...",
                }
            ),
            "port": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "value": 47808,
                    "min": 1024,
                    "max": 65535,
                }
            ),
        }

        help_texts = {
            "device_id": "Unique BACnet device ID (0-4194303)",
            "device_name": "Human-readable name for this virtual device",
            "port": "BACnet UDP port (default 47808)",
        }

    def clean_device_id(self):
        """Validate device_id is unique"""
        device_id = self.cleaned_data["device_id"]

        if VirtualBACnetDevice.objects.filter(device_id=device_id).exists():
            raise forms.ValidationError(
                f"Device ID {device_id} already exists. Please choose a different ID."
            )

        if device_id < 0 or device_id > 4194303:
            raise forms.ValidationError("Device ID must be between 0 and 4194303")
        return device_id

    def clean_port(self):
        """Validate port number"""
        port = self.cleaned_data["port"]

        if port < 1024 or port > 65535:
            raise forms.ValidationError("Port must be between 1024 and 65535")
        return port
