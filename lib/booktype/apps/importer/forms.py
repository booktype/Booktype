# -*- coding: utf-8 -*-
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


class UploadBookForm(forms.Form):
    book_title = forms.CharField(required=False)
    book_file = forms.FileField()
    hidden = forms.BooleanField(required=False)

    def clean(self, *args, **kwargs):
        data = super(UploadBookForm, self).clean(*args, **kwargs)

        book_file = data.get('book_file')
        content_type = book_file.content_type

        if content_type not in ALLOWED_TYPES:
            raise forms.ValidationError(_('Filetype not supported.'))

        return data
