# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org> # noqa
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
import uuid
import json
import string
import logging
from random import choice

from django.core import signing
from django.db.models import Q
from django.conf import settings
from django.db import IntegrityError
from django.contrib import auth, messages
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.views.generic import DetailView, View
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.utils.translation import ugettext, ugettext_lazy as _
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.views.generic.edit import BaseCreateView, UpdateView, FormView

from braces.views import LoginRequiredMixin, JSONResponseMixin
from sputnik.utils import LazyEncoder

from booktype.utils import config
from booktype.apps.core import views
from booktype.utils import misc, security
from booktype.apps.edit.models import InviteCode
from booktype.apps.edit.forms import MetadataForm
from booktype.apps.account.models import UserPassword
from booki.messaging.views import get_endpoint_or_none
from booktype.apps.core.models import Role, BookRole, BookSkeleton
from booktype.apps.core.views import BasePageView, PageView, SecurityMixin
from booktype.utils.book import check_book_availability, create_book
from booktype.utils.misc import has_book_limit
from booki.editor.models import (
    Book, BookHistory, BookiGroup, BookCover, Language, License)
from booktype.apps.importer.utils import (
    import_based_on_book, import_based_on_epub, import_based_on_file)

from . import tasks, utils
from .forms import UserSettingsForm, UserPasswordChangeForm, UserInviteForm, BookCreationForm

import booktype.apps.account.signals

logger = logging.getLogger('booktype.apps.account.views')


class DashboardPageView(SecurityMixin, BasePageView, DetailView):
    template_name = "account/dashboard.html"
    page_title = _('Dashboard')
    title = _('My Dashboard')

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'current_user'

    def check_permissions(self, request, *args, **kwargs):
        self.is_current_user_dashboard = kwargs.get(self.slug_url_kwarg, None) == self.request.user.username
        if not self.security.has_perm('account.can_view_user_info') and not self.is_current_user_dashboard:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(DashboardPageView, self).get_context_data(**kwargs)
        current_user = self.request.user

        context['is_admin'] = current_user.is_superuser
        # get all user permissions
        role_key = security.get_default_role_key(current_user)
        default_role = security.get_default_role(role_key)
        if default_role:
            context['roles_permissions'] = [p.key_name for p in default_role.permissions.all()]
        else:
            context['roles_permissions'] = []

        context['licenses'] = License.objects.all().order_by('name')
        context['languages'] = Language.objects.all()

        if self.is_current_user_dashboard:
            context['books'] = Book.objects.select_related('version').filter(
                owner=self.object).order_by('title')
        else:
            context['books'] = Book.objects.select_related('version').filter(
                owner=self.object, hidden=False).order_by('title')

        context['groups'] = BookiGroup.objects.filter(
            owner=self.object).order_by('name')

        context['participating_groups'] = BookiGroup.objects.filter(
            members=self.object).exclude(owner=self.object).order_by('name')

        # get books which user has collaborated on
        book_ids = set(BookHistory.objects.filter(user=self.object).values_list('book', flat=True).distinct())

        # get books with user assigned by roles
        book_ids.update(BookRole.objects.filter(members=self.object).values_list('book', flat=True).distinct())

        context['books_collaborating'] = Book.objects.filter(
            id__in=book_ids).exclude(owner=self.object).order_by('title')

        # get user recent activity
        context['recent_activity'] = BookHistory.objects.filter(
            user=self.object).order_by('-modified')[:3]

        context['can_upload_book'] = security.get_security(current_user).has_perm('account.can_upload_book')
        context['can_create_book'] = True

        # NOTE: base_books will be user's books for now, let's define with the rest of team
        # what should be a good logic to define existent books as skeletons
        form_kwargs = {'base_book_qs': context['books']}

        context['book_creation_form'] = BookCreationForm(
            initial={
                'language': config.get_configuration('CREATE_BOOK_LANGUAGE'),
                'license': config.get_configuration('CREATE_BOOK_LICENSE'),
                'visible_to_everyone': config.get_configuration('CREATE_BOOK_VISIBLE')
            }, **form_kwargs)

        # if only admin import then deny user permission to upload books
        if config.get_configuration('ADMIN_IMPORT_BOOKS'):
            if not current_user.is_superuser:
                context['can_upload_book'] = False

        # if only admin create then deny user permission to create new books
        if config.get_configuration('ADMIN_CREATE_BOOKS'):
            if not current_user.is_superuser:
                context['can_create_book'] = False

        # check if user can create/import more books
        context['is_book_limit'] = has_book_limit(current_user)

        if context['is_book_limit']:
            if not current_user.is_superuser:
                context['can_create_book'] = False
                context['can_upload_book'] = False
            else:
                context['is_book_limit'] = False

        # change title in case of not authenticated user
        if not current_user.is_authenticated() or \
           self.object != current_user:
            context['title'] = _('User profile')
            context['page_title'] = _('User profile')

        # Getting context variables for the form to invite users
        if current_user.is_authenticated():
            initial = {
                'message': getattr(settings, 'BOOKTYPE_DEFAULT_INVITE_MESSAGE', '')
            }
            context['invite_form'] = UserInviteForm(user=current_user, initial=initial)

        return context


class CreateBookView(LoginRequiredMixin, SecurityMixin, BaseCreateView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'user'

    def check_permissions(self, request, *args, **kwargs):
        if self.request.user.is_superuser:
            return

        # if only admin create then deny user permission to create new books
        if config.get_configuration('ADMIN_CREATE_BOOKS'):
            raise PermissionDenied

        # check if user can create more books
        if has_book_limit(self.request.user):
            raise PermissionDenied

    def get(self, request, *args, **kwargs):
        if request.GET.get('q', None) == "check":
            data = {
                "available": check_book_availability(
                    request.GET.get('bookname', '').strip())
            }
            return HttpResponse(json.dumps(data), 'application/json')

    def post(self, request, *args, **kwargs):
        # TODO: convert this into an atomic view
        # TODO: use the form class to achieve this process and simplify this view and add validations
        # TODO: we should print warnings so user knows what's going on

        data = request.POST
        book = create_book(request.user, data.get('title'))

        license = License.objects.get(abbrevation=data.get('license'))
        language = Language.objects.get(abbrevation=data.get('language'))

        # STEP 1: Details
        book.author = data.get('author')
        book.license = license
        book.language = language
        book.hidden = (data.get('visible_to_everyone', None) != 'on')
        book.description = data.get('description', '')

        # STEP 2: Metadata
        metaform = MetadataForm(book=book, data=data)
        if metaform.is_valid():
            metaform.save_settings(book, request)
        else:
            pass

        # STEP 3: Creation mode
        creation_mode = data.get('creation_mode', 'scratch')
        if creation_mode == 'based_on_book':
            try:
                base_book = Book.objects.get(id=request.POST.get('base_book'))
                base_book_version = base_book.get_version(None)
                result = import_based_on_book(base_book_version, book)
            except Book.DoesNotExist:
                logger.warn("Provided base book was not found")

        elif creation_mode == 'based_on_skeleton':
            try:
                base_skeleton = BookSkeleton.objects.get(id=request.POST.get('base_skeleton'))
                result = import_based_on_epub(base_skeleton.skeleton_file, book)
            except BookSkeleton.DoesNotExist:
                logger.warn("Provided base skeleton was not found")

        elif creation_mode == 'based_on_file':
            import_file = request.FILES.get('import_file')
            if import_file is not None:
                try:
                    result = import_based_on_file(import_file, book)  # noqa
                except Exception as err:
                    logger.error("ImportError: Something went wrong importing file. Msg %s" % err)

        # STEP 4: Book Cover
        if 'cover_image' in request.FILES:
            # first we create a cover registry and upload the file
            file_data = request.FILES['cover_image']
            filename = file_data.name

            cover_license = License.objects.get(abbrevation=data.get('cover_license'))

            cover = BookCover(
                book=book,
                user=request.user,
                cid=uuid.uuid4().hex,
                title=data.get('cover_title'),
                filename=filename[:250],
                creator=data.get('cover_creator', '')[:40],
                license=cover_license,
                approved=False)
            cover.save()

            # now save the cover attachment
            cover.attachment.save(filename, file_data, save=False)
            cover.save()

            # and then finally, we set the book thumbnail
            try:
                fh, fname = misc.save_uploaded_as_file(file_data)
                book.set_cover(fname)
                os.unlink(fname)
            except:
                pass

        book.save()

        redirect_url = reverse('reader:infopage', args=[book.url_title])
        return HttpResponse(json.dumps({'redirect': redirect_url}), 'application/json')


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
        dispatch_super = super(UserSettingsPage, self).dispatch(request, *args, **kwargs)

        if not request.user.is_authenticated():
            return dispatch_super

        if request.user.username == kwargs['username'] or \
           request.user.is_superuser:
            return dispatch_super
        else:
            return redirect(
                'accounts:user_settings', username=request.user.username)

    def get_context_data(self, **kwargs):
        context = super(UserSettingsPage, self).get_context_data(**kwargs)
        context['password_form'] = self.password_form_class(user=self.object)
        return context

    def form_valid(self, form):
        user = form.save()
        profile = user.profile
        profile.description = form.data.get('aboutyourself', '')
        profile.save()

        if 'profile_pic' in form.files:
            misc.set_profile_image(user, form.files['profile_pic'])
        else:
            if form.data.get('profile_pic_remove', False):
                profile.remove_image()

        try:
            ep_config = get_endpoint_or_none(
                '@%s' % user.username).get_config()
            ep_config.notification_filter = form.data.get('notification', '')
            ep_config.save()
        except:
            pass

        # send a success message to user
        messages.success(
            self.request, _('User settings have been saved successfully!'))

        return redirect(self.get_success_url())

    def get_initial(self):
        profile = self.object.profile
        initial = super(UserSettingsPage, self).get_initial()
        initial['aboutyourself'] = profile.description
        endpoint = get_endpoint_or_none('@%s' % self.object.username)
        try:
            endpoint_config = endpoint.get_config()
            initial['notification'] = endpoint_config.notification_filter
        except Exception:
            initial['notification'] = ''

        if profile.image:
            initial['profile_pic'] = profile.image.url
        return initial

    def get_success_url(self):
        return reverse(
            'accounts:view_profile', args=[self.get_object().username])

    def post(self, request, *args, **kwargs):
        """
        Overrides the post method in order to handle settings form and
        also password form
        """

        if 'password_change' in request.POST:
            form = self.password_form_class(user=request.user, data=request.POST)
            if form.is_valid():
                # save password form
                form.save()

                # send a success message to user
                messages.success(
                    self.request, _('Password changed successfully!'))

                return redirect(reverse('accounts:signin'))
            else:
                self.object = self.get_object()
                form_class = self.get_form_class()

                context = self.get_context_data()
                context.update({
                    'form': form_class(
                        instance=self.object,
                        initial=self.get_initial()
                    ),
                    'password_form': form,
                })

                return self.render_to_response(context)

        return super(UserSettingsPage, self).post(request, *args, **kwargs)


class ForgotPasswordView(PageView):
    template_name = "account/forgot_password.html"
    page_title = _('Forgot your password')
    title = _('Forgot your password')

    def get_context_data(self, **kwargs):
        context = super(ForgotPasswordView, self).get_context_data(**kwargs)

        context['is_admin'] = self.request.user.is_superuser
        # get all user permissions
        role_key = security.get_default_role_key(self.request.user)
        default_role = security.get_default_role(role_key)
        if default_role:
            context['roles_permissions'] = [p.key_name for p in default_role.permissions.all()]
        else:
            context['roles_permissions'] = []

        return context

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

        THIS_BOOKTYPE_SERVER = config.get_configuration('THIS_BOOKTYPE_SERVER')  # noqa
        for usr in users_to_email:
            secretcode = self.generate_secret_code()

            usr_obj = UserPassword()
            usr_obj.user = usr
            usr_obj.remote_useragent = request.META.get('HTTP_USER_AGENT', '')
            usr_obj.remote_addr = request.META.get('REMOTE_ADDR', '')
            usr_obj.remote_host = request.META.get('REMOTE_HOST', '')
            usr_obj.secretcode = secretcode

            body = render_to_string(
                'account/password_reset_email.html',
                dict(secretcode=secretcode, hostname=THIS_BOOKTYPE_SERVER)
            )

            msg = EmailMessage(
                _('Reset password'), body,
                settings.DEFAULT_FROM_EMAIL, [usr.email]
            )
            msg.content_subtype = 'html'

            # In case of an error we really should not send email
            # to user and do rest of the procedure

            try:
                usr_obj.save()
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
        context = super(
            ForgotPasswordEnterView, self).get_context_data(**kwargs)

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
        context = super(
            ForgotPasswordEnterView, self).get_context_data(**kwargs)
        context['secretcode'] = self.request.GET['secretcode']

        return context


class SignInView(PageView):
    template_name = "account/register.html"
    page_title = _('Log in')
    title = _('Log in')

    def get_context_data(self, **kwargs):
        context = super(SignInView, self).get_context_data(**kwargs)
        try:
            context['invite_email'] = self.request.session['invite_data']['email']
        except KeyError:
            pass

        context['is_admin'] = self.request.user.is_superuser
        # get all user permissions
        role_key = security.get_default_role_key(self.request.user)
        default_role = security.get_default_role(role_key)
        if default_role:
            context['roles_permissions'] = [p.key_name for p in default_role.permissions.all()]
        else:
            context['roles_permissions'] = []
        return context

    def _check_if_empty(self, request, key):
        return request.POST.get(key, "").strip() == ""

    def _do_checks_for_empty(self, request):
        if self._check_if_empty(request, "username"):
            return 2
        if self._check_if_empty(request, "email"):
            return 3
        if self._check_if_empty(request, "password") or \
           self._check_if_empty(request, "password2"):
            return 4
        if self._check_if_empty(request, "fullname"):
            return 5

        return 0

    def get(self, request):
        signed_data = request.GET.get('data', None)

        if request.user.is_authenticated() and signed_data:
            assign_invitation(request.user, signing.loads(signed_data))
            return HttpResponseRedirect(reverse('portal:frontpage'))

        elif signed_data:
            request.session['invite_data'] = signing.loads(signed_data)

        return super(SignInView, self).get(request)

    def _do_check_valid(self, request):
        # check if it is valid username
        # - from 2 to 20 characters long
        # - word, number, ., _, -
        mtch = re.match(
            '^[\w\d\_\.\-]{2,20}$', request.POST.get("username", "").strip())
        if not mtch:
            return 6

        # check if it is valid email
        if not bool(misc.is_valid_email(request.POST["email"].strip())):
            return 7

        if request.POST.get("password", "") != \
           request.POST.get("password2", "").strip():
            return 8
        if len(request.POST.get("password", "").strip()) < 6:
            return 9

        if len(request.POST.get("fullname", "").strip()) > 30:
            return 11

        # check if this user exists
        try:
            auth.models.User.objects.get(
                username=request.POST.get("username", "").strip())
            return 10
        except auth.models.User.DoesNotExist:
            pass

        # TODO all this register logic is horrible, we must rewrite it completely
        # check if this email exists
        try:
            auth.models.User.objects.get(
                email=request.POST.get("email", "").strip())
            return 12
        except auth.models.User.MultipleObjectsReturned:
            return 12
        except auth.models.User.DoesNotExist:
            pass

        return 0

    def post(self, request, *args, **kwargs):
        limit_reached = misc.is_user_limit_reached()

        username = request.POST["username"].strip()
        password = request.POST["password"].strip()

        if request.POST.get("ajax", "") == "1":
            ret = {"result": 0}

            if request.POST.get("method", "") == "register" and \
               config.get_configuration('FREE_REGISTRATION') and \
               not limit_reached:
                email = request.POST["email"].strip()
                fullname = request.POST["fullname"].strip()
                ret["result"] = self._do_checks_for_empty(request)

                if ret["result"] == 0:  # if there was no errors
                    ret["result"] = self._do_check_valid(request)

                    if ret["result"] == 0:
                        ret["result"] = 1

                        user = None
                        try:
                            user = auth.models.User.objects.create_user(
                                username=username, email=email, password=password)
                        except IntegrityError:
                            ret["result"] = 10
                        except:
                            ret["result"] = 10
                            user = None

                        # this is not a good place to fire signal, but i need password for now
                        # should create function createUser for future use

                        if user:
                            user.first_name = fullname

                            booktype.apps.account.signals.account_created.send(
                                sender=user,
                                password=request.POST['password'],
                                post_params=request.POST
                            )

                            try:
                                user.save()

                                # groups

                                for group_name in json.loads(request.POST.get('groups')):
                                    if group_name.strip() != '':
                                        try:
                                            group = BookiGroup.objects.get(url_name=group_name)
                                            group.members.add(user)
                                        except:
                                            pass

                                user2 = auth.authenticate(username=username, password=password)
                                auth.login(request, user2)
                            except:
                                ret['result'] = 666

            if request.POST.get('method', '') == 'signin':
                user = auth.authenticate(username=username, password=password)

                if user and user.is_active:
                    auth.login(request, user)
                    ret['result'] = 1
                elif user and not user.is_active:
                    ret['result'] = 4
                else:
                    try:
                        auth.models.User.objects.get(username=username)
                        # User does exist. Must be wrong password then
                        ret['result'] = 3
                    except auth.models.User.DoesNotExist:
                        # User does not exist
                        ret['result'] = 2

            if ret['result'] == 1:
                invite_data = request.session.pop('invite_data', False)
                if invite_data:
                    assign_invitation(user, invite_data)

            return HttpResponse(json.dumps(ret), content_type="text/json")
        return HttpResponseBadRequest()


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
        user = User.objects.get(username=profileid)
    except User.DoesNotExist:
        return views.ErrorPage(request, 'errors/user_does_not_exist.html', {'username': profileid})

    profile_image = utils.get_profile_image(user, int(request.GET.get('width', 24)))
    return redirect(profile_image)


class SendInviteView(PageView, FormView):
    form_class = UserInviteForm
    initial = {
        'message': getattr(settings, 'BOOKTYPE_DEFAULT_INVITE_MESSAGE', '')
    }

    def get_form_kwargs(self):
        kwargs = super(SendInviteView, self).get_form_kwargs()
        kwargs['user'] = self.request.user

        return kwargs

    def form_valid(self, form):
        tasks.send_invite_emails.delay(
            email_list=form.cleaned_data['email_list'],
            message=form.cleaned_data['message'],
            book_ids=[b.id for b in form.cleaned_data['books']],
            role_ids=[r.id for r in form.cleaned_data['roles']]
        )
        return HttpResponse('{"success": true}', 'text/json')

    def form_invalid(self, form):
        return HttpResponse(json.dumps(form.errors), 'text/json')


def assign_invitation(user, invite_data):
    """
    Assigns roles to the user based on the information found in the invitation link
    """
    if user.email != invite_data['email']:
        return

    books = Book.objects.filter(pk__in=invite_data['book_ids'])
    roles = Role.objects.filter(pk__in=invite_data['role_ids'])

    for book in books:
        for role in roles:
            book_role, _ = BookRole.objects.get_or_create(role=role, book=book)
            book_role.members.add(user)


class JoinWithCode(LoginRequiredMixin, JSONResponseMixin, View):

    http_method_names = [u'post']
    json_encoder_class = LazyEncoder

    def response(self, data):
        return self.render_json_response(data)

    def post(self, request, *args, **kwargs):
        invite_code = request.POST.get('invite_code', None)
        if invite_code is None:
            return self.response({'result': False})

        try:
            code = InviteCode.objects.get(code=invite_code.lower())

            # if code is expired, go away
            if code.expired:
                return self.response({'result': False})

            for role in code.roles.all():
                book_role, _ = BookRole.objects.get_or_create(role=role, book=code.book)
                book_role.members.add(request.user)

            # TODO: send notification so others users knows about new collaborator joined book

            msg = ugettext('You have been added to "{}". Click Accept button to reload screen and see the book').format(
                code.book.title)

            return self.response({
                'result': True, 'message': msg,
                'redirect_url': reverse(
                    'reader:infopage', args=[code.book.url_title])
            })

        except Exception:
            return self.response({'result': False})
