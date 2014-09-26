# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext as _
from booktype.apps.portal.forms import SpanErrorList
from booki.editor.models import Language, Info

class BaseSettingsForm(object):
    success_url = None
    success_message = None

    def __init__(self, *args, **kwargs):
        kwargs.update({'error_class': SpanErrorList})
        super(BaseSettingsForm, self).__init__(*args, **kwargs)

    @classmethod
    def initial_data(cls):
        return None

    @classmethod
    def extra_context(cls, book=None, request=None):
        return {}

    def save_settings(self, request):
        pass

class LanguageForm(BaseSettingsForm, forms.Form):
    language = forms.ModelChoiceField(
            label = _('Language'),
            queryset = Language.objects.all()
        )
    right_to_left = forms.BooleanField(
            label = _('Right to left text'),
            required = False,
            help_text = _("Book with right to left writting.")
        )

    @classmethod
    def initial_data(cls, book=None, request=None):
        try:
            rtl = Info.objects.get(book=book, kind=0).getValue()
        except (Info.DoesNotExist, Info.MultipleObjectsReturned):
            rtl = 'LTR'

        return {
            'right_to_left': (rtl == 'RTL'),
            'language': book.language
        }

    def save_settings(self, book, request):
        book.language = self.cleaned_data['language']
        book.save()

        rtl_value = self.cleaned_data['right_to_left']
        rtl_value = "RTL" if rtl_value else "LTR"

        try:
            rtl = Info.objects.get(book=book, kind=0)
            rtl.value_string = rtl_value
            rtl.save()
        except Info.DoesNotExist:
            rtl = Info(book=book, kind=0, value_string=rtl_value)
            rtl.save()

class LicenseForm(BaseSettingsForm, forms.Form):
    pass

class ChapterStatus(BaseSettingsForm, forms.Form):
    pass