import re

from django import forms


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    phone = forms.CharField(
        max_length=15, help_text="M-Pesa number, e.g. 0712345678"
    )

    def clean_phone(self):
        phone = re.sub(r"[\s\-+]", "", self.cleaned_data["phone"])
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        if not re.fullmatch(r"254[17]\d{8}", phone):
            raise forms.ValidationError("Enter a valid Kenyan number, e.g. 0712345678.")
        return phone