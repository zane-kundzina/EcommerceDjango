from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField, PasswordChangeForm, SetPasswordForm, PasswordResetForm
from django.contrib.auth.models import User
from .models import Customer, Review
from django.core.exceptions import ValidationError
import re

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
            user.is_active = False 
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
    country_code = forms.ChoiceField(
        choices=[
            ('+371', '+371 (Latvia)'),
            ('+372', '+372 (Estonia)'),
            ('+370', '+370 (Lithuania)'),
        ],
        initial='+371',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    mobile = forms.CharField(
        max_length=8,
        min_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number',
            'inputmode': 'numeric'
        })
    )
    
    class Meta:
        model = Customer
        fields = ['name', 'locality', 'city', 'country_code', 'mobile', 'zipcode', 'country']
        labels = {'locality': 'Street', 'city': 'City', 'mobile': 'Mobile Number', 'zipcode': 'Zip Code'}
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'locality': forms.TextInput(attrs={'class':'form-control'}),
            'city': forms.TextInput(attrs={'class':'form-control'}),
            'zipcode': forms.TextInput(attrs={'class':'form-control'}),
            'country': forms.Select(attrs={'class':'form-control'}),
        }
    
    # VALIDĀCIJA (tikai 8 cipari)
    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')

        if not re.fullmatch(r'\d{8}', mobile):
            raise ValidationError("Enter exactly 8 digits")

        return mobile
    
    # SAGLABĀ KOPĀ
    def save(self, commit=True):
        instance = super().save(commit=False)

        country_code = self.cleaned_data.get('country_code')
        mobile = self.cleaned_data.get('mobile')

        instance.mobile = f"{country_code} {mobile}"

        if commit:
            instance.save()

        return instance


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['comment', 'rating']

        widgets = {
            'rating': forms.HiddenInput(),
            'comment': forms.Textarea(attrs={'rows': 3,  'class': 'form-control', 'placeholder': 'Write your review here...'})
        }

    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        error_messages={
            'min_value': 'Please select at least 1 star.',
            'max_value': 'Rating cannot exceed 5 stars.'
        }
    )

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None or rating < 1 or rating > 5:
            raise forms.ValidationError("Please select a star rating (1 to 5).")
        return rating    
