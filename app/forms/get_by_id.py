from django import forms

class GetByIdForm(forms.Form):
    track_id = forms.CharField(max_length=100, required=False)
    artist_id = forms.CharField(max_length=100, required=False)
    genre_id = forms.CharField(max_length=100, required=False)
    album_id = forms.CharField(max_length=100, required=False)

    def clean(self):
        cleaned_data = super().clean()
        if not any([cleaned_data.get('track_id'), cleaned_data.get('artist_id'), cleaned_data.get('genre_id'), cleaned_data.get('album_id')]):
            raise forms.ValidationError('At least one identifier must be provided.')
        return cleaned_data