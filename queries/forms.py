from django import forms


class UploadFileForm(forms.Form):
    table_name = forms.CharField(max_length=50, help_text='Only letters, numbers and underscore.')
    file = forms.FileField(help_text='CSV file containing data for your table. CSV must contain header row.')
    # database =
