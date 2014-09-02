# -*- coding: utf-8 -*-
from django import forms

class BaseSettingsForm(object):
    success_url = None
    success_message = None

    @classmethod
    def initial_data(cls):
        return None

    @classmethod
    def extra_context(cls):
        return {}

    def save_settings(self, request):
        pass

class LanguageForm(BaseSettingsForm, forms.Form):
    pass

class LicenseForm(BaseSettingsForm, forms.Form):
    pass

class ChapterStatus(BaseSettingsForm, forms.Form):
    pass