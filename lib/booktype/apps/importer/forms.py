# -*- coding: utf-8 -*-

from functools import partial

from django import forms
from django.utils.translation import ugettext_lazy as _

from booktype.utils import config

EPUB_CTYPE = 'application/epub+zip'
DOCX_CTYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

ALLOWED_TYPES = [
    EPUB_CTYPE, DOCX_CTYPE
]

ALLOWED_EXTENSIONS = ['.docx', '.epub']
ALLOWED_MSWORD_EXTENSIONS = ['.docx']


def _check_extension(file_name, extension):
    return file_name.endswith(extension)


# TODO: it seems this class is not used anymore. Check if can be deleted
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


class UploadDocxFileForm(forms.Form):
    # no need to translate this below, it will be hidden form
    IMPORT_CHOICES = (
        ("append", "Append"),
        ("overwrite", "Overwrite"),
    )

    chapter_file = forms.FileField(required=True)
    import_mode = forms.ChoiceField(
        required=True, choices=IMPORT_CHOICES, widget=forms.TextInput())

    upload_docx_default_mode = forms.CharField(
        widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(UploadDocxFileForm, self).__init__(*args, **kwargs)
        default_mode = config.get_configuration('UPLOAD_DOCX_DEFAULT_MODE')
        self.fields['upload_docx_default_mode'].initial = "" if (default_mode is None) else default_mode

    def clean(self, *args, **kwargs):
        data = super(UploadDocxFileForm, self).clean(*args, **kwargs)

        chapter_file = data.get('chapter_file')
        content_type = chapter_file.content_type

        if content_type == 'application/octet-stream':
            if not any(map(partial(_check_extension, chapter_file.name), ALLOWED_MSWORD_EXTENSIONS)):
                raise forms.ValidationError(_('Filetype not supported.'))
        elif content_type != DOCX_CTYPE:
            raise forms.ValidationError(_('Filetype not supported.'))

        return data
