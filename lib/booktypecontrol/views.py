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

import booki
import sputnik
import forms as control_forms

from collections import Counter

from django.conf import settings
from django.db import connection
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse, reverse_lazy

from django.views.generic.detail import SingleObjectMixin
from django.views.generic import TemplateView, FormView
from django.views.generic import DetailView, UpdateView, DeleteView

from braces.views import LoginRequiredMixin, SuperuserRequiredMixin

from booktype.utils import misc
from booki.editor.models import Book, BookiGroup, BookHistory, License
from booktype.apps.core.views import BasePageView


OPTION_NAMES = {
    'site-description'    : _('Description'),
    'appearance'          : _('Appearance'),
    'frontpage'           : _('Frontpage'),
    'license'             : _('Licenses'),
    'book-settings'       : _('Default Book Settings for Creating Books'),
    'privacy'             : _('Privacy'),
    'add-person'          : _('Add a new Person'),
    'list-of-people'      : _('List of People'),
    'add-book'            : _('Add new Book'),
    'list-of-books'       : _('List of Books'),
    'publishing'          : _('Allowed publishing options'),
    'publishing-defaults' : _('Publishing Defaults'),
    'add-group'           : _('Add new Group'),
    'list-of-groups'      : _('List of Groups')
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
        users = most_active_query.values_list('user', flat=True)
        most_active = Counter(users).most_common()[:5]
        context['most_active_users'] = User.objects.filter(id__in=[id for id, freq in most_active])

        # get latest books
        context['latest_books'] = Book.objects.order_by('-created')[:4]

        # most active books
        books = most_active_query.values_list('book', flat=True)
        most_active_books = Counter(books).most_common()[:4]
        context['most_active_books'] = Book.objects.filter(id__in=[id for id, freq in most_active_books])

        # recent activity
        context['recent_activity'] = BookHistory.objects.filter(kind__in=[1, 10]).order_by('-modified')[:20]

        return context

    def get_stats(self):
        # This should not be here in the future. It takes way too much time.
        attachment_directory = '%s/books/' % (settings.DATA_ROOT, )
        attachments_size = misc.get_directory_size(attachment_directory)

        # check the database size        
        cursor = connection.cursor()

        try:
            # This will not work if user has new style of configuration for the database
            # This will also only work for PostgreSQL. Should make another method for checking sqlite database size.
            cursor.execute("SELECT pg_database_size(%s)", [settings.DATABASES['default']['NAME']]);
            databaseSize = cursor.fetchone()[0]
        except:
            databaseSize = 0

        return {
            'version': '.'.join([str(num) for num in booki.version]),
            'users': User.objects.count(),
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
            messages.success(self.request, form.success_message or _('Successfully saved settings.'))
        except Exception as err:
            print err
            messages.warning(self.request, _('Unknown error while saving changes.'))
        return super(ControlCenterSettings, self).form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        # if redirect param is present, go to right submodule
        redirect = request.REQUEST.get('redirect', None)
        if redirect and redirect in VALID_OPTIONS:
            return HttpResponseRedirect('{0}#{1}'.format(reverse('control_center:settings'), redirect))

        option = request.REQUEST.get('option', None)
        if option and option in VALID_OPTIONS:
            self.submodule = option
        return super(ControlCenterSettings, self).dispatch(request, *args, **kwargs)

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
                "booktypecontrol/_control_center_%s.html" % self.submodule.replace('-', '_'), 
                "booktypecontrol/_control_center_settings.html"
            ]
        return super(ControlCenterSettings, self).get_template_names()

    def get_context_data(self, *args, **kwargs):
        context = super(ControlCenterSettings, self).get_context_data(*args, **kwargs)
        context['option'] = self.submodule
        context['option_name'] = OPTION_NAMES.get(self.submodule, '')

        extra_context = self.form_class.extra_context()
        if extra_context:
            context.update(extra_context)
        return context

    def get_success_url(self):
        # if form class has custom success url
        if self.form_class.success_url:
            success_url = self.form_class.success_url
            if "#" in success_url:
                success_url = "{0}{1}".format(self.success_url, success_url)
            return success_url
        return super(ControlCenterSettings, self).get_success_url()

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
        context['activity'] = BookHistory.objects.filter(user=person, kind__in=[1, 10]).order_by('-modified')[:20]
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
        profile = self.object.get_profile()
        profile.description = form.cleaned_data['description']
        profile.save()

        if form.files.has_key('profile'):
            misc.set_profile_image(self.object, form.files['profile'])
        else:
            if form.data.get('profile_remove', False):
                profile.remove_image()

        messages.success(self.request, _('Successfully saved changes.'))

        return HttpResponseRedirect(self.get_success_url())

    def get_initial(self):
        initial_dict = super(EditPersonInfo, self).get_initial()
        profile = self.object.get_profile()
        initial_dict['description'] = profile.description
        if profile.image:
            initial_dict['profile'] = profile.image.url
        return initial_dict

    def get_success_url(self):
        return "%s#list-of-people" % reverse('control_center:settings')

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
    form_class = control_forms.PasswordForm
    template_name = "booktypecontrol/control_center_settings.html"

    def get_form(self, form_class):
        self.object = self.get_object()
        return form_class(user=self.object, **self.get_form_kwargs())

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _('Successfully saved changes.'))
        return super(FormView, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super(PasswordChangeView, self).get_context_data(*args, **kwargs)
        context['option'] = None
        context['option_name'] = "%s: %s" % (_('Change Password'), self.object.username)
        return context

    def get_success_url(self):
        return "%s#list-of-people" % reverse('control_center:settings')

class DeleteGroupView(BaseCCView, DeleteView):
    model = BookiGroup
    slug_field = 'url_name'
    slug_url_kwarg = 'groupid'
    context_object_name = 'group'
    template_name = 'booktypecontrol/_control_center_modal_delete_group.html'

    def get_success_url(self):
        messages.success(self.request, _('Group successfully deleted.'))
        return "%s#list-of-groups" % reverse('control_center:settings')

class LicenseEditView(BaseCCView, UpdateView):
    model = License
    context_object_name = 'license'
    form_class = control_forms.LicenseForm
    page_title = _('Admin Control Center')
    title = page_title
    template_name = "booktypecontrol/_control_center_license_edit.html"

    def get_context_data(self, *args, **kwargs):
        context = super(LicenseEditView, self).get_context_data(*args, **kwargs)
        context['option'] = 'license'
        context['option_name'] = _('Edit licence')
        context['licensed_books'] = Book.objects.filter(license=self.object).order_by('title')
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
            messages.warning(self.request, _('There are licensed books with this license. Unable to remove'))
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.success(self.request, _('License successfully deleted.'))
        return super(DeleteLicenseView, self).delete(request, *args, **kwargs)

    def get_success_url(self):
        return "%s#license" % reverse('control_center:settings')