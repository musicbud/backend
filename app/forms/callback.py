from django import forms

class CodeForm(forms.Form):
    code = forms.CharField(max_length=100, required=True)
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data