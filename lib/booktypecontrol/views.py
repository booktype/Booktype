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

import datetime
import traceback
import booki
import sputnik
import forms as forms_module

from collections import Counter

from django import forms
from django.conf import settings
from django.contrib import messages
from django.template import RequestContext
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.db import IntegrityError, connection
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, FormView
from django.contrib.auth.decorators import user_passes_test
from django.core.validators import RegexValidator, MinLengthValidator

from braces.views import LoginRequiredMixin, SuperuserRequiredMixin

from booki.editor import models
from booktype.apps.core import views
from booki.utils import misc, config
from booki.editor.models import Book, BookiGroup, BookHistory

from booktype.apps.core.views import BasePageView

# TODO: to be removed
from .forms import *


# What tabs do you want to have visible at the moment
#ADMIN_OPTIONS = ["dashboard", "people", "books", "filebrowse", "templates", "activity", "messages", "settings"]
ADMIN_OPTIONS = ["dashboard", "people", "books", "settings"]

@user_passes_test(lambda u: u.is_superuser)
def frontpage(request):

    # check all active online users and what are they doing
    import sputnik

    clientList = sputnik.rkeys("ses:*:username")
    onlineUsers = []

    for us in clientList:
        clientID = us[4:-9]

        channelList = []
        for chan in sputnik.smembers('ses:%s:channels' % clientID):
            if chan.startswith('/booki/book/'):
                _s = chan.split('/')
                if len(_s) > 3:
                    bookID = _s[3]
                    try:
                        b = models.Book.objects.get(pk=bookID)
                        channelList.append(b)
                    except models.Book.DoesNotExist:
                        pass
            
        _u = sputnik.get(us)
        onlineUsers.append((_u, channelList))

    # Check the attachment size.
    # This should not be here in the future. It takes way too much time.
    from booki.utils import misc

    attachmentDirectory = '%s/books/' % (settings.DATA_ROOT, )
    attachmentsSize = misc.getDirectorySize(attachmentDirectory)

    # Number of books and number of groups
    number_of_books = len(models.Book.objects.all())
    number_of_groups = len(models.BookiGroup.objects.all())

    # Number of all users on the system.
    # This should somehow check only the active users
    number_of_users = User.objects.count()

    # check the database size
    from django.db import connection
    cursor = connection.cursor()

    try:
        # This will not work if user has new style of configuration for the database
        # This will also only work for PostgreSQL. Should make another method for checking sqlite database size.
        cursor.execute("SELECT pg_database_size(%s)", [settings.DATABASES['default']['NAME']]);
        databaseSize = cursor.fetchone()[0]
    except:
        databaseSize = 0

    # Book activity
    activityHistory = models.BookHistory.objects.filter(kind__in=[1, 10]).order_by('-modified')[:20]

    # Booktype version
    import booki
    booktypeVersion = '.'.join([str(num) for num in booki.version])

    return render_to_response('booktypecontrol/frontpage.html', 
                              {"request": request,
                               "booktype_version": booktypeVersion,
                               "admin_options": ADMIN_OPTIONS,
                               "online_users": onlineUsers,
                               "attachments_size": attachmentsSize,
                               "number_of_books": number_of_books,
                               "number_of_users": number_of_users,
                               "number_of_groups": number_of_groups,
                               "database_size": databaseSize,
                               "activity_history": activityHistory
                               })

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
        attachments_size = misc.getDirectorySize(attachment_directory)

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
    'privacy'          : _('Privacy')
}

class ControlCenterSettings(BaseCCView, FormView):
    """
    Generic class for control center settings
    """

    VALID_OPTIONS = OPTION_NAMES.keys()
    template_name = 'booktypecontrol/control_center_settings.html'
    submodule = 'site-description'
    success_url = '/_control/new/settings/'
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
        option = request.REQUEST.get('option', None)
        if option and option in self.VALID_OPTIONS:
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
                "booktypecontrol/_control_center_%s.html" % self.submodule, 
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


@user_passes_test(lambda u: u.is_superuser)
def people(request):
    """
    Front page for the people tab. Shows list of all the users.
    """

    from django.contrib.auth.models import User

    people = User.objects.all().order_by("username")

    return render_to_response('booktypecontrol/people.html', 
                              {"request": request,
                               "people": people,
                               "admin_options": ADMIN_OPTIONS                               
                               },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def profile(request, username):
    """
    Shows info about one person.
    """

    from django.contrib.auth.models import User

    try:
        person = User.objects.get(username=username)
    except User.DoesNotExist:
        return views.ErrorPage(request, "errors/user_does_not_exist.html", {"username": username})

    from django.utils.html import escape
    personDescription = escape(person.get_profile().description)

    books = models.Book.objects.filter(owner=person)
    groups = models.BookiGroup.objects.filter(owner=person)

    activityHistory = models.BookHistory.objects.filter(user=person, kind__in=[1, 10]).order_by('-modified')[:20]

    return render_to_response('booktypecontrol/profile.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "person": person,
                               "description": personDescription,
                               "books": books,
                               "groups": groups,
                               "activity_history": activityHistory
                               },
                              context_instance=RequestContext(request))


class ProfileForm(forms.Form):
    username = forms.CharField(label=_('Username'),
                               required=True, 
                               max_length=100, 
                               error_messages={'required': _('Username is required.'),
                                               'ivalid': _("Illegal characters in username.")},
                               validators=[RegexValidator(r"^[\w\d\@\.\+\-\_]+$", message=_("Illegal characters in username.")), MinLengthValidator(3)])
    first_name = forms.CharField(label=_('First name'),
                                 required=True, 
                                 error_messages={'required': _('First name is required.')},                                 
                                 max_length=32)
    email = forms.EmailField(label=_('Email'),
                             required=True,
                             error_messages={'required': _('Email is required.')},                                 
                             max_length=100)
    profile = forms.ImageField(label=_('Profile picture'),
                               required=False)
    description = forms.CharField(label=_("User description"), 
                                  required=False, 
                                  widget=forms.Textarea)

    def __unicode__(self):
        return self.first_name


@user_passes_test(lambda u: u.is_superuser)
def edit_profile(request, username):
    from django.contrib.auth.models import User

    try:
        person = User.objects.get(username=username)
    except User.DoesNotExist:
        return views.ErrorPage(request, "errors/user_does_not_exist.html", {"username": username})

    if request.method == 'POST': 
        frm = ProfileForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_profile', args=[person.username])) 

        if frm.is_valid(): 
            person.username = frm.cleaned_data['username']
            person.email = frm.cleaned_data['email']
            person.first_name = frm.cleaned_data['first_name']
            person.save()

            person.get_profile().description = frm.cleaned_data['description']
            person.get_profile().save()

            if request.FILES.has_key('profile'):
                from booki.utils import misc

                misc.setProfileImage(person, request.FILES['profile'])

            messages.success(request, _('Successfuly saved changes.'))
            return HttpResponseRedirect(reverse('control_profile', args=[person.username])) 
    else:
        frm = ProfileForm({'username': person.username,
                           'first_name': person.first_name,
                           'email': person.email,
                           'description': person.get_profile().description})


    return render_to_response('booktypecontrol/edit_profile.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "person": person,
                               "form": frm
                               },
                              context_instance=RequestContext(request))


class PasswordForm(forms.Form):
    password1 = forms.CharField(label=_('Password'), 
                                required=True, 
                                error_messages={'required': _('Password is required.')},
                                max_length=100, 
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Password confirmation'), 
                                required=True, 
                                max_length=100, 
                                error_messages={'required': _('Password is required.')},
                                widget=forms.PasswordInput, 
                                help_text = _("Enter the same password as above, for verification."))


    def __unicode__(self):
        return self.first_name


@user_passes_test(lambda u: u.is_superuser)
def edit_password(request, username):
    from django.contrib.auth.models import User

    try:
        person = User.objects.get(username=username)
    except User.DoesNotExist:
        return views.ErrorPage(request, "errors/user_does_not_exist.html", {"username": username})

    if request.method == 'POST': 
        frm = PasswordForm(request.POST) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect('../') 

        if frm.is_valid(): 
            if frm.cleaned_data['password1'] == frm.cleaned_data['password2']:
                person.set_password(frm.cleaned_data['password1']) 
                person.save() 

                messages.success(request, _('Successfuly saved changes.'))
                return HttpResponseRedirect(reverse('control_profile', args=[person.username])) 

            messages.warning(request, _('Passwords do not match'))
    else:
        frm = PasswordForm()

    return render_to_response('booktypecontrol/edit_password.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "person": person,
                               "form": frm
                               },
                              context_instance=RequestContext(request))


class NewPersonForm(forms.Form):
    username = forms.CharField(label=_('Username'),
                               required=True, 
                               error_messages={'required': _('Username is required.'),
                                               'ivalid': _("Illegal characters in username.")},
                               max_length=100, 
                               validators=[RegexValidator(r"^[\w\d\@\.\+\-\_]+$", message=_("Illegal characters in username.")), MinLengthValidator(3)])
    first_name = forms.CharField(label=_('First name'),
                                 required=True, 
                                 error_messages={'required': _('First name is required.')},                                 
                                 max_length=32)
    email = forms.EmailField(label=_('Email'),
                             required=True,
                             error_messages={'required': _('Email is required.')},                                 
                             max_length=100)
    description = forms.CharField(label=_("User description"), 
                                  required=False, 
                                  widget=forms.Textarea)
    password1 = forms.CharField(label=_('Password'), 
                                required=True, 
                                error_messages={'required': _('Password is required.')},
                                max_length=100, 
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Password confirmation'), 
                                required=True, 
                                error_messages={'required': _('Password is required.')},
                                max_length=100, 
                                widget=forms.PasswordInput, 
                                help_text = _("Enter the same password as above, for verification."))
    send_email = forms.BooleanField(label=_('Notify person by email'), 
                                    required=False)

    def clean_username(self):
        from django.contrib.auth.models import User

        try:
            usr = User.objects.get(username=self.cleaned_data['username'])
        except User.DoesNotExist:
            pass
        else:
            raise forms.ValidationError(_("This Person already exists."))

        return self.cleaned_data['username']

    def clean_password2(self):
        if self.cleaned_data['password2'] != self.cleaned_data['password1']:
            raise forms.ValidationError(_("Passwords do not match."))

        return self.cleaned_data['password2']

    def __unicode__(self):
        return self.username


@user_passes_test(lambda u: u.is_superuser)
def add_person(request):
    from django.contrib.auth.models import User

    if request.method == 'POST': 
        frm = NewPersonForm(request.POST) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_people')) 

        if frm.is_valid(): 
            from django.contrib import auth
            try:
                user = auth.models.User.objects.create_user(username=frm.cleaned_data['username'],
                                                            email=frm.cleaned_data['email'],
                                                            password=frm.cleaned_data['password2'])
                user.first_name = frm.cleaned_data['first_name']
                user.save()

                user.get_profile().description = frm.cleaned_data['description']
                user.get_profile().save()

                if frm.cleaned_data["send_email"]:
                    from django import template

                    t = template.loader.get_template('booktypecontrol/new_person_email.html')
                    content = t.render(template.Context({"username": frm.cleaned_data['username'],
                                                         "password": frm.cleaned_data['password2'],
                                                         "server":   settings.BOOKTYPE_URL}))

                    from django.core.mail import EmailMultiAlternatives
                    emails = [frm.cleaned_data['email']]

                    msg = EmailMultiAlternatives('You have a new Booktype Account ', content, settings.REPORT_EMAIL_USER, emails)
                    msg.attach_alternative(content, "text/html")
                    msg.send(fail_silently=True)

                messages.success(request, 'Successfuly created new account.')

                return HttpResponseRedirect(reverse('control_people')) 
            except IntegrityError:
                messages.warning(request, _('Unknown error while creating new account.'))
                
    else:
        frm = NewPersonForm()

    return render_to_response('booktypecontrol/add_person.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm
                               },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def books(request):
    books = models.Book.objects.all().order_by("title")

    return render_to_response('booktypecontrol/books.html', 
                              {"request": request,
                               "books": books,
                               "admin_options": ADMIN_OPTIONS
                               },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def view_book(request, bookid):
    from booki.utils import misc

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = book.get_version(None)

    # this only shows info for latest version
    book_history =  models.BookHistory.objects.filter(version = book_version).order_by("-modified")[:20]
    book_collaborators =  [e.values()[0] for e in models.BookHistory.objects.filter(version = book_version, kind = 2).values("user__username").distinct()]

    from booki.utils import security
    bookSecurity = security.getUserSecurityForBook(request.user, book)
    isBookAdmin = bookSecurity.isAdmin()

    import sputnik
    channel_name = "/booki/book/%s/%s/" % (book.id, book_version.get_version())
    online_users = sputnik.smembers("sputnik:channel:%s:users" % channel_name)

    book_versions = models.BookVersion.objects.filter(book=book).order_by("created")

    from django.utils.html import escape
    bookDescription = escape(book.description)

    attachmentDirectory = '%s/books/%s' % (settings.DATA_ROOT, book.url_title)
    attachmentsSize = misc.getDirectorySize(attachmentDirectory)


    return render_to_response('booktypecontrol/book.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "book": book,
                               "book_version": book_version.get_version(),
                               "book_versions": book_versions,
                               "book_history": book_history, 
                               "book_collaborators": book_collaborators,
                               "is_book_admin": isBookAdmin,
                               "online_users": online_users,
                               "book_description": '<br/>'.join(bookDescription.replace('\r','').split('\n')),
                               "attachments_size": attachmentsSize
                               },
                              context_instance=RequestContext(request)
                              )


from django.contrib.auth.models import User

class DeleteBookForm(forms.Form):
    title = forms.CharField(label=_("Title"), 
                            error_messages={'required': _('Title is required.')},                                 
                            required=True, 
                            max_length=100)
    def __unicode__(self):
        return self.title


@user_passes_test(lambda u: u.is_superuser)
def delete_book(request, bookid):
    from booki.utils import misc

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})


    if request.method == 'POST': 
        frm = DeleteBookForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_book', args=[book.url_title]))

        if frm.is_valid(): 
            try:
                if frm.cleaned_data['title'].upper() == book.title.upper():
                    from booki.utils.book import removeBook

                    removeBook(book)

                    messages.success(request, _('Successfuly deleted the book'))

                    return HttpResponseRedirect(reverse('control_books')) 
                else:
                    messages.warning(request, _('Wrong title.'))
            except:
                messages.warning(request, _('Unknown error while deleting the book'))

    else:
        frm = DeleteBookForm()

    return render_to_response('booktypecontrol/delete_book.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm,
                               "book": book
                               },
                              context_instance=RequestContext(request))


from django.contrib.auth.models import User

class NewBookForm(forms.Form):
    title = forms.CharField(label=_("Title"), 
                            error_messages={'required': _('Title is required.')},                                 
                            required=True, 
                            max_length=100)
    description = forms.CharField(label=_('Description'),
                                  required=False, 
                                  widget=forms.Textarea)
    owner = forms.ModelChoiceField(label=_('Owner'),
                                   error_messages={'required': _('Book owner is required.')},                                 
                                   queryset=User.objects.all().order_by("username"), 
                                   required=True)
    license = forms.ModelChoiceField(label=_('License'),
                                     queryset=models.License.objects.all().order_by("name"), 
                                     error_messages={'required': _('License is required.')},                                 
                                     required=True)
    is_hidden = forms.BooleanField(label=_('Initially hide from others'), 
                                   required=False)
    cover = forms.ImageField(label=_('Cover image'),
                             required=False)

    def clean_title(self):
        from booki.utils.book import checkBookAvailability

        if not checkBookAvailability(self.cleaned_data['title']):
            raise forms.ValidationError(_("This Book already exists."))

        return self.cleaned_data['title']


    def __unicode__(self):
        return self.username


@user_passes_test(lambda u: u.is_superuser)
def add_book(request):
    from booki.utils.book import createBook

    if request.method == 'POST': 
        frm = NewBookForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_books')) 

        if frm.is_valid(): 
            try:
                book = createBook(frm.cleaned_data['owner'], frm.cleaned_data['title'])
                book.license = frm.cleaned_data['license']
                book.description = frm.cleaned_data['description']
                book.is_hidden = frm.cleaned_data['is_hidden']
                book.save()

                if request.FILES.has_key('cover'):
                    from booki.utils import misc
                    import os

                    try:
                        fh, fname = misc.saveUploadedAsFile(request.FILES['cover'])

                        book.set_cover(fname)
                        os.unlink(fname)
                    except:
                        pass
                    
                book.save()

                messages.success(request, _('Successfuly created new book.'))

                return HttpResponseRedirect(reverse('control_books')) 
            except:
                messages.warning(request, _('Unknown error while creating new book.'))

    else:
        frm = NewBookForm()

    return render_to_response('booktypecontrol/add_book.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm
                               },
                              context_instance=RequestContext(request))


class BookForm(forms.Form):
    description = forms.CharField(label=_('Description'),
                                  required=False, 
                                  widget=forms.Textarea)
    owner = forms.ModelChoiceField(label=_('Owner'),
                                   error_messages={'required': _('Owner is required.')},                                 
                                   queryset=User.objects.all().order_by("username"), 
                                   required=True)
    license = forms.ModelChoiceField(label=_('License'),
                                     error_messages={'required': _('License is required.')},                                 
                                     queryset=models.License.objects.all().order_by("name"), 
                                     required=True)
    is_hidden = forms.BooleanField(label=_('Initially hide from others'), 
                                   required=False)
    cover = forms.ImageField(label=_('Cover image'),
                             required=False)

    def clean_title(self):
        from booki.utils.book import checkBookAvailability

        if not checkBookAvailability(self.cleaned_data['title']):
            raise forms.ValidationError(_("This Book already exists."))

        return self.cleaned_data['title']


    def __unicode__(self):
        return self.username


@user_passes_test(lambda u: u.is_superuser)
def edit_book(request, bookid):

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = book.get_version(None)

    if request.method == 'POST': 
        frm = BookForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_book', args=[book.url_title])) 

        if frm.is_valid(): 
            try:
                book.license = frm.cleaned_data['license']
                book.description = frm.cleaned_data['description']
                book.hidden = frm.cleaned_data['is_hidden']
                book.save()

                if request.FILES.has_key('cover'):
                    from booki.utils import misc
                    import os

                    try:
                        fh, fname = misc.saveUploadedAsFile(request.FILES['cover'])
                        book.set_cover(fname)
                        os.unlink(fname)
                    except:
                        pass
                    
                book.save()

                messages.success(request, _('Successfuly saved changes.'))

                return HttpResponseRedirect(reverse('control_book', args=[book.url_title])) 
            except:
                messages.warning(request, _('Unknown error while saving changes.'))

    else:
        data = {'description': book.description,
                'cover': book.cover}

        if book.owner:
            data['owner'] = book.owner.id
        if book.license:
            data['license'] = book.license.id
        if book.hidden:
            data['is_hidden'] = True
        
        frm = BookForm(initial=data)

    return render_to_response('booktypecontrol/edit_book.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm,
                               "book": book
                               },
                              context_instance=RequestContext(request))


class BookRenameForm(forms.Form):
    title = forms.CharField(label=_("Title"), 
                            required=True, 
                            error_messages={'required': _('Title is required.')},                                 
                            max_length=200)
    url_title = forms.CharField(label=_("URL title"), 
                                required=False, 
                                max_length=200, 
                                validators=[RegexValidator(r"^[\w\s\_\.\-\d]+$", message=_("Illegal characters in URL title."))],
                                help_text=_("If you leave this field empty URL title will be assigned automatically."))

    def __unicode__(self):
        return self.username


@user_passes_test(lambda u: u.is_superuser)
def rename_book(request, bookid):

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = book.get_version(None)

    if request.method == 'POST': 
        frm = BookRenameForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_book', args=[book.url_title]))

        if frm.is_valid(): 
            from booki.utils.book import renameBook
            from booki.utils.misc import bookiSlugify

            title =  frm.cleaned_data['title']
            URLTitle = frm.cleaned_data['url_title']

            if URLTitle.strip() == '':
                URLTitle = bookiSlugify(title)

            # this is not the nice way to solve this
            if book.url_title != URLTitle:
                try:
                    b = models.Book.objects.get(url_title__iexact=URLTitle)
                except models.Book.DoesNotExist:
                    renameBook(book, title, URLTitle)
                    book.save()

                    messages.success(request, _('Successfuly renamed book.'))

                    return HttpResponseRedirect(reverse('control_book', args=[book.url_title]))
            else:
                    renameBook(book, title, URLTitle)
                    book.save()

                    messages.success(request, _('Successfuly renamed book.'))

                    return HttpResponseRedirect(reverse('control_book', args=[book.url_title]))


    else:
        frm = BookRenameForm(initial={'title': book.title, 'url_title': book.url_title})

    return render_to_response('booktypecontrol/rename_book.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm,
                               "book": book
                               },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def viewsettings(request):
    return render_to_response('booktypecontrol/settings.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS                               
                               },
                              context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser)
def settings_description(request):
    if request.method == 'POST': 
        frm = SiteDescriptionForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 
            from booki.utils import config

            config.setConfiguration('BOOKTYPE_SITE_NAME', frm.cleaned_data['title'])
            config.setConfiguration('BOOKTYPE_SITE_TAGLINE', frm.cleaned_data['tagline'])

            if request.FILES.has_key('favicon'):
                from booki.utils import misc
                import shutil

                # just check for any kind of silly error
                try:
                    fh, fname = misc.saveUploadedAsFile(request.FILES['favicon'])
                    shutil.move(fname, '%s/favicon.ico' % settings.STATIC_ROOT)

                    config.setConfiguration('BOOKTYPE_SITE_FAVICON', '%s/static/favicon.ico' % settings.BOOKTYPE_URL)
                except:
                    pass

            try:
                config.saveConfiguration()
                messages.success(request, _('Successfuly saved settings.'))
            except config.ConfigurationError:
                messages.warning(request, _('Unknown error while saving changes.'))

            return HttpResponseRedirect(reverse('control_settings'))             
    else:
        frm = SiteDescriptionForm(initial={'title': config.getConfiguration('BOOKTYPE_SITE_NAME'),
                                           'tagline': config.getConfiguration('BOOKTYPE_SITE_TAGLINE')})


    return render_to_response('booktypecontrol/settings_description.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm                               
                               },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def settings_book_create(request):
    if request.method == 'POST': 
        frm = BookCreateForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 
            from booki.utils import config

            config.setConfiguration('CREATE_BOOK_VISIBLE', frm.cleaned_data['visible'])

            if frm.cleaned_data['license']:
                config.setConfiguration('CREATE_BOOK_LICENSE', frm.cleaned_data['license'].abbrevation)
            else:
                config.setConfiguration('CREATE_BOOK_LICENSE', '')

            try:
                config.saveConfiguration()
                messages.success(request, _('Successfuly saved settings.'))
            except config.ConfigurationError:
                messages.warning(request, _('Unknown error while saving changes.'))

            return HttpResponseRedirect(reverse('control_settings'))             
    else:
        from booki.utils import config

        _l = config.getConfiguration('CREATE_BOOK_LICENSE')
        if _l and _l != '':
            try:
                license = models.License.objects.get(abbrevation = _l)
            except models.License.DoesNotExist:
                license = None
        else:
            license = None
            
        frm = BookCreateForm(initial={'visible': config.getConfiguration('CREATE_BOOK_VISIBLE'),
                                      'license': license})

    return render_to_response('booktypecontrol/settings_book_create.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm                               
                               },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def settings_license(request):
    if request.method == 'POST': 
        frm = LicenseForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 
            from booki.utils import config

            license = models.License(abbrevation = frm.cleaned_data['abbrevation'],
                                     name = frm.cleaned_data['name'])
            license.save()

            messages.success(request, _('Successfuly created new license.'))

            return HttpResponseRedirect(reverse('control_settings_license'))             
    else:
        frm = LicenseForm()

    licenses = models.License.objects.all().order_by("name")

    return render_to_response('booktypecontrol/settings_license.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm,
                               "licenses": licenses
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
    from booki.utils import config

    if request.method == 'POST': 
        frm = PrivacyForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 

            config.setConfiguration('FREE_REGISTRATION', frm.cleaned_data['user_register'])
            config.setConfiguration('ADMIN_CREATE_BOOKS', frm.cleaned_data['create_books'])
            config.setConfiguration('ADMIN_IMPORT_BOOKS', frm.cleaned_data['import_books'])

            try:
                config.saveConfiguration()
                messages.success(request, _('Successfuly saved changes.'))
            except config.ConfigurationError:
                messages.warning(request, _('Unknown error while saving changes.'))

            return HttpResponseRedirect(reverse('control_settings'))             
    else:
        frm = PrivacyForm(initial = {'user_register': config.getConfiguration('FREE_REGISTRATION'),
                                     'create_books': config.getConfiguration('ADMIN_CREATE_BOOKS'),
                                     'import_books': config.getConfiguration('ADMIN_IMPORT_BOOKS')
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
    from booki.utils import config
    
    publishOptions = config.getConfiguration('PUBLISH_OPTIONS')

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

            config.setConfiguration('PUBLISH_OPTIONS', opts)

            try:
                config.saveConfiguration()
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
    from booki.utils import config

    data = {'book_css':  config.getConfiguration('BOOKTYPE_CSS_BOOK', ''),
            'ebook_css': config.getConfiguration('BOOKTYPE_CSS_EBOOK', ''),
            'pdf_css':   config.getConfiguration('BOOKTYPE_CSS_PDF', ''),
            'odt_css':   config.getConfiguration('BOOKTYPE_CSS_ODT', '')}

    if request.method == 'POST': 
        frm = PublishingDefaultsForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 
            if frm.cleaned_data['book_css'] != data['book_css']:
                config.setConfiguration('BOOKTYPE_CSS_BOOK', frm.cleaned_data['book_css'])

            if frm.cleaned_data['ebook_css'] != data['ebook_css']:
                config.setConfiguration('BOOKTYPE_CSS_EBOOK', frm.cleaned_data['ebook_css'])

            if frm.cleaned_data['pdf_css'] != data['pdf_css']:
                config.setConfiguration('BOOKTYPE_CSS_PDF', frm.cleaned_data['pdf_css'])

            if frm.cleaned_data['odt_css'] != data['odt_css']:
                config.setConfiguration('BOOKTYPE_CSS_ODT', frm.cleaned_data['odt_css'])

            try:
                config.saveConfiguration()
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


@user_passes_test(lambda u: u.is_superuser)
def settings_frontpage(request):
    from booki.utils import config


    staticRoot = settings.BOOKTYPE_ROOT

    if request.method == 'POST': 
        frm = FrontpageForm(request.POST, request.FILES) 

        if request.POST['submit'] == _('Cancel'):
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 
            config.setConfiguration('BOOKTYPE_FRONTPAGE_HISTORY', frm.cleaned_data['show_changes'])

            import os.path, os

            if not os.path.exists('%s/templates/portal/' % staticRoot):
                os.makedirs('%s/templates/portal/' % staticRoot)

            try:
                f = open('%s/templates/portal/welcome_message.html' % staticRoot, 'w')
                
                textData = frm.cleaned_data['description'] 
                textData = textData.replace('{%', '').replace('%}', '').replace('{{', '').replace('}}', '')

                f.write(textData.encode('utf8'))
                f.close()

                messages.success(request, _('Successfuly saved changes.'))

                config.saveConfiguration()
            except IOError:
                messages.warning(request, _('Error while saving changes'))
            except config.ConfigurationError:
                messages.warning(request, _('Unknown error while saving changes.'))

            return HttpResponseRedirect(reverse('control_settings'))             
    else:
        try:
            f = open('%s/templates/portal/welcome_message.html' % staticRoot, 'r')
            textContent = unicode(f.read(), 'utf8')
            f.close()
        except IOError:
            textContent = ''

        frm = FrontpageForm(initial = {'show_changes': config.getConfiguration('BOOKTYPE_FRONTPAGE_HISTORY', True),
                                       'description': textContent})

    return render_to_response('booktypecontrol/settings_frontpage.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm
                               })

