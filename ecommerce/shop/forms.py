from django import forms
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from .models import CustomUser
from django.contrib.auth.models import User



class RegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        
        return password


class LoginForm(AuthenticationForm):
    pass

class CheckoutForm(forms.Form):
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label="Shipping Address")
    phone_number = forms.CharField(max_length=15, label="Phone Number")
    pincode = forms.CharField(max_length=10, label="Pincode")





