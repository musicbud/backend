from django import forms

class SetMyProfileForm(forms.Form):
    bio = forms.CharField(max_length=500, required=False)
    display_name = forms.CharField(max_length=100, required=False)
    photo = forms.ImageField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
