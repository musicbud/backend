from django import forms

class GetBudProfileForm(forms.Form):
    bud_id = forms.CharField(max_length=100, required=True)
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data