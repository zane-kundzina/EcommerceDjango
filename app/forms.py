from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField, PasswordChangeForm, SetPasswordForm, PasswordResetForm
from django.contrib.auth.models import User
from .models import Customer

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus':'True',
    'class': 'form-control'} ))
    password = forms.CharField(label='Password', widget=forms.PasswordInput
    (attrs={'autocomplete':'current-password','class':'form-control'}))

class CustomerRegistrationForm(UserCreationForm):
    username = forms. CharField(widget=forms.TextInput(attrs={'autofocus':'True',
    'class': 'form-control'} ))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class':'form-control'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput
    (attrs={'class':'form-control'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.
    PasswordInput(attrs={'class':'form-control'}))

    class Meta:
            model = User
            fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
            user = super().save(commit=False)
            user.email = self.cleaned_data['email']
            if commit:
                user.save()
            return user
    
class MyPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label="Old Password", widget=forms.PasswordInput(attrs={'autocomplete':'current-password','autofocus':'True','class':'form-control'}))
    new_password1 = forms.CharField(label="New Password", widget=forms.PasswordInput(attrs={'autocomplete':'new-password','class':'form-control'}))
    new_password2 = forms.CharField(label="Confirm New Password", widget=forms.PasswordInput(attrs={'autocomplete':'new-password','class':'form-control'}))

class MyPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Email", max_length=254, widget=forms.EmailInput(attrs={'autocomplete':'email','class':'form-control'}))

class MySetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label="New Password", widget=forms.PasswordInput(attrs={'autocomplete':'new-password','class':'form-control'}))
    new_password2 = forms.CharField(label="Confirm New Password", widget=forms.PasswordInput(attrs={'autocomplete':'new-password','class':'form-control'}))

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'locality', 'city', 'mobile', 'zipcode', 'country']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'locality': forms.TextInput(attrs={'class':'form-control'}),
            'city': forms.TextInput(attrs={'class':'form-control'}),
            'mobile': forms.NumberInput(attrs={'class':'form-control'}),
            'zipcode': forms.TextInput(attrs={'class':'form-control'}),
            'country': forms.Select(attrs={'class':'form-control'}),
        }
        