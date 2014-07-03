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
import forms as forms_module

from collections import Counter

from django import forms
from django.conf import settings
from django.db import connection
from django.contrib import messages
from django.template import RequestContext
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import user_passes_test

from django.views.generic.detail import SingleObjectMixin
from django.views.generic import TemplateView, FormView, DetailView, UpdateView

from braces.views import LoginRequiredMixin, SuperuserRequiredMixin

from booktype.utils import misc
from booki.editor import models
from booki.editor.models import Book, BookiGroup, BookHistory

from booktype.apps.core import views
from booktype.apps.core.views import BasePageView

# TODO: to be removed
from .forms import *


# What tabs do you want to have visible at the moment
#ADMIN_OPTIONS = ["dashboard", "people", "books", "filebrowse", "templates", "activity", "messages", "settings"]
ADMIN_OPTIONS = ["dashboard", "people", "books", "settings"]

class BaseCCView(LoginRequiredMixin, SuperuserRequiredMixin, BasePageView):
    pass

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


OPTION_NAMES = {
    'site-description' : _('Description'),
    'appearance'       : _('Appearance'),
    'frontpage'        : _('Frontpage'),
    'license'          : _('Licenses'),
    'book-settings'    : _('Default Book Settings for Creating Books'),
    'privacy'          : _('Privacy'),
    'add-person'       : _('Add a new Person'),
    'list-of-people'   : _('List of People'),
    'add-book'         : _('Add new Book'),
    'list-of-books'    : _('List of Books')
}

VALID_OPTIONS = OPTION_NAMES.keys()

class ControlCenterSettings(BaseCCView, FormView):
    """
    Generic class for control center settings
    """

    template_name = 'booktypecontrol/control_center_settings.html'
    submodule = 'site-description'
    success_url = '/_control/settings/' # TODO: change this url later
    page_title = _('Admin Control Center')
    title = page_title

    def camelize(self, text):
        return ''.join([s for s in text.title() if s.isalpha()])

    def form_valid(self, form):
        try:
            form.save_settings()
            messages.success(self.request, form.success_message or _('Successfully saved settings.'))
        except:
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
        self.form_class = getattr(forms_module, class_text)
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
        context['valid_options'] = VALID_OPTIONS

        extra_context = self.form_class.extra_context()
        if extra_context:
            context.update(extra_context)

        return context

class PersonInfoView(BaseCCView, DetailView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'current_user'

    template_name = "booktypecontrol/_control_center_modal_person_info.html"

class EditPersonInfo(BaseCCView, UpdateView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'current_user'
    form_class = EditPersonInfoForm
    success_url = '/_control/settings/' # TODO: change this url later
    page_title = _('Admin Control Center')
    title = page_title

    template_name = "booktypecontrol/control_center_settings.html"

    def get_context_data(self, *args, **kwargs):
        context = super(EditPersonInfo, self).get_context_data(*args, **kwargs)
        context['option'] = None
        context['option_name'] = _('Edit Person Info')
        context['valid_options'] = VALID_OPTIONS
        return context

    def form_valid(self, form):
        self.object = form.save()
        self.object.get_profile().description = form.cleaned_data['description']
        self.object.get_profile().save()

        if form.files.has_key('profile'):
            misc.set_profile_image(self.object, form.files['profile'])

        messages.success(self.request, _('Successfully saved changes.'))

        return HttpResponseRedirect(self.get_success_url())

    def get_initial(self):
        initial_dict = super(EditPersonInfo, self).get_initial()
        initial_dict['description'] = self.object.get_profile().description

        return initial_dict

class BookRenameView(EditPersonInfo):
    model = Book
    slug_field = 'url_title'
    slug_url_kwarg = 'bookid'
    form_class = BookRenameForm
    template_name = "booktypecontrol/control_center_settings.html"

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_initial(self):
        return {}

class PasswordChangeView(BaseCCView, FormView, SingleObjectMixin):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'current_user'
    success_url = '/_control/settings/' # TODO: change this url later
    page_title = _('Admin Control Center')
    title = page_title
    form_class = PasswordForm

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
        context['valid_options'] = VALID_OPTIONS
        return context


@user_passes_test(lambda u: u.is_superuser)
def settings_book_create(request):
    if request.method == 'POST': 
        frm = BookCreateForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 
            from booktype.utils import config

            config.set_configuration('CREATE_BOOK_VISIBLE', frm.cleaned_data['visible'])

            if frm.cleaned_data['license']:
                config.set_configuration('CREATE_BOOK_LICENSE', frm.cleaned_data['license'].abbrevation)
            else:
                config.set_configuration('CREATE_BOOK_LICENSE', '')

            try:
                config.save_configuration()
                messages.success(request, _('Successfuly saved settings.'))
            except config.ConfigurationError:
                messages.warning(request, _('Unknown error while saving changes.'))

            return HttpResponseRedirect(reverse('control_settings'))             
    else:
        from booktype.utils import config

        _l = config.get_configuration('CREATE_BOOK_LICENSE')
        if _l and _l != '':
            try:
                license = models.License.objects.get(abbrevation = _l)
            except models.License.DoesNotExist:
                license = None
        else:
            license = None
            
        frm = BookCreateForm(initial={'visible': config.get_configuration('CREATE_BOOK_VISIBLE'),
                                      'license': license})

    return render_to_response('booktypecontrol/settings_book_create.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm                               
                               },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def settings_license_edit(request, licenseid):

    books = []

    if request.method == 'POST': 
        frm = LicenseForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_settings_license')) 

        if request.POST['submit'] == _('Remove it'):
            # this could delete all books with this license
            try:
                license = models.License.objects.get(pk=licenseid)
            except models.License.DoesNotExist:
                return views.ErrorPage(request, "errors/license_does_not_exist.html", {"username": ''})

            license.delete()

            messages.success(request, _('Successfuly removed license.'))

            return HttpResponseRedirect(reverse('control_settings_license')) 

        if frm.is_valid(): 
            try:
                license = models.License.objects.get(pk=licenseid)
            except models.License.DoesNotExist:
                return views.ErrorPage(request, "errors/license_does_not_exist.html", {"username": ''})

            license.abbrevation = frm.cleaned_data['abbrevation']
            license.name = frm.cleaned_data['name']
            license.save()

            messages.success(request, _('Successfuly saved changes.'))

            return HttpResponseRedirect(reverse('control_settings_license'))             
    else:
        try:
            license = models.License.objects.get(pk=licenseid)
        except models.License.DoesNotExist:
            # change this
            return views.ErrorPage(request, "errors/license_does_not_exist.html", {"username": ''})

        books = models.Book.objects.filter(license=license).order_by("title")
            
        frm = LicenseForm(initial = {'abbrevation': license.abbrevation,
                                     'name': license.name})

    return render_to_response('booktypecontrol/settings_license_edit.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm,
                               "licenseid": licenseid,
                               "license": license,
                               "books": books
                               },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def settings_privacy(request):
    from booktype.utils import config

    if request.method == 'POST': 
        frm = PrivacyForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 

            config.set_configuration('FREE_REGISTRATION', frm.cleaned_data['user_register'])
            config.set_configuration('ADMIN_CREATE_BOOKS', frm.cleaned_data['create_books'])
            config.set_configuration('ADMIN_IMPORT_BOOKS', frm.cleaned_data['import_books'])

            try:
                config.save_configuration()
                messages.success(request, _('Successfuly saved changes.'))
            except config.ConfigurationError:
                messages.warning(request, _('Unknown error while saving changes.'))

            return HttpResponseRedirect(reverse('control_settings'))             
    else:
        frm = PrivacyForm(initial = {'user_register': config.get_configuration('FREE_REGISTRATION'),
                                     'create_books': config.get_configuration('ADMIN_CREATE_BOOKS'),
                                     'import_books': config.get_configuration('ADMIN_IMPORT_BOOKS')
                                     })

    return render_to_response('booktypecontrol/settings_privacy.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm
                               })



class PublishingForm(forms.Form):
    publish_book = forms.BooleanField(label=_('book'), 
                                      required=False)
    publish_ebook = forms.BooleanField(label=_('ebook'), 
                                       required=False)
    publish_pdf = forms.BooleanField(label=_('PDF'), 
                                     required=False)
    publish_odt = forms.BooleanField(label=_('ODT'), 
                                     required=False)

    def __unicode__(self):
        return u'Publishing'


@user_passes_test(lambda u: u.is_superuser)
def settings_publishing(request):
    from booktype.utils import config
    
    publishOptions = config.get_configuration('PUBLISH_OPTIONS')

    if request.method == 'POST': 
        frm = PublishingForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 
            opts = []
            # a bit silly way to create a list

            if frm.cleaned_data['publish_book']: opts.append('book')
            if frm.cleaned_data['publish_ebook']: opts.append('ebook')
            if frm.cleaned_data['publish_pdf']: opts.append('pdf')
            if frm.cleaned_data['publish_odt']: opts.append('odt')

            config.set_configuration('PUBLISH_OPTIONS', opts)

            try:
                config.save_configuration()
                messages.success(request, _('Successfuly saved changes.'))
            except config.ConfigurationError:
                messages.warning(request, _('Unknown error while saving changes.'))
                
            return HttpResponseRedirect(reverse('control_settings'))             
    else:
        frm = PublishingForm(initial = {'publish_book': 'book' in publishOptions,
                                        'publish_ebook': 'ebook' in publishOptions,
                                        'publish_pdf': 'pdf' in publishOptions,
                                        'publish_odt': 'odt' in publishOptions})


    return render_to_response('booktypecontrol/settings_publishing.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm
                               })


@user_passes_test(lambda u: u.is_superuser)
def settings_appearance(request):
    staticRoot = settings.STATIC_ROOT

    if request.method == 'POST': 
        frm = AppearanceForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 
            try:
                # should really save it in a safe way
                f = open('%s/css/_user.css' % staticRoot, 'w')
                f.write(frm.cleaned_data['css'].encode('utf8'))
                f.close()

                messages.success(request, _('Successfuly saved changes.'))
            except IOError:
                messages.warning(request, _('Unknown error while saving changes.'))

            return HttpResponseRedirect(reverse('control_settings'))             
    else:
        try:
            f = open('%s/css/_user.css' % staticRoot, 'r')
            cssContent = unicode(f.read(), 'utf8')
            f.close()
        except IOError:
            cssContent = ''

        frm = AppearanceForm(initial = {'css': cssContent})


    return render_to_response('booktypecontrol/settings_appearance.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm
                               })


class PublishingDefaultsForm(forms.Form):
    book_css = forms.CharField(label=_('Book CSS'), 
                          required=False, 
                          widget=forms.Textarea(attrs={'rows': 30}))
    ebook_css = forms.CharField(label=_('E-Book CSS'), 
                          required=False, 
                          widget=forms.Textarea(attrs={'rows': 30}))
    pdf_css = forms.CharField(label=_('PDF CSS'), 
                          required=False, 
                          widget=forms.Textarea(attrs={'rows': 30}))
    odt_css = forms.CharField(label=_('ODT CSS'), 
                          required=False, 
                          widget=forms.Textarea(attrs={'rows': 30}))

    def __unicode__(self):
        return u'Default settings'


@user_passes_test(lambda u: u.is_superuser)
def settings_publishing_defaults(request):
    from booktype.utils import config

    data = {'book_css':  config.get_configuration('BOOKTYPE_CSS_BOOK', ''),
            'ebook_css': config.get_configuration('BOOKTYPE_CSS_EBOOK', ''),
            'pdf_css':   config.get_configuration('BOOKTYPE_CSS_PDF', ''),
            'odt_css':   config.get_configuration('BOOKTYPE_CSS_ODT', '')}

    if request.method == 'POST': 
        frm = PublishingDefaultsForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 
            if frm.cleaned_data['book_css'] != data['book_css']:
                config.set_configuration('BOOKTYPE_CSS_BOOK', frm.cleaned_data['book_css'])

            if frm.cleaned_data['ebook_css'] != data['ebook_css']:
                config.set_configuration('BOOKTYPE_CSS_EBOOK', frm.cleaned_data['ebook_css'])

            if frm.cleaned_data['pdf_css'] != data['pdf_css']:
                config.set_configuration('BOOKTYPE_CSS_PDF', frm.cleaned_data['pdf_css'])

            if frm.cleaned_data['odt_css'] != data['odt_css']:
                config.set_configuration('BOOKTYPE_CSS_ODT', frm.cleaned_data['odt_css'])

            try:
                config.save_configuration()
                messages.success(request, _('Successfuly saved changes.'))
            except config.ConfigurationError:
                messages.warning(request, _('Unknown error while saving changes.'))

            return HttpResponseRedirect(reverse('control_settings'))             
    else:
        frm = PublishingDefaultsForm(initial = data)


    return render_to_response('booktypecontrol/settings_publishing_defaults.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm
                               })