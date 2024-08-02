from django import forms

class SearchUsersForm(forms.Form):
    query = forms.CharField(max_length=100, required=True)
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data