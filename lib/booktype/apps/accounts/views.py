from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from django.contrib.auth.models import User

from booktype.apps.core.views import PageView


class RegisterPageView(PageView):
    template_name = "accounts/register.html"
    page_title = _('Register')
    title = _('Please register')

    def get_context_data(self, **kwargs):
        context = super(RegisterPageView, self).get_context_data(**kwargs)

        return context