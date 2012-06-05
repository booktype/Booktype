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
from django.shortcuts import render_to_response, redirect
from django.template.loader import render_to_string
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.db import IntegrityError, transaction
from django.contrib.auth.decorators import login_required
try:
    from django.core.validators import email_re, RegexValidator, MinLengthValidator
except:
    from django.forms.fields import email_re

from django import forms

from django.template import RequestContext

from django.utils.translation import ugettext as _

from booki.editor import models
from booki.utils import pages


# What tabs do you want to have visible at the moment
#ADMIN_OPTIONS = ["dashboard", "people", "books", "filebrowse", "templates", "activity", "messages", "settings"]
ADMIN_OPTIONS = ["dashboard", "people", "books", "settings"]

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
                    b = models.Book.objects.get(pk=bookID)
                    channelList.append(b)
            
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
    from django.contrib.auth.models import User
    number_of_users = len(User.objects.all())

    # check the database size
    from django.db import connection
    cursor = connection.cursor()
    # This will not work if user has new style of configuration for the database
    cursor.execute("SELECT pg_database_size(%s)", [settings.DATABASE_NAME]);
    databaseSize = cursor.fetchone()[0]

    # Book activity
    activityHistory = models.BookHistory.objects.filter(kind__in=[1, 10]).order_by('-modified')[:20]

    return render_to_response('booktypecontrol/frontpage.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "online_users": onlineUsers,
                               "attachments_size": attachmentsSize,
                               "number_of_books": number_of_books,
                               "number_of_users": number_of_users,
                               "number_of_groups": number_of_groups,
                               "database_size": databaseSize,
                               "activity_history": activityHistory
                               })


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
                               })


def profile(request, username):
    """
    Shows info about one person.
    """

    from django.contrib.auth.models import User

    try:
        person = User.objects.get(username=username)
    except User.DoesNotExist:
        return pages.ErrorPage(request, "errors/user_does_not_exist.html", {"username": username})

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
                               })


class ProfileForm(forms.Form):
    username = forms.CharField(required=True, max_length=100, validators=[RegexValidator(r"^[\w\d\@\.\+\-\_]+$", message=_("Illegal characters in username.")), MinLengthValidator(3)])
    first_name = forms.CharField(required=True, max_length=100)
    email = forms.EmailField(required=True,max_length=100)
    profile = forms.ImageField(required=False)
    description = forms.CharField(required=False, widget=forms.Textarea)

    def __unicode__(self):
        return self.first_name


def edit_profile(request, username):
    from django.contrib.auth.models import User

    try:
        person = User.objects.get(username=username)
    except User.DoesNotExist:
        return pages.ErrorPage(request, "errors/user_does_not_exist.html", {"username": username})

    if request.method == 'POST': 
        frm = ProfileForm(request.POST, request.FILES) 

        if request.POST['submit'] == u'Cancel':
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
                               })


class PasswordForm(forms.Form):
    password1 = forms.CharField(label='Password', required=True, max_length=100, widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', required=True, max_length=100, widget=forms.PasswordInput, help_text = _("Enter the same password as above, for verification."))


    def __unicode__(self):
        return self.first_name


def edit_password(request, username):
    from django.contrib.auth.models import User

    try:
        person = User.objects.get(username=username)
    except User.DoesNotExist:
        return pages.ErrorPage(request, "errors/user_does_not_exist.html", {"username": username})

    if request.method == 'POST': 
        frm = PasswordForm(request.POST) 

        if request.POST['submit'] == u'Cancel':
            return HttpResponseRedirect('../') 

        if frm.is_valid(): 
            if frm.cleaned_data['password1'] == frm.cleaned_data['password2']:
                person.set_password(frm.cleaned_data['password1']) 
                person.save() 

                return HttpResponseRedirect(reverse('control_profile', args=[person.username])) 
    else:
        frm = PasswordForm()

    return render_to_response('booktypecontrol/edit_password.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "person": person,
                               "form": frm
                               })

class NewPersonForm(forms.Form):
    username = forms.CharField(required=True, max_length=100, validators=[RegexValidator(r"^[\w\d\@\.\+\-\_]+$", message=_("Illegal characters in username.")), MinLengthValidator(3)])
    first_name = forms.CharField(required=True, max_length=100)
    email = forms.EmailField(required=True,max_length=100)
    description = forms.CharField(required=False, widget=forms.Textarea)
    password1 = forms.CharField(label=_('Password'), required=True, max_length=100, widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Password confirmation'), required=True, max_length=100, widget=forms.PasswordInput, help_text = _("Enter the same password as above, for verification."))
    send_email = forms.BooleanField(label=_('Notify person by email'), required=False)


    def clean_username(self):
        from django.contrib.auth.models import User

        try:
            usr = User.objects.get(username=self.cleaned_data['username'])
        except User.DoesNotExist:
            pass
        else:
            raise forms.ValidationError("This Person already exists.")

        return self.cleaned_data['username']

    def clean_password2(self):
        if self.cleaned_data['password2'] != self.cleaned_data['password1']:
            raise forms.ValidationError("Passwords do not match.")


    def __unicode__(self):
        return self.username


def add_person(request):
    from django.contrib.auth.models import User

    if request.method == 'POST': 
        frm = NewPersonForm(request.POST) 

        if request.POST['submit'] == u'Cancel':
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
                                                         "password": frm.cleaned_data['password2']}))

                    from django.core.mail import EmailMultiAlternatives
                    emails = [frm.cleaned_data['email']]

                    msg = EmailMultiAlternatives('We have just created account for you', content, settings.REPORT_EMAIL_USER, emails)
                    msg.attach_alternative(content, "text/html")
                    msg.send(fail_silently=True)

                return HttpResponseRedirect(reverse('control_people')) 
            except IntegrityError:
                pass
                
    else:
        frm = NewPersonForm()

    return render_to_response('booktypecontrol/add_person.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm
                               })

def books(request):
    books = models.Book.objects.all().order_by("title")

    return render_to_response('booktypecontrol/books.html', 
                              {"request": request,
                               "books": books,
                               "admin_options": ADMIN_OPTIONS
                               })


def view_book(request, bookid):
    from booki.editor.views import getVersion
    from booki.utils import misc

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = getVersion(book, None)

    # this only shows info for latest version
    book_history =  models.BookHistory.objects.filter(version = book_version).order_by("-modified")[:20]
    book_collaborators =  [e.values()[0] for e in models.BookHistory.objects.filter(version = book_version, kind = 2).values("user__username").distinct()]

    from booki.utils import security
    bookSecurity = security.getUserSecurityForBook(request.user, book)
    isBookAdmin = bookSecurity.isAdmin()

    import sputnik
    channel_name = "/booki/book/%s/%s/" % (book.id, book_version.getVersion())
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
                               "book_version": book_version.getVersion(),
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

class NewBookForm(forms.Form):
    title = forms.CharField(label=_("Title"), required=True, max_length=100)
    description = forms.CharField(required=False, widget=forms.Textarea)
    owner = forms.ModelChoiceField(queryset=User.objects.all().order_by("username"), required=True)
    license = forms.ModelChoiceField(queryset=models.License.objects.all().order_by("name"), required=True)
    is_hidden = forms.BooleanField(label=_('Initially hide from others'), required=False)
    cover = forms.ImageField(required=False)

    def clean_title(self):
        from booki.utils.book import checkBookAvailability

        if not checkBookAvailability(self.cleaned_data['title']):
            raise forms.ValidationError(_("This Book already exists."))

        return self.cleaned_data['title']


    def __unicode__(self):
        return self.username


def add_book(request):
    from booki.utils.book import createBook

    if request.method == 'POST': 
        frm = NewBookForm(request.POST, request.FILES) 

        if request.POST['submit'] == u'Cancel':
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

                        book.setCover(fname)
                        os.unlink(fname)
                    except:
                        pass
                    
                book.save()

                return HttpResponseRedirect(reverse('control_books')) 
            except:
                pass
    else:
        frm = NewBookForm()

    return render_to_response('booktypecontrol/add_book.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm
                               })


class BookForm(forms.Form):
    description = forms.CharField(required=False, widget=forms.Textarea)
    owner = forms.ModelChoiceField(queryset=User.objects.all().order_by("username"), required=True)
    license = forms.ModelChoiceField(queryset=models.License.objects.all().order_by("name"), required=True)
    is_hidden = forms.BooleanField(label=_('Initially hide from others'), required=False)
    cover = forms.ImageField(required=False)

    def clean_title(self):
        from booki.utils.book import checkBookAvailability

        if not checkBookAvailability(self.cleaned_data['title']):
            raise forms.ValidationError(_("This Book already exists."))

        return self.cleaned_data['title']


    def __unicode__(self):
        return self.username


def edit_book(request, bookid):
    from booki.editor.views import getVersion

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = getVersion(book, None)

    if request.method == 'POST': 
        frm = BookForm(request.POST, request.FILES) 

        if request.POST['submit'] == u'Cancel':
            return HttpResponseRedirect(reverse('control_book', args=[book.url_title])) 

        if frm.is_valid(): 
            try:
                book.license = frm.cleaned_data['license']
                book.description = frm.cleaned_data['description']
                book.is_hidden = frm.cleaned_data['is_hidden']
                book.save()

                if request.FILES.has_key('cover'):
                    from booki.utils import misc
                    import os

                    try:
                        fh, fname = misc.saveUploadedAsFile(request.FILES['cover'])
                        book.setCover(fname)
                        os.unlink(fname)
                    except:
                        pass
                    
                book.save()

#                messages.success(request, 'Successfuly saved changes.')

                return HttpResponseRedirect(reverse('control_book', args=[book.url_title])) 
            except:
                pass
    else:
        data = {'description': book.description,
                'cover': book.cover}

        if book.owner:
            data['owner'] = book.owner.id
        if book.license:
            data['license'] = book.license.id
        
        frm = BookForm(initial=data)

    return render_to_response('booktypecontrol/edit_book.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm,
                               "book": book
                               })



class BookRenameForm(forms.Form):
    title = forms.CharField(label=_("Title"), required=True, max_length=200)
    url_title = forms.CharField(label=_("URL title"), 
                                required=False, 
                                max_length=200, 
                                validators=[RegexValidator(r"^[\w\s\_\.\-\d]+$", message=_("Illegal characters in URL title."))],
                                help_text=_("If you leave this field empty URL title will be assigned automatically."))

    def __unicode__(self):
        return self.username


def rename_book(request, bookid):
    from booki.editor.views import getVersion

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = getVersion(book, None)

    if request.method == 'POST': 
        frm = BookRenameForm(request.POST, request.FILES) 

        if request.POST['submit'] == u'Cancel':
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
                    return HttpResponseRedirect(reverse('control_book', args=[book.url_title]))
            else:
                    renameBook(book, title, URLTitle)
                    book.save()
                    return HttpResponseRedirect(reverse('control_book', args=[book.url_title]))


    else:
        frm = BookRenameForm(initial={'title': book.title, 'url_title': book.url_title})

    return render_to_response('booktypecontrol/rename_book.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm,
                               "book": book
                               })

def viewsettings(request):
    return render_to_response('booktypecontrol/settings.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS                               
                               })



class SiteDescriptionForm(forms.Form):
    title = forms.CharField(label=_("Site title"), required=True, max_length=200)
    tagline = forms.CharField(label=_("Tagline"), required=False, max_length=200)
    favicon = forms.FileField(label=_("Favicon"), required=False, help_text=_("Upload .ico file"))
        
    def __unicode__(self):
        return self.username


def settings_description(request):
    if request.method == 'POST': 
        frm = SiteDescriptionForm(request.POST, request.FILES) 

        if request.POST['submit'] == u'Cancel':
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

                    config.setConfiguration('BOOKTYPE_SITE_FAVICON', '%s/static/favicon.ico' % settings.BOOKI_URL)
                except:
                    pass

            config.saveConfiguration()

            return HttpResponseRedirect(reverse('control_settings'))             
    else:
        from booki.utils import config
        frm = SiteDescriptionForm(initial={'title': config.getConfiguration('BOOKTYPE_SITE_NAME'),
                                           'tagline': config.getConfiguration('BOOKTYPE_SITE_TAGLINE')})


    return render_to_response('booktypecontrol/settings_description.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm                               
                               })

from django.forms.fields import ChoiceField

class BookCreateForm(forms.Form):
    visible = forms.BooleanField(label=_('Visibility'), required=False, help_text=_('If it is turned on then all books will be visible to everyone.'))
    license = forms.ModelChoiceField(queryset=models.License.objects.all().order_by("name"), required=False, help_text=_("Default license for newly created book."))
        
    def __unicode__(self):
        return 'Book create'


def settings_book_create(request):
    if request.method == 'POST': 
        frm = BookCreateForm(request.POST, request.FILES) 

        if request.POST['submit'] == u'Cancel':
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 
            from booki.utils import config

            config.setConfiguration('CREATE_BOOK_VISIBLE', frm.cleaned_data['visible'])

            if frm.cleaned_data['license']:
                config.setConfiguration('CREATE_BOOK_LICENSE', frm.cleaned_data['license'].abbrevation)
            else:
                config.setConfiguration('CREATE_BOOK_LICENSE', '')

            config.saveConfiguration()

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
                               })



class LicenseForm(forms.Form):
    abbrevation = forms.CharField(label=_("Abbrevation"), required=True, max_length=30)
    name = forms.CharField(label=_("Name"), required=True, max_length=100)
        
    def __unicode__(self):
        return self.abbrevation


def settings_license(request):
    if request.method == 'POST': 
        frm = LicenseForm(request.POST, request.FILES) 

        if request.POST['submit'] == u'Cancel':
            return HttpResponseRedirect(reverse('control_settings')) 

        if frm.is_valid(): 
            from booki.utils import config

            license = models.License(abbrevation = frm.cleaned_data['abbrevation'],
                                     name = frm.cleaned_data['name'])
            license.save()

            return HttpResponseRedirect(reverse('control_settings_license'))             
    else:
        frm = LicenseForm()

    licenses = models.License.objects.all().order_by("name")

    return render_to_response('booktypecontrol/settings_license.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm,
                               "licenses": licenses
                               })

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
                return pages.ErrorPage(request, "errors/license_does_not_exist.html", {"username": ''})

            license.delete()

            return HttpResponseRedirect(reverse('control_settings_license')) 

        if frm.is_valid(): 
            try:
                license = models.License.objects.get(pk=licenseid)
            except models.License.DoesNotExist:
                return pages.ErrorPage(request, "errors/license_does_not_exist.html", {"username": ''})

            license.abbrevation = frm.cleaned_data['abbrevation']
            license.name = frm.cleaned_data['name']
            license.save()

            return HttpResponseRedirect(reverse('control_settings_license'))             
    else:
        try:
            license = models.License.objects.get(pk=licenseid)
        except models.License.DoesNotExist:
            # change this
            return pages.ErrorPage(request, "errors/license_does_not_exist.html", {"username": ''})

        books = models.Book.objects.filter(license=license).order_by("title")
            
        frm = LicenseForm(initial = {'abbrevation': license.abbrevation,
                                     'name': license.name})

    return render_to_response('booktypecontrol/settings_license_edit.html', 
                              {"request": request,
                               "admin_options": ADMIN_OPTIONS,
                               "form": frm,
                               "licenseid": licenseid,
                               "books": books
                               })




