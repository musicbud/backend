from django import forms
from .models import Channel

class ChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("Form initialized with args:", args)
        print("Form initialized with kwargs:", kwargs)
        print("Initial form data:", self.data)

    def is_valid(self):
        print("Form data before validation:", self.data)
        valid = super().is_valid()
        print("Form is valid:", valid)
        if not valid:
            print("Form errors:", self.errors)
        return valid
