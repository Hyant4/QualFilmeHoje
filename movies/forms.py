import re

from django import forms


class WhatsAppContactForm(forms.Form):
    phone_number = forms.CharField(
        label="Seu número do WhatsApp",
        required=False,
        max_length=30,
        help_text="Opcional. Use DDD; exemplo: (85) 99999-0000.",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "tel",
                "inputmode": "tel",
                "placeholder": "+55 85 99999-0000",
            }
        ),
    )

    def clean_phone_number(self):
        value = self.cleaned_data["phone_number"].strip()
        if not value:
            return ""

        digits = re.sub(r"\D", "", value)
        if len(digits) in {10, 11}:  # número brasileiro informado com DDD
            digits = f"55{digits}"
        if not (digits.startswith("55") and len(digits) in {12, 13}):
            raise forms.ValidationError(
                "Informe um número brasileiro válido, com DDD."
            )
        return f"+{digits}"
