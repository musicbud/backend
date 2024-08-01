from django import forms

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)
    photo = forms.ImageField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
