# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
#
# Booktype is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Booktype is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Booktype.  If not, see <http://www.gnu.org/licenses/>.

import os
import datetime
import string
from random import choice


from django.core.files import File
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db import transaction, models
from django.views.generic import DetailView
from django.contrib.auth.models import User
from django.views.generic.edit import BaseCreateView
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.db.models import Q
from django.conf import settings


from booki.utils import config, misc
from booki.utils.json_wrapper import json
from booki.utils.book import checkBookAvailability, createBook
from booki.editor.models import Book, License, BookHistory, BookiGroup
from booki.account.models import UserPassword
from booki.utils import pages

from booktype.apps.core.views import BasePageView, PageView


class RegisterPageView(PageView):
    template_name = "accounts/register.html"
    page_title = _('Register')
    title = _('Please register')

    def get_context_data(self, **kwargs):
        context = super(RegisterPageView, self).get_context_data(**kwargs)

        return context


class DashboardPageView(BasePageView, DetailView):
    template_name = "accounts/dashboard.html"
    page_title = _('Dashboard')
    title = _('My Dashboard')

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'current_user'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['books'] = Book.objects.filter(owner=self.object)
        context['licenses'] = License.objects.all().order_by('name')
        context['groups'] = BookiGroup.objects.filter(owner=self.object)

        # get books with user has collaborated with
        book_ids = BookHistory.objects.filter(user=self.object).values_list('book', flat=True).distinct()
        context['books_collaborating'] = Book.objects.filter(id__in=book_ids).exclude(owner=self.object)

        # get user recent activity
        context['recent_activity'] = BookHistory.objects.filter(user=self.object).order_by('-modified')[:3]

        context['book_license'] = config.getConfiguration('CREATE_BOOK_LICENSE')
        context['book_visible'] = config.getConfiguration('CREATE_BOOK_VISIBLE')

        return context


class CreateBookView(BaseCreateView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'user'

    def get(self, request, *args, **kwargs):
        if request.GET.get('q', None) == "check":
            data = {
                "available": checkBookAvailability(request.GET.get('bookname', '').strip())
            }
            return HttpResponse(json.dumps(data), "application/json")

    def post(self, request, *args, **kwargs):
        book = createBook(request.user, request.POST.get('title'))
        lic = License.objects.get(abbrevation=request.POST.get('license'))

        book.license = lic
        book.description = request.POST.get('description', '')
        book.hidden = (request.POST.get('hidden', None) == 'on')

        if 'cover' in request.FILES:
            try:
                fh, fname = misc.saveUploadedAsFile(request.FILES['cover'])
                book.setCover(fname)
                os.unlink(fname)
            except:
                pass

        book.save()

        return render(
            request,
            'accounts/create_book_redirect.html',
            {"request": request, "book": book}
        )


class ForgotPasswordView(PageView):
    template_name = "accounts/forgot_password.html"
    page_title = _('Forgot your password')
    title = _('Forgot your password')

    def generate_secret_code(self):
        return ''.join([choice(string.letters + string.digits) for i in range(30)])

    def post(self, request, *args, **kwargs):
        context = super(ForgotPasswordView, self).get_context_data(**kwargs)
        if "name" not in request.POST:
            return pages.ErrorPage(request, "500.html")

        name = request.POST["name"].strip()

        users_to_email = list(User.objects.filter(Q(username=name) | Q(email=name)))
        if len(name) == 0:
            context['error'] = _('Missing username')
            return render(request, self.template_name, context)

        if len(users_to_email) == 0:
            context['error'] = _('No such user')
            return render(request, self.template_name, context)

        THIS_BOOKTYPE_SERVER = config.getConfiguration('THIS_BOOKTYPE_SERVER')
        for usr in users_to_email:
            secretcode = self.generate_secret_code()

            account_models = UserPassword()
            account_models.user = usr
            account_models.remote_useragent = request.META.get('HTTP_USER_AGENT', '')
            account_models.remote_addr = request.META.get('REMOTE_ADDR', '')
            account_models.remote_host = request.META.get('REMOTE_HOST', '')
            account_models.secretcode = secretcode

            body = render_to_string('accounts/password_reset_email.html',
                                    dict(secretcode=secretcode, hostname=THIS_BOOKTYPE_SERVER))

            msg = EmailMessage(_('Reset password'), body, settings.REPORT_EMAIL_USER, [usr.email])
            msg.content_subtype = 'html'

            # In case of an error we really should not send email to user and do rest of the procedure

            try:
                account_models.save()
                msg.send()
            except:
                context['error'] = _('Unknown error')

        return render(request, self.template_name, context)


class ForgotPasswordEnterView(PageView):
    template_name = "accounts/forgot_password_enter.html"
    page_title = _('Reset your password')
    title = _('Reset your password')

    def post(self, request, *args, **kwargs):
        context = super(ForgotPasswordEnterView, self).get_context_data(**kwargs)

        if "secretcode" and "password1" and "password2" not in request.POST:
            return pages.ErrorPage(request, "500.html")

        secretcode = request.POST["secretcode"].strip()
        password1 = request.POST["password1"].strip()
        password2 = request.POST["password2"].strip()

        if len(password1) == 0 or len(password2) == 0:
            context['password2_error'] = _('Password can\'t be empty')
            context['secretcode'] = secretcode
            return render(request, self.template_name, context)

        if password1 != password2:
            context['password2_error'] = _('Passwords don\'t match')
            context['secretcode'] = secretcode
            return render(request, self.template_name, context)

        all_ok = True

        try:
            pswd = UserPassword.objects.get(secretcode=secretcode)
        except UserPassword.DoesNotExist:
            all_ok = False

        if all_ok:
            pswd.user.set_password(password1)
            pswd.user.save()
            return redirect("/")
        else:
            context['code_error'] = _('Wrong secret code')
            context['secretcode'] = secretcode
            return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super(ForgotPasswordEnterView, self).get_context_data(**kwargs)
        context['secretcode'] = self.request.GET['secretcode']

        return context    
