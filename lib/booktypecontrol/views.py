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



