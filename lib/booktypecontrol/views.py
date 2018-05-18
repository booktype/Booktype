# This file is part of Booktype.
# Copyright (c) 2012
# Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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
import json
import logging
import sputnik
import forms as control_forms
from unipath import Path
from datetime import datetime, timedelta, date
import git

from collections import Counter, OrderedDict

from django import template
from django.conf import settings
from django.db import connection
from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.mail import EmailMultiAlternatives

from django.views.generic import TemplateView, FormView, ListView, View
from django.views.generic import DetailView, UpdateView, DeleteView
from django.views.generic.detail import SingleObjectMixin

from braces.views import LoginRequiredMixin, SuperuserRequiredMixin

from booktype.utils import misc, config
from booktype.apps.core.models import Role, BookSkeleton
from booktype.apps.core.views import BasePageView
from booki.editor.models import Book, BookiGroup, BookHistory, License
from booktype.apps.export.models import BookExport, ExportFile

from .forms import UserSearchForm

logger = logging.getLogger('booktype')


OPTION_NAMES = {
    'site-description': _('Site Description'),
    'appearance': _('Site Appearance'),
    'frontpage': _('Site Front Page'),
    'license': _('Book Licenses'),
    'book-settings': _('Book Creation Defaults'),
    'privacy': _('Privacy'),
    'add-person': _('Add a New Person'),
    'archived-users': _('Archived Users'),
    'add-book': _('Add a New Book'),
    'list-of-books': _('List of Books'),
    'add-skeleton': _('Add Book Skeleton'),
    'list-of-skeletons': _('Book Skeletons'),
    'publishing': _('Publishing Options'),
    'publishing-defaults': _('Publishing Defaults'),
    'add-group': _('Add a New Group'),
    'list-of-groups': _('List of Groups'),
    'add-role': _('Add a New Role'),
    'list-of-roles': _('List of Roles'),
    'default-roles': _('Default Roles')
}

VALID_OPTIONS = OPTION_NAMES.keys()


class BaseCCView(LoginRequiredMixin, SuperuserRequiredMixin, BasePageView):

    def get_context_data(self, *args, **kwargs):
        context = super(BaseCCView, self).get_context_data(*args, **kwargs)
        context['valid_options'] = VALID_OPTIONS
        return context


class ControlCenterView(BaseCCView, TemplateView):
    """
    Renders the control center dashboard based in user rights

    """

    template_name = 'booktypecontrol/control_center_dashboard.html'
    page_title = _('Admin Control Center')
    title = page_title

    def get_context_data(self, **kwargs):
        context = super(ControlCenterView, self).get_context_data(**kwargs)
        context['stats'] = self.get_stats()
        context['online_users'] = self.get_online_users()

        # most active base var
        most_active_query = BookHistory.objects.filter(kind=2)

        # now get the most active users base on saving chapters history
        users = most_active_query.filter(chapter__isnull=False).values_list('user', flat=True)
        most_actives = [pk for pk, _y in Counter(users).most_common()[:5]]
        most_active_users = User.objects.filter(id__in=most_actives)

        # we need to keep the order of frequency found by most_common method
        most_active_users = list(most_active_users)
        most_active_users.sort(key=lambda u: most_actives.index(u.pk))

        # let's get latest bookhistory with chapter connected
        most_active_users_history = OrderedDict()
        for user in most_active_users:
            most_active_users_history[user] = most_active_query.filter(user=user).last()

        context['most_active_users_history'] = most_active_users_history

        # get latest books
        context['latest_books'] = Book.objects.order_by('-created')[:4]

        # most active books
        books = most_active_query.values_list('book', flat=True)
        most_active_books = Counter(books).most_common()[:4]
        context['most_active_books'] = Book.objects.filter(
            id__in=[id for id, freq in most_active_books]
        )

        # recent activity
        context['recent_activity'] = BookHistory.objects.filter(
            kind__in=[1, 10]).order_by('-modified')[:20]

        return context

    def get_stats(self):
        # This should not be here in the future. It takes way too much time.
        attachment_directory = '%s/books/' % (settings.DATA_ROOT, )
        attachments_size = misc.get_directory_size(attachment_directory)

        # check the database size
        cursor = connection.cursor()

        try:
            # This will not work if user has new style of configuration
            # for the database. This will also only work for PostgreSQL.
            # Should make another method for checking sqlite database size.
            cursor.execute(
                "SELECT pg_database_size(%s)",
                [settings.DATABASES['default']['NAME']]
            )
            databaseSize = cursor.fetchone()[0]
        except:
            databaseSize = 0

        # git
        gitrepo = git.Repo(Path(os.path.abspath(__file__)).ancestor(3))

        _since = datetime.now() - timedelta(days=30)
        log_stdout = gitrepo.git.log(
            '--since={}'.format(_since.strftime("%Y-%m-%d"))
        )

        return {
            'version': gitrepo.tags[-1],
            'git_log': log_stdout,
            'users': User.objects.filter(is_active=True).count(),
            'books': Book.objects.count(),
            'groups': BookiGroup.objects.count(),
            'attach_size': attachments_size,
            'db_size': databaseSize
        }

    def get_online_users(self):
        client_list = sputnik.rkeys("ses:*:username")
        online_users = {}

        for us in client_list:
            clientID = us[4:-9]

            channel_list = []
            for chan in sputnik.smembers('ses:%s:channels' % clientID):
                if chan.startswith('/booktype/book/'):
                    _s = chan.split('/')
                    if len(_s) > 3:
                        bookID = _s[3]
                        try:
                            b = Book.objects.get(pk=bookID)
                            channel_list.append(b)
                        except Book.DoesNotExist:
                            pass

            _u = sputnik.get(us)
            online_users[_u] = channel_list

        return online_users


class ControlCenterSettings(BaseCCView, FormView):
    """
    Generic class for control center settings
    """

    template_name = 'booktypecontrol/control_center_settings.html'
    submodule = 'site-description'
    success_url = reverse_lazy('control_center:settings')
    page_title = _('Admin Control Center')
    title = page_title

    def camelize(self, text):
        return ''.join([s for s in text.title() if s.isalpha()])

    def form_valid(self, form):
        try:
            form.save_settings(self.request)
            messages.success(
                self.request,
                form.success_message or _('Successfully saved settings.')
            )
        except Exception as err:
            print err
            messages.warning(self.request,
                             _('Unknown error while saving changes.'))
        return super(ControlCenterSettings, self).form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        # if redirect param is present, go to right submodule
        _request_data = getattr(request, request.method)

        redirect = _request_data.get('redirect', None)
        if redirect and redirect in VALID_OPTIONS:
            return HttpResponseRedirect(
                '{0}#{1}'.format(reverse('control_center:settings'), redirect))

        option = _request_data.get('option', None)
        if option and option in VALID_OPTIONS:
            self.submodule = option
        return super(ControlCenterSettings, self).dispatch(
            request, *args, **kwargs
        )

    def get_form_class(self):
        class_text = "%sForm" % self.camelize(self.submodule)
        self.form_class = getattr(control_forms, class_text)
        return self.form_class

    def get_initial(self):
        """
        Returns initial data for each admin option form
        """
        return self.form_class.initial_data()

    def get_template_names(self):
        if self.request.is_ajax():
            return [
                "booktypecontrol/_control_center_%s.html"
                % self.submodule.replace('-', '_'),
                "booktypecontrol/_control_center_settings.html"
            ]
        return super(ControlCenterSettings, self).get_template_names()

    def get_context_data(self, *args, **kwargs):
        context = super(ControlCenterSettings, self).get_context_data(
            *args, **kwargs)
        context['option'] = self.submodule
        context['option_name'] = OPTION_NAMES.get(self.submodule, '')

        extra_context = self.form_class.extra_context()
        if extra_context:
            context.update(extra_context)
        return context

    def get_success_url(self):
        # if form class has custom success url
        success_url = self.form_class.success_url
        if not success_url:
            success_url = "#%s" % self.submodule

        if success_url and "#" in success_url:
            return "{0}{1}".format(self.success_url, success_url)
        return super(ControlCenterSettings, self).get_success_url()


class PeopleListView(BaseCCView, ListView):
    model = User
    paginate_by = 50
    page_title = _('List of people')
    title = page_title
    template_name = "booktypecontrol/control_center_people_list.html"

    def get_queryset(self):
        users_qs = User.objects.filter(is_active=True).order_by("username")

        if 'search' in self.request.GET:
            users_qs = users_qs.filter(
                Q(username__icontains=self.request.GET.get('search')) |
                Q(first_name__icontains=self.request.GET.get('search')) |
                Q(last_name__icontains=self.request.GET.get('search')) |
                Q(email__icontains=self.request.GET.get('search'))
            )

        return users_qs

    def get_context_data(self, **kwargs):
        context = super(PeopleListView, self).get_context_data(**kwargs)

        if 'search' in self.request.GET:
            search_form = UserSearchForm(self.request.GET)
        else:
            search_form = UserSearchForm()

        context['search_form'] = search_form

        return context


class PersonInfoView(BaseCCView, DetailView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'current_user'
    template_name = "booktypecontrol/_control_center_modal_person_info.html"

    def get_context_data(self, *args, **kwargs):
        context = super(PersonInfoView, self).get_context_data(*args, **kwargs)
        person = self.object
        context['books'] = Book.objects.filter(owner=person)
        context['groups'] = BookiGroup.objects.filter(owner=person)
        context['activity'] = BookHistory.objects.filter(
            user=person, kind__in=[1, 10]).order_by('-modified')[:20]
        return context


class EditPersonInfo(BaseCCView, UpdateView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'current_user'
    form_class = control_forms.EditPersonInfoForm
    page_title = _('Admin Control Center')
    title = page_title
    template_name = "booktypecontrol/control_center_settings.html"
    option_name = _('Edit Person Info')

    def get_context_data(self, *args, **kwargs):
        context = super(EditPersonInfo, self).get_context_data(*args, **kwargs)
        context['option'] = None
        context['option_name'] = self.option_name
        return context

    def form_valid(self, form):
        self.object = form.save()
        profile = self.object.profile
        profile.description = form.cleaned_data['description']
        profile.save()

        if 'profile' in form.files:
            misc.set_profile_image(self.object, form.files['profile'])
        else:
            if form.data.get('profile_remove', False):
                profile.remove_image()

        messages.success(self.request, _('Successfully saved changes.'))

        return HttpResponseRedirect(self.get_success_url())

    def get_initial(self):
        initial_dict = super(EditPersonInfo, self).get_initial()
        profile = self.object.profile
        initial_dict['description'] = profile.description
        if profile.image:
            initial_dict['profile'] = profile.image.url
        return initial_dict

    def get_success_url(self):
        return reverse_lazy('control_center:people_list')


class BookRenameView(EditPersonInfo):
    model = Book
    slug_field = 'url_title'
    slug_url_kwarg = 'bookid'
    form_class = control_forms.BookRenameForm
    template_name = "booktypecontrol/control_center_settings.html"
    option_name = _('Rename Book')

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _('Book name successfully changed.'))
        return HttpResponseRedirect(self.get_success_url())

    def get_initial(self):
        return {}

    def get_success_url(self):
        return "%s#list-of-books" % reverse('control_center:settings')


class PasswordChangeView(BaseCCView, FormView, SingleObjectMixin):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'current_user'
    page_title = _('Admin Control Center')
    title = page_title
    template_name = "booktypecontrol/control_center_settings.html"

    def get_form(self, form_class=control_forms.PasswordForm):
        self.object = self.get_object()
        return form_class(user=self.object, **self.get_form_kwargs())

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _('Successfully saved changes.'))

        if form.cleaned_data['send_login_data']:
            t = template.loader.get_template('booktypecontrol/password_changed_email.html')
            content = t.render({
                "username": self.object.username,
                "password": form.cleaned_data['password2'],
                "short_message": form.cleaned_data['short_message']
            })

            msg = EmailMultiAlternatives(
                _('Your password was changed'),
                content, settings.DEFAULT_FROM_EMAIL,
                [self.object.email]
            )
            msg.attach_alternative(content, "text/html")
            try:
                msg.send(fail_silently=False)
            except Exception as e:
                logger.error(
                    '[CCENTER] Unable to send email to %s after password was changed, msg: %s' %
                    (self.object.email, e)
                )

        return super(FormView, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super(PasswordChangeView, self).get_context_data(
            *args, **kwargs)
        context['option'] = None
        context['option_name'] = _('Change Password: %s') % self.object.username
        return context

    def get_success_url(self):
        return reverse_lazy('control_center:people_list')


class DeleteGroupView(BaseCCView, DeleteView):
    model = BookiGroup
    slug_field = 'url_name'
    slug_url_kwarg = 'groupid'
    context_object_name = 'group'
    template_name = 'booktypecontrol/_control_center_modal_delete_group.html'

    def get_success_url(self):
        messages.success(self.request, _('Group successfully deleted.'))
        return "%s#list-of-groups" % reverse('control_center:settings')

    def delete(self, request, *args, **kwargs):
        group = self.get_object()

        # remove books from group
        group.book_set.update(group=None)

        # delete group images if needed
        try:
            group.remove_group_images()
        except Exception as e:
            print e

        return super(DeleteGroupView, self).delete(request, *args, **kwargs)


class LicenseEditView(BaseCCView, UpdateView):
    model = License
    context_object_name = 'license'
    form_class = control_forms.LicenseForm
    page_title = _('Admin Control Center')
    title = page_title
    template_name = "booktypecontrol/_control_center_license_edit.html"

    def get_context_data(self, *args, **kwargs):
        context = super(LicenseEditView, self).get_context_data(
            *args, **kwargs)
        context['option'] = 'license'
        context['option_name'] = _('Edit licence')
        context['licensed_books'] = Book.objects.filter(
            license=self.object).order_by('title')
        return context

    def get_success_url(self):
        messages.success(self.request, _('License successfully updated.'))
        return "%s#license" % reverse('control_center:settings')


class DeleteLicenseView(BaseCCView, DeleteView):
    model = License
    context_object_name = 'license'
    template_name = 'booktypecontrol/_control_center_modal_delete_license.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.book_set.all():
            _suc_msg = _('There are books remaining with this license. \
                    Unable to remove')
            messages.warning(self.request, _suc_msg)
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.success(self.request, _('License successfully deleted.'))
        return super(DeleteLicenseView, self).delete(request, *args, **kwargs)

    def get_success_url(self):
        return "%s#license" % reverse('control_center:settings')


class RoleEditView(BaseCCView, UpdateView):
    model = Role
    context_object_name = 'role'
    form_class = control_forms.AddRoleForm
    page_title = _('Admin Control Center')
    title = page_title
    template_name = "booktypecontrol/control_center_settings.html"

    def get_context_data(self, *args, **kwargs):
        context = super(RoleEditView, self).get_context_data(
            *args, **kwargs)
        context['option'] = 'list-of-roles'
        context['option_name'] = _('Edit role')
        return context

    def get_success_url(self):
        messages.success(self.request, _('Role successfully updated.'))
        return "%s#list-of-roles" % reverse('control_center:settings')


class DeleteRoleView(BaseCCView, DeleteView):
    model = Role
    context_object_name = 'role'
    template_name = 'booktypecontrol/_control_center_modal_delete_role.html'

    def get_success_url(self):
        messages.success(self.request, _('Role successfully deleted.'))
        return "%s#list-of-roles" % reverse('control_center:settings')


class BookSkeletonEditView(BaseCCView, UpdateView):
    model = BookSkeleton
    context_object_name = 'skeleton'
    form_class = control_forms.ListOfSkeletonsForm
    page_title = _('Admin Control Center')
    title = page_title
    template_name = "booktypecontrol/_control_center_book_skeleton_edit.html"

    def get_context_data(self, *args, **kwargs):
        context = super(BookSkeletonEditView, self).get_context_data(
            *args, **kwargs)
        context['option'] = 'book-skeleton'
        context['option_name'] = _('Edit Book Skeleton')
        return context

    def get_success_url(self):
        messages.success(self.request, _('Book Skeleton successfully updated'))
        return "%s#list-of-skeletons" % reverse('control_center:settings')


class DeleteBookSkeletonView(BaseCCView, DeleteView):
    model = BookSkeleton
    context_object_name = 'skeleton'
    template_name = 'booktypecontrol/_control_center_modal_delete_book_skeleton.html'

    def get_success_url(self):
        messages.success(self.request, _('Book Skeleton successfully deleted'))
        return "%s#list-of-skeletons" % reverse('control_center:settings')


class StatisticsView(BaseCCView, TemplateView):
    template_name = 'booktypecontrol/control_center_statistics.html'
    page_title = _('Statistics and instance data')
    title = page_title

    def get_context_data(self, **kwargs):
        context = super(StatisticsView, self).get_context_data(**kwargs)

        statistics = {}
        today = date.today()
        month_ago = today - timedelta(days=30)
        year_ago = today.replace(year=today.year - 1)
        begin_year = User.objects.all().order_by('date_joined')[0].date_joined.year
        current_year = User.objects.all().order_by('-date_joined')[0].date_joined.year
        all_users_count = User.objects.filter(is_active=True, is_superuser=False).count()

        # users increasing
        statistics['users_increasing'] = {
            'labels': [],
            'data': []
        }
        users_count = 0

        for year in range(begin_year, current_year + 1):
            statistics['users_increasing']['labels'].append(year)
            users_count += User.objects.filter(date_joined__year=year).count()
            statistics['users_increasing']['data'].append(users_count)

        # signups per year
        statistics['signups'] = {
            'labels': [],
            'data': []
        }
        for year in range(begin_year, current_year + 1):
            statistics['signups']['labels'].append(year)
            statistics['signups']['data'].append(User.objects.filter(date_joined__year=year).count())

        # last year login
        statistics['last_year_login'] = {}
        active_during_last_year = User.objects.filter(
            is_active=True, is_superuser=False, last_login__gte=year_ago, last_login__lte=today
        ).count()

        statistics['last_year_login']['labels'] = ["Login", "Not login"]
        statistics['last_year_login']['data'] = [active_during_last_year, all_users_count - active_during_last_year]

        # last month login
        statistics['last_month_login'] = {}
        active_during_last_month = User.objects.filter(
            is_active=True, is_superuser=False, last_login__gte=month_ago, last_login__lte=today
        ).count()
        statistics['last_month_login']['labels'] = ["Login", "Not login"]
        statistics['last_month_login']['data'] = [active_during_last_month, all_users_count - active_during_last_month]

        # count of books per active/not active users
        statistics['active_users_books_count'] = {
            'labels': [],
            'data': []
        }
        statistics['not_active_users_books_count'] = {
            'labels': [],
            'data': []
        }
        _active = {}
        _not_active = {}

        for limit in range(0, 10):
            _active[limit] = 0
            _not_active[limit] = 0

        # books per year
        statistics['books_per_year'] = {
            'labels': [],
            'data': []
        }
        for year in range(begin_year, current_year + 1):
            statistics['books_per_year']['labels'].append(year)
            statistics['books_per_year']['data'].append(Book.objects.filter(created__year=year).count())

        # books increasing per year
        statistics['books_increasing_per_year'] = {
            'labels': [],
            'data': []
        }
        books_count = 0
        for year in range(begin_year, current_year + 1):
            statistics['books_increasing_per_year']['labels'].append(year)
            books_count += Book.objects.filter(created__year=year).count()
            statistics['books_increasing_per_year']['data'].append(books_count)

        # not active users
        not_active_during_last_year = User.objects.filter(
            is_active=True, is_superuser=False, last_login__lte=year_ago
        )
        _stats = not_active_during_last_year.annotate(count_of_books=Count('book')).values_list('count_of_books')
        for _count in [i[0] for i in _stats]:
            try:
                _not_active[_count] += 1
            except KeyError:
                _not_active[_count] = 1

        for k, v in _not_active.items():
            statistics['not_active_users_books_count']['labels'].append('{} book(s)'.format(k))
            statistics['not_active_users_books_count']['data'].append(v)

        # active users
        active_during_last_year = User.objects.filter(
            is_active=True, is_superuser=False, last_login__gte=year_ago, last_login__lte=today
        )

        _stats = active_during_last_year.annotate(count_of_books=Count('book')).values_list('count_of_books')

        for _count in [i[0] for i in _stats]:
            try:
                _active[_count] += 1
            except KeyError:
                _active[_count] = 1

        for k, v in _active.items():
            statistics['active_users_books_count']['labels'].append('{} book(s)'.format(k))
            statistics['active_users_books_count']['data'].append(v)

        # exports per year
        statistics['exports_per_year'] = {
            'labels': [],
            'data': []
        }
        for year in range(begin_year, current_year + 1):
            statistics['exports_per_year']['labels'].append(year)
            statistics['exports_per_year']['data'].append(BookExport.objects.filter(created__year=year).count())

        # export formats
        statistics['exports_per_format'] = {
            'labels': [],
            'data': []
        }

        for _data in ExportFile.objects.all().values('typeof').annotate(total=Count('typeof')).order_by('typeof'):
            statistics['exports_per_format']['labels'].append(_data['typeof'])
            statistics['exports_per_format']['data'].append(_data['total'])

        context['statistics'] = json.dumps(statistics)

        return context
