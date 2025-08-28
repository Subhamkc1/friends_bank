from django import forms
from django.contrib.auth.models import User
from .models import MoneyRequest

class TransferForm(forms.Form):
    to_username = forms.CharField(label='To (username)')
    amount = forms.DecimalField(decimal_places=2, max_digits=12, min_value=0.01)
    note = forms.CharField(required=False)

class WithdrawForm(forms.Form):
    amount = forms.DecimalField(decimal_places=2, max_digits=12, min_value=0.01)
    note = forms.CharField(required=False)

class RequestMoneyForm(forms.ModelForm):
    class Meta:
        model = MoneyRequest
        fields = ['amount','note']

class AdminUserForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField(required=False)

class AdminDepositForm(forms.Form):
    username = forms.CharField(label="To username")
    amount = forms.DecimalField(decimal_places=2, max_digits=12, min_value=0.01)
    note = forms.CharField(required=False)
