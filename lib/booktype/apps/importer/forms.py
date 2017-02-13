# -*- coding: utf-8 -*-

from functools import partial

from django import forms
from django.utils.translation import ugettext_lazy as _


class UploadForm(forms.Form):
    title = forms.CharField(
        required=False,
        label='Book title',
        widget=forms.TextInput(
            attrs={'placeholder': 'Only if you want to rename it'}
        )
    )
    file = forms.FileField(
        required=True,
        label='Your EPUB file'
    )


ALLOWED_TYPES = [
    'application/epub+zip',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
]

ALLOWED_EXTENSIONS = ['.docx', '.epub']


def _check_extension(file_name, extension):
    return file_name.endswith(extension)


class UploadBookForm(forms.Form):
    book_title = forms.CharField(required=False)
    book_file = forms.FileField()
    hidden = forms.BooleanField(required=False)

    def clean(self, *args, **kwargs):
        data = super(UploadBookForm, self).clean(*args, **kwargs)

        book_file = data.get('book_file')
        content_type = book_file.content_type

        if content_type == 'application/octet-stream':
            if not any(map(partial(_check_extension, book_file.name), ALLOWED_EXTENSIONS)):
                raise forms.ValidationError(_('Filetype not supported.'))
        elif content_type not in ALLOWED_TYPES:
            raise forms.ValidationError(_('Filetype not supported.'))

        return data
