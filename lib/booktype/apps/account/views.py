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


import re
import os
import string
import json
from random import choice

from django.contrib import messages
from django.views.generic import DetailView, View
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.edit import BaseCreateView, UpdateView
from django.contrib import auth
from django.db import IntegrityError
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.db.models import Q
from django.conf import settings


from braces.views import LoginRequiredMixin
from booktype.utils import config
from booktype.utils import misc
from booki.messaging.views import get_endpoint_or_none
from booktype.utils.book import check_book_availability, create_book
from booki.editor.models import Book, License, BookHistory, BookiGroup
from booktype.apps.account.models import UserPassword
from booktype.apps.core import views
import booktype.apps.account.signals
from booktype.apps.core.views import BasePageView, PageView

from .forms import UserSettingsForm, UserPasswordChangeForm


class DashboardPageView(BasePageView, DetailView):
    template_name = "account/dashboard.html"
    page_title = _('Dashboard')
    title = _('My Dashboard')

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'current_user'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['books'] = Book.objects.filter(owner=self.object).order_by('title')
        context['licenses'] = License.objects.all().order_by('name')
        context['groups'] = BookiGroup.objects.filter(owner=self.object).order_by('name')
        context['participating_groups'] = BookiGroup.objects.filter(members=self.object).exclude(owner=self.object).order_by('name')

        # get books with user has collaborated with
        book_ids = BookHistory.objects.filter(user=self.object).values_list('book', flat=True).distinct()
        context['books_collaborating'] = Book.objects.filter(id__in=book_ids).exclude(owner=self.object).order_by('title')

        # get user recent activity
        context['recent_activity'] = BookHistory.objects.filter(user=self.object).order_by('-modified')[:3]

        context['book_license'] = config.get_configuration('CREATE_BOOK_LICENSE')
        context['book_visible'] = config.get_configuration('CREATE_BOOK_VISIBLE')

        # change title in case of not authenticated user
        if not self.request.user.is_authenticated() or self.object != self.request.user:
            context['title'] = _('User profile')
            context['page_title'] = _('User profile')

        return context


class CreateBookView(LoginRequiredMixin, BaseCreateView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'user'

    def get(self, request, *args, **kwargs):
        if request.GET.get('q', None) == "check":
            data = {
                "available": check_book_availability(request.GET.get('bookname', '').strip())
            }
            return HttpResponse(json.dumps(data), "application/json")

    def post(self, request, *args, **kwargs):
        book = create_book(request.user, request.POST.get('title'))
        lic = License.objects.get(abbrevation=request.POST.get('license'))

        book.license = lic
        book.description = request.POST.get('description', '')
        book.hidden = (request.POST.get('hidden', None) == 'on')

        if 'cover' in request.FILES:
            try:
                fh, fname = misc.save_uploaded_as_file(request.FILES['cover'])
                book.setCover(fname)
                os.unlink(fname)
            except:
                pass

        book.save()

        return render(
            request,
            'account/create_book_redirect.html',
            {"request": request, "book": book}
        )


class UserSettingsPage(LoginRequiredMixin, BasePageView, UpdateView):
    template_name = "account/dashboard_settings.html"
    page_title = _('Settings')
    title = _('Settings')

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'current_user'
    form_class = UserSettingsForm
    password_form_class = UserPasswordChangeForm

    def dispatch(self, request, *args, **kwargs):
        dispatch_super = super(self.__class__, self).dispatch(request, *args, **kwargs)

        if not request.user.is_authenticated():
            return dispatch_super

        if request.user.username == kwargs['username'] or request.user.is_superuser:
            return dispatch_super
        else:
            return redirect('accounts:user_settings', username=request.user.username)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['password_form'] = self.password_form_class(user=self.object)
        return context

    def form_valid(self, form):
        user = form.save()
        profile = user.get_profile()
        profile.description = form.data.get('aboutyourself', '')
        profile.save()

        if form.files.has_key('profile_pic'):
            misc.set_profile_image(user, form.files['profile_pic'])
        else:
            if form.data.get('profile_pic_remove', False):
                profile.remove_image()

        try:
            endpoint_config = get_endpoint_or_none("@"+user.username).get_config()
            endpoint_config.notification_filter = form.data.get('notification', '')
            endpoint_config.save()
        except:
            pass

        # send a success message to user
        messages.success(self.request, _('User settings has been successfully saved!'))

        return redirect(self.get_success_url())

    def get_initial(self):
        profile = self.object.get_profile()
        initial = super(self.__class__, self).get_initial()
        initial['aboutyourself'] = profile.description
        endpoint = get_endpoint_or_none("@"+self.object.username)
        try:
            endpoint_config = endpoint.get_config()
            initial['notification'] = endpoint_config.notification_filter
        except Exception:
            initial['notification'] = ''

        if profile.image:
            initial['profile_pic'] = profile.image.url
        return initial

    def get_success_url(self):
        return reverse('accounts:view_profile', args=[self.get_object().username])

    def post(self, request, *args, **kwargs):
        '''
        Overrides the post method in order to handle settings form and
        also password form
        '''

        if 'password_change' in request.POST:
            form = self.password_form_class(user=request.user, data=request.POST)
            if form.is_valid():
                # save password form
                form.save()

                # send a success message to user
                messages.success(self.request, _('Password changed successfully!'))

                return redirect(self.get_success_url())
            else:
                self.object = self.get_object()
                form_class = self.get_form_class()

                context = self.get_context_data()
                context.update({
                    'form': form_class(instance=self.object, initial=self.get_initial()),
                    'password_form': form,
                })

                return self.render_to_response(context)

        return super(self.__class__, self).post(request, *args, **kwargs)


class ForgotPasswordView(PageView):
    template_name = "account/forgot_password.html"
    page_title = _('Forgot your password')
    title = _('Forgot your password')

    def generate_secret_code(self):
        return ''.join([choice(string.letters + string.digits) for i in range(30)])

    def post(self, request, *args, **kwargs):
        context = super(ForgotPasswordView, self).get_context_data(**kwargs)
        if "name" not in request.POST:
            return views.ErrorPage(request, "errors/500.html")

        name = request.POST["name"].strip()

        users_to_email = list(User.objects.filter(Q(username=name) | Q(email=name)))
        if len(name) == 0:
            context['error'] = _('Missing username')
            return render(request, self.template_name, context)

        if len(users_to_email) == 0:
            context['error'] = _('No such user')
            return render(request, self.template_name, context)

        THIS_BOOKTYPE_SERVER = config.get_configuration('THIS_BOOKTYPE_SERVER')
        for usr in users_to_email:
            secretcode = self.generate_secret_code()

            account_models = UserPassword()
            account_models.user = usr
            account_models.remote_useragent = request.META.get('HTTP_USER_AGENT', '')
            account_models.remote_addr = request.META.get('REMOTE_ADDR', '')
            account_models.remote_host = request.META.get('REMOTE_HOST', '')
            account_models.secretcode = secretcode

            body = render_to_string('account/password_reset_email.html',
                                    dict(secretcode=secretcode, hostname=THIS_BOOKTYPE_SERVER))

            msg = EmailMessage(_('Reset password'), body, settings.REPORT_EMAIL_USER, [usr.email])
            msg.content_subtype = 'html'

            # In case of an error we really should not send email to user and do rest of the procedure

            try:
                account_models.save()
                msg.send()
                context['mail_sent'] = True
            except:
                context['error'] = _('Unknown error')

        return render(request, self.template_name, context)


class ForgotPasswordEnterView(PageView):
    template_name = "account/forgot_password_enter.html"
    page_title = _('Reset your password')
    title = _('Reset your password')

    def post(self, request, *args, **kwargs):
        context = super(ForgotPasswordEnterView, self).get_context_data(**kwargs)

        if "secretcode" and "password1" and "password2" not in request.POST:
            return views.ErrorPage(request, "errors/500.html")

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
            return redirect(reverse('accounts:signin'))
        else:
            context['code_error'] = _('Wrong secret code')
            context['secretcode'] = secretcode
            return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super(ForgotPasswordEnterView, self).get_context_data(**kwargs)
        context['secretcode'] = self.request.GET['secretcode']

        return context


class SignInView(PageView):
    template_name = "account/register.html"
    page_title = _('Sign in')
    title = _('Sign in')

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        return context

    def _check_if_empty(self, request, key):
        return request.POST.get(key, "").strip() == ""

    def _do_checks_for_empty(self, request):
        if self._check_if_empty(request, "username"):
            return 2
        if self._check_if_empty(request, "email"):
            return 3
        if self._check_if_empty(request, "password") or self._check_if_empty(request, "password2"):
            return 4
        if self._check_if_empty(request, "fullname"):
            return 5

        return 0

    def _do_check_valid(self, request):
        # check if it is valid username
        # - from 2 to 20 characters long
        # - word, number, ., _, -
        mtch = re.match('^[\w\d\_\.\-]{2,20}$', request.POST.get("username", "").strip())
        if not mtch:
            return 6

        # check if it is valid email
        if not bool(misc.is_valid_email(request.POST["email"].strip())):
            return 7

        if request.POST.get("password", "") != request.POST.get("password2", "").strip():
            return 8
        if len(request.POST.get("password", "").strip()) < 6:
            return 9

        if len(request.POST.get("fullname", "").strip()) > 30:
            return 11

        # check if this user exists
        try:
            u = auth.models.User.objects.get(username=request.POST.get("username", "").strip())
            return 10
        except auth.models.User.DoesNotExist:
            pass

        return 0

    def post(self, request, *args, **kwargs):
        limit_reached = misc.is_user_limit_reached()

        username = request.POST["username"].strip()
        password = request.POST["password"].strip()

        if request.POST.get("ajax", "") == "1":
            ret = {"result": 0}

            if request.POST.get("method", "") == "register" and config.get_configuration('FREE_REGISTRATION') and not limit_reached:
                email = request.POST["email"].strip()
                fullname = request.POST["fullname"].strip()
                ret["result"] = self._do_checks_for_empty(request)

                if ret["result"] == 0:  # if there was no errors
                    ret["result"] = self._do_check_valid(request)

                    if ret["result"] == 0:
                        ret["result"] = 1

                        user = None
                        try:
                            user = auth.models.User.objects.create_user(username=username,
                                                                        email=email,
                                                                        password=password)
                        except IntegrityError:
                            ret["result"] = 10
                        except:
                            ret["result"] = 10
                            user = None

                        # this is not a good place to fire signal, but i need password for now
                        # should create function createUser for future use

                        if user:
                            user.first_name = fullname

                            booktype.apps.account.signals.account_created.send(sender=user, password=request.POST["password"])

                            try:
                                user.save()

                                # groups

                                for group_name in json.loads(request.POST.get("groups")):
                                    if group_name.strip() != '':
                                        try:
                                            group = BookiGroup.objects.get(url_name=group_name)
                                            group.members.add(user)
                                        except:
                                            pass

                                user2 = auth.authenticate(username=username, password=password)
                                auth.login(request, user2)
                            except:
                                ret["result"] = 666

            if request.POST.get("method", "") == "signin":
                user = auth.authenticate(username=username, password=password)

                if user:
                    auth.login(request, user)
                    ret["result"] = 1
                else:
                    try:
                        usr = auth.models.User.objects.get(username=username)
                        # User does exist. Must be wrong password then
                        ret["result"] = 3
                    except auth.models.User.DoesNotExist:
                        # User does not exist
                        ret["result"] = 2

            try:
                resp = HttpResponse(json.dumps(ret), mimetype="text/json")
            except:
                raise
        return resp


class SignOutView(View):

    def get(self, request):

        auth.logout(request)
        return HttpResponseRedirect(reverse("portal:frontpage"))


def profilethumbnail(request, profileid):
    """
    Django View. Shows user profile image.

    One of the problems with this view is that it does not handle gravatar images.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request
    @type profileid: C{string}
    @param profileid: Username.

    @todo: Check if user exists.
    """

    try:
        u = User.objects.get(username=profileid)
    except User.DoesNotExist:
        return views.ErrorPage(request, "errors/user_does_not_exist.html", {"username": profileid})

    name = ''

    def _get_default_profile():
        "Return path to default profile image."

        try:
            name = '%s/account/images/%s' % (settings.STATIC_ROOT, settings.DEFAULT_PROFILE_IMAGE)
        except AttributeError:
            name = '%s%s' % (settings.STATIC_ROOT, '/account/images/anonymous.png')

        return name

    # this should be a seperate function

    if not u.get_profile().image:
        name = _get_default_profile()
    else:
        name = u.get_profile().image.path

    try:
        from PIL import Image
    except ImportError:
        import Image

    # Don't do much in case of Image handling errors

    try:
        image = Image.open(name)
    except IOError:
        image = Image.open(_get_default_profile())

    image.thumbnail((int(request.GET.get('width', 24)), int(request.GET.get('width', 24))), Image.ANTIALIAS)

    response = HttpResponse(mimetype="image/jpg")
    image.save(response, "JPEG")

    return response
