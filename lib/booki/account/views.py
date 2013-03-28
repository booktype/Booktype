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
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.contrib.auth.decorators import login_required
try:
    from django.core.validators import email_re
except:
    from django.forms.fields import email_re

from django import forms

from booki import constants
from booki.utils import pages
from django.utils.translation import ugettext as _

from booki.utils.log import logBookHistory, logError
from booki.utils.book import createBook
from booki.editor import common

from booki.messaging.views import get_endpoint_or_none
from booki.utils import config


def view_accounts(request):
    """
    Django View for /accounts/ url. Does nothing at the moment.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request

    @todo: This has to change as soon as possible. Redirect somewhere? Show list of current users?
    """
    return HttpResponse("", mimetype="text/plain")

# signout

def signout(request):
    """
    Django View. Gets called when user wants to signout.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request
    """

    from django.contrib import auth

    auth.logout(request)

    return HttpResponseRedirect(reverse("frontpage"))

# signin

@transaction.commit_manually
def signin(request):
    """
    Django View. Gets called when user wants to signin or create new account.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request
    """


    from booki.utils.json_wrapper import simplejson
    from booki.utils.misc import  isUserLimitReached
    from booki.editor.models import BookiGroup

    from django.core.exceptions import ObjectDoesNotExist
    from django.contrib import auth

    limitReached = isUserLimitReached()

    if request.POST.get("ajax", "") == "1":
        ret = {"result": 0}

        if request.POST.get("method", "") == "register" and config.getConfiguration('FREE_REGISTRATION') and not limitReached:
            def _checkIfEmpty(key):
                return request.POST.get(key, "").strip() == ""

            def _doChecksForEmpty():
                if _checkIfEmpty("username"): return 2
                if _checkIfEmpty("email"): return 3
                if _checkIfEmpty("password") or _checkIfEmpty("password2"): return 4
                if _checkIfEmpty("fullname"): return 5

                return 0

            ret["result"] = _doChecksForEmpty()

            if ret["result"] == 0: # if there was no errors
                import re

                def _doCheckValid():
                    # check if it is valid username
                    # - from 2 to 20 characters long
                    # - word, number, ., _, -
                    mtch = re.match('^[\w\d\_\.\-]{2,20}$', request.POST.get("username", "").strip())
                    if not mtch:  return 6

                    # check if it is valid email
                    if not bool(email_re.match(request.POST["email"].strip())): return 7

                    if request.POST.get("password", "") != request.POST.get("password2", "").strip(): return 8
                    if len(request.POST.get("password", "").strip()) < 6: return 9

                    if len(request.POST.get("fullname", "").strip()) > 30: return 11

                    # check if this user exists
                    try:
                        u = auth.models.User.objects.get(username=request.POST.get("username", "").strip())
                        return 10
                    except auth.models.User.DoesNotExist:
                        pass

                    return 0

                ret["result"] = _doCheckValid()

                if ret["result"] == 0:
                    ret["result"] = 1

                    user = None

                    try:
                        user = auth.models.User.objects.create_user(username=request.POST["username"].strip(),
                                                                    email=request.POST["email"].strip(),
                                                                    password=request.POST["password"].strip())
                    except IntegrityError:
                        ret["result"] = 10
                    except:
                        ret["result"] = 10
                        user = None

                    # this is not a good place to fire signal, but i need password for now
                    # should create function createUser for future use

                    if user:
                        user.first_name = request.POST["fullname"].strip()

                        import booki.account.signals
                        booki.account.signals.account_created.send(sender = user, password = request.POST["password"])

                        try:
                            user.save()

                            # groups

                            for groupName in simplejson.loads(request.POST.get("groups")):
                                if groupName.strip() != '':
                                    sid = transaction.savepoint()

                                    try:
                                        group = BookiGroup.objects.get(url_name=groupName)
                                        group.members.add(user)
                                    except:
                                        transaction.savepoint_rollback(sid)
                                    else:
                                        transaction.savepoint_commit(sid)

                            user2 = auth.authenticate(username=request.POST["username"].strip(), password=request.POST["password"].strip())
                            auth.login(request, user2)
                        except:
                            transaction.rollback()
                            ret["result"] = 666
                        else:
                            transaction.commit()
                    else:
                        transaction.rollback()

        if request.POST.get("method", "") == "signin":
            user = auth.authenticate(username=request.POST["username"].strip(), password=request.POST["password"].strip())

            if user:
                auth.login(request, user)
                ret["result"] = 1

                from django.core.urlresolvers import reverse
                ret["redirect"] = reverse('view_profile', args=[user.username])
            else:
                try:
                    usr = auth.models.User.objects.get(username=request.POST["username"])
                    # User does exist. Must be wrong password then
                    ret["result"] = 3
                except auth.models.User.DoesNotExist:
                    # User does not exist
                    ret["result"] = 2

        try:
            resp = HttpResponse(simplejson.dumps(ret), mimetype="text/json")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()
            
        return resp

    from django.core.urlresolvers import reverse
    redirect = request.GET.get('redirect', '')

    if(redirect == reverse('frontpage')): 
        redirect = ''
    
    if request.GET.get('next', None):
        redirect = request.GET.get('next')


    joinGroups = []
    for groupName in request.GET.getlist("group"):
        try:
            joinGroups.append(BookiGroup.objects.get(url_name=groupName))
        except BookiGroup.DoesNotExist:
            pass

    try:
        resp = render_to_response('account/signin.html', {'request': request, 
                                                          'redirect': redirect, 
                                                          'joingroups': joinGroups, 
                                                          'limit_reached': limitReached})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()
        
    return resp


# forgotpassword
@transaction.commit_manually
def forgotpassword(request):
    """
    Django View. Gets called when user wants to change password he managed to forget.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request
    """

    from booki.utils.json_wrapper import simplejson
    from django.core.exceptions import ObjectDoesNotExist
    from django.contrib.auth.models import User

    if request.POST.get("ajax", "") == "1":
        ret = {"result": 0}
        usr = None

        if request.POST.get("method", "") == "forgot_password":
            def _checkIfEmpty(key):
                return request.POST.get(key, "").strip() == ""

            def _doChecksForEmpty():
                if _checkIfEmpty("username"): return 2
                return 0

            ret["result"] = _doChecksForEmpty()

            if ret["result"] == 0:
                usersToEmail = list(User.objects.filter(Q(username=request.POST.get("username", "")) | Q(email=request.POST.get("username", ""))))

                for usr in usersToEmail:
                    from booki.account import models as account_models

                    def generateSecretCode():
                        import string
                        from random import choice
                        return ''.join([choice(string.letters + string.digits) for i in range(30)])

                    secretcode = generateSecretCode()

                    account_models = account_models.UserPassword()
                    account_models.user = usr
                    account_models.remote_useragent = request.META.get('HTTP_USER_AGENT','')
                    account_models.remote_addr = request.META.get('REMOTE_ADDR','')
                    account_models.remote_host = request.META.get('REMOTE_HOST','')
                    account_models.secretcode = secretcode

                    # In case of an error we really should not send email to user and do rest of the procedure
                    try:
                        account_models.save()
                    except:
                        transaction.rollback()
                    else:
                        transaction.commit()

                    THIS_BOOKI_SERVER = config.getConfiguration('THIS_BOOKI_SERVER')
                    body = render_to_string('account/password_reset_email.html', 
                                            dict(secretcode=secretcode,
                                                 hostname=THIS_BOOKI_SERVER))
                    
                    from django.core.mail import EmailMessage

                    msg = EmailMessage(_('Reset password'), body, settings.REPORT_EMAIL_USER, [usr.email])
                    msg.content_subtype = 'html'

                    try:
                        msg.send()
                    except:
                        ret["result"] = 4

                if len(usersToEmail) == 0:
                    ret["result"] = 3

        # Do we need rollback for this?!
        try:
            resp = HttpResponse(simplejson.dumps(ret), mimetype="text/json")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    # Do we need commit for this?!
    try:
        resp = render_to_response('account/forgot_password.html', {"request": request})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()

    return resp


# forgotpasswordenter
@transaction.commit_manually
def forgotpasswordenter(request):
    """
    Django View. Gets called when user clicks on the link he recieved over email.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request
    """

    from booki.utils.json_wrapper import simplejson

    secretcode = request.GET.get('secretcode', '')

    from django.core.exceptions import ObjectDoesNotExist
    from django.contrib.auth.models import User

    if request.POST.get("ajax", "") == "1":
        ret = {"result": 0}
        usr = None

        if request.POST.get("method", "") == "forgot_password_enter":
            def _checkIfEmpty(key):
                return request.POST.get(key, "").strip() == ""

            def _doChecksForEmpty():
                if _checkIfEmpty("secretcode"): return 2
                if _checkIfEmpty("password1"): return 3
                if _checkIfEmpty("password2"): return 4

                return 0

            ret["result"] = _doChecksForEmpty()

            if ret["result"] == 0:

                from booki.account import models as account_models
                allOK = True

                try:
                    pswd = account_models.UserPassword.objects.get(secretcode=request.POST.get("secretcode", ""))
                except account_models.UserPassword.DoesNotExist:
                    allOK = False

                if allOK:
                    pswd.user.set_password(request.POST.get("password1", ""))
                    pswd.user.save()
                else:
                    ret["result"] = 5

        try:
            resp = HttpResponse(simplejson.dumps(ret), mimetype="text/json")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    try:
        resp = render_to_response('account/forgot_password_enter.html', {"request": request, "secretcode": secretcode})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()

    return resp

def view_profile(request, username):
    """
    Django View. Shows user profile. Right now, this is just basics.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request
    @type username: C{string}
    @param username: Username.

    @todo: Check if user exists. 
    """

    from django.contrib.auth.models import User
    from booki.editor import models
    from booki.utils.misc import isBookLimitReached

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/user_does_not_exist.html", {"username": username})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()
            
        return resp

    notification_filter = ''

    if request.user.username == username:
        books = models.Book.objects.filter(owner=user)
        endpoint = get_endpoint_or_none("@"+user.username)

        if endpoint:
            endpoint_config = endpoint.get_config()

            if endpoint_config:
                notification_filter = endpoint_config.notification_filter
    else:
        if request.user.is_authenticated() and request.user.is_superuser:
            books = models.Book.objects.filter(owner=user)
        else:
            books = models.Book.objects.filter(owner=user, hidden=False)
    
    groups = user.members.all()
    
    from django.utils.html import escape
    userDescription = escape(user.get_profile().description)

    admin_create = config.getConfiguration('ADMIN_CREATE_BOOKS')
    admin_import = config.getConfiguration('ADMIN_IMPORT_BOOKS')

    if request.user.is_superuser:
        admin_create = False
        admin_import = False

    try:
        resp = render_to_response('account/view_profile.html', {"request": request,
                                                                "user": user,
                                                                "admin_create": admin_create,
                                                                "admin_import": admin_import,
                                                                "user_description": '<br/>'.join(userDescription.replace('\r','').split('\n')),
                                                                "books": books,
                                                                "limit_reached": isBookLimitReached(),
                                                                "notification_filter": notification_filter,
                                                                "groups": groups})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()

    return resp

@transaction.commit_manually
def save_settings(request, username):
    from django.contrib.auth.models import User
    from booki.editor import models

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return pages.ErrorPage(request, "errors/user_does_not_exist.html", {"username": username})

    if request.user.username != username:
        return HttpResponse("No, can't do!", "text/plain")

    profile = user.get_profile()

    user.email      = request.POST.get('email' ,'')
    user.first_name = request.POST.get('fullname', '')
    user.save()

    profile.description = request.POST.get('aboutyourself', '')

    if request.FILES.has_key('profile'):
        from booki.utils import misc

        # Check for any kind of error at the moment.
        # Notify user later with different messages.

        try:
            misc.setProfileImage(user, request.FILES['profile'])
        except:
            pass

    try:
        profile.save()
        
        endpoint_config = get_endpoint_or_none("@"+user.username).get_config()
        endpoint_config.notification_filter = request.POST.get('notification', '')
        endpoint_config.save()
    except:
        # Should set some error code here
        transaction.rollback()
    else:
        transaction.commit()

    try:
        resp = HttpResponse('<html><head><script>var j = parent.jQuery; j(function() { j.booki.profile.reloadProfileInfo(); });</script></head></html>', 'text/html')
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()

    return resp


def view_profilethumbnail(request, profileid):
    """
    Django View. Shows user profile image.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request
    @type profileid: C{string}
    @param profileid: Username.

    @todo: Check if user exists. 
    """

    from django.http import HttpResponse

    from django.contrib.auth.models import User

    try:
        u = User.objects.get(username=profileid)
    except User.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/user_does_not_exist.html", {"username": profileid})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    name = ''

    def _getDefaultProfile():
        "Return path to default profile image."

        try:
            name = '%s/images/%s' % (settings.STATIC_ROOT, settings.DEFAULT_PROFILE_IMAGE)
        except AttributeError:
            name = '%s%s' % (settings.SITE_STATIC_ROOT, '/images/anonymous.png')

        return name

    # this should be a seperate function

    if not u.get_profile().image:
        name = _getDefaultProfile()
    else:
        name =  u.get_profile().image.path

    import Image
    
    try:
        image = Image.open(name)
    except IOError:
        image = Image.open(_getDefaultProfile())

    image.thumbnail((int(request.GET.get('width', 24)), int(request.GET.get('width', 24))), Image.ANTIALIAS)

    # serialize to HTTP response
    # this could throw exception if PIL does not have support for jpeg
    try:
        response = HttpResponse(mimetype="image/jpg")
        image.save(response, "JPEG")
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()
        
    return response


@transaction.commit_manually
def create_book(request, username):
    """
    Django View. Show content for Create Book dialog and creates book.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request
    @type username: C{string}
    @param username: Username.
    """

    from django.contrib.auth.models import User
    from booki.utils.misc import isBookLimitReached

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/user_does_not_exist.html", {"username": username})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp

    if isBookLimitReached() or not request.user.is_authenticated():
        try:
            resp = pages.ErrorPage(request, "errors/no_permissions.html")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp

    from booki.utils.book import checkBookAvailability, createBook
    from booki.editor import models

    book_visible = config.getConfiguration('CREATE_BOOK_VISIBLE')
    book_license = config.getConfiguration('CREATE_BOOK_LICENSE')
    admin_create = config.getConfiguration('ADMIN_CREATE_BOOKS')

    if request.user.is_superuser:
        admin_create = False


    if request.GET.get("q", "") == "check":
        from booki.utils.json_wrapper import json

        data = {"available": checkBookAvailability(request.GET.get('bookname', '').strip())}

        try:
            resp = HttpResponse(json.dumps(data), "text/plain")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp

    if request.method == 'POST' and admin_create == False:
        book = None
        try:
            # hidden on
            # description
            # license
            # title
            # cover

            book = createBook(request.user, request.POST.get('title'))

            lic = models.License.objects.get(abbrevation=request.POST.get('license'))
            book.license = lic
            book.description = request.POST.get('description', '')

            if request.POST.get("hidden", "") == "on":
                is_hidden = True
            else:
                is_hidden = False
            book.hidden = is_hidden
            
            from django.core.files import File

            if request.FILES.has_key('cover'):
                # TODO: Show some kind of error message to the user
                from booki.utils import misc
                import os

                try:
                    fh, fname = misc.saveUploadedAsFile(request.FILES['cover'])
                    book.setCover(fname)
                    os.unlink(fname)
                except:
                    pass

            book.save()
                
        except:
            transaction.rollback()
        else:
            transaction.commit()


        try:
            resp = render_to_response('account/create_book_redirect.html', {"request": request,
                                                                            "user": user,
                                                                            "book": book})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp
        
    from booki.editor.models import License
    
    licenses = License.objects.all().order_by('name')


    try:
        resp = render_to_response('account/create_book.html', {"request": request,
                                                               "book_visible": book_visible,
                                                               "book_license": book_license,
                                                               "admin_create": admin_create,
                                                               "licenses": licenses,
                                                               "user": user})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()    

    return resp


@transaction.commit_manually
def create_group(request, username):
    """
    Django View. Show content for Create Group dialog and creates group.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request
    @type username: C{string}
    @param username: Username.
    """

    from django.contrib.auth.models import User

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/user_does_not_exist.html", {"username": username})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp

    if not request.user.is_authenticated():
        try:
            resp = pages.ErrorPage(request, "errors/no_permissions.html")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp

            
    from booki.utils.book import checkGroupAvailability, createBookiGroup
    from booki.editor import models

    if request.GET.get("q", "") == "check":
        from booki.utils.json_wrapper import json

        data = {"available": checkGroupAvailability(request.GET.get('groupname', '').strip())}

        try:
            resp = HttpResponse(json.dumps(data), "text/plain")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp

    if request.GET.get("q", "") == "create":
        from booki.utils.json_wrapper import json

        groupName = request.GET.get('name', '').strip()
        groupDescription = request.GET.get('description', '').strip()

        groupCreated = False

        if checkGroupAvailability(groupName):
            try:
                group = createBookiGroup(groupName, groupDescription, request.user)
                group.members.add(request.user)
                groupCreated = True
            except BookiGroupExist:
                groupCreated = False
                transaction.rollback()
            else:
                transaction.commit()

        data = {'created': groupCreated}

        try:
            resp = HttpResponse(json.dumps(data), "text/plain")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp

    try:
        resp = render_to_response('account/create_group.html', {"request": request,
                                                                "user": user})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()    

    return resp


@transaction.commit_manually
def import_book(request, username):
    """
    Django View. Book Import dialog.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request
    @type username: C{string}
    @param username: Username.
    """

    from django.contrib.auth.models import User
    from booki.utils.misc import isBookLimitReached

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/user_does_not_exist.html", {"username": username})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp

    if isBookLimitReached() or not request.user.is_authenticated():
        try:
            resp = pages.ErrorPage(request, "errors/no_permissions.html")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp
            
    from booki.utils.book import checkGroupAvailability, createBookiGroup
    from booki.editor import models

    if request.GET.get("q", "") == "check":
        from booki.utils.json_wrapper import json

        data = {"available": checkGroupAvailability(request.GET.get('groupname', '').strip())}

        try:
            resp = HttpResponse(json.dumps(data), "text/plain")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp

    book_visible = config.getConfiguration('CREATE_BOOK_VISIBLE')
    admin_import = config.getConfiguration('ADMIN_IMPORT_BOOKS')

    if request.user.is_superuser:
        admin_import = False


    if request.GET.get("q", "") == "import" and admin_import == False:
        from booki.utils.json_wrapper import json

        data = {}

        try:
            bookid = request.GET.get('source', '')
            importType = request.GET.get('importtype', '')
            renameTitle = request.GET.get('title', '')

            extraOptions = {}

            if renameTitle:
                extraOptions['book_title'] = renameTitle

            if request.GET.get('hidden', '') != '':
                extraOptions['hidden'] = True

            ESPRI_URL = config.getConfiguration('ESPRI_URL')

            importSources = {  
                "archive":      (ESPRI_URL, "archive.org"),
                "wikibooks":    (ESPRI_URL, "wikibooks"),
                "epub":         (ESPRI_URL, "url"),
                }
            
            if importType == "booki":
                bookid = bookid.rstrip('/')
                booki_url, book_url_title = bookid.rsplit("/", 1)
                base_url = "%s/export/%s/export" % (booki_url, book_url_title)
                source = "booki"
            else:
                base_url, source = importSources[importType]

            book = common.importBookFromUrl2(user, base_url,
                                             args=dict(source=source,
                                                       book=bookid),
                                             **extraOptions
                                             )
        except Exception:
            data['imported'] = False
            transaction.rollback()
        else:
            transaction.commit()
            data['imported'] = True

            from django.core.urlresolvers import reverse
            data['info_url'] = reverse('book_info', args=[book.url_title])

        try:
            resp = HttpResponse(json.dumps(data), "text/plain")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp


    try:
        resp = render_to_response('account/import_book.html', {"request": request,
                                                               "book_visible": book_visible,
                                                               "admin_import": admin_import,
                                                               "user": user})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()    

    return resp
