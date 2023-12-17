from django import forms

from django.contrib.auth.forms import UserCreationForm


class UploadForm(forms.Form):
    YouTube_URL = forms.URLField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter YouTube URL'}),
        label='Insert YouTube URL'
    )
    local_directory = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control-file'}),
        label='Upload from your computer'
    )

    video_language = forms.ChoiceField(
        choices=[
            ('en', 'English'),
            ('zh-cn', 'Chinese'),
            ('fr', 'French'),
            ('es', 'Spanish'),
            ('de', 'German'),
            ('it', 'Italian'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Video Language'
    )
    