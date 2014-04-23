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

from django.shortcuts import render
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse,HttpResponseRedirect
from django.contrib.auth.models import User
from django.db import transaction

from booki.editor import models
from booki.utils import security, pages
from django.conf import settings
from booki.utils.json_wrapper import json
from booki.utils.log import logWarning
from booki import constants

BOOKI_URL = settings.BOOKI_URL

try:
    OBJAVI_URL = settings.OBJAVI_URL
except AttributeError:
    OBJAVI_URL = constants.OBJAVI_URL

try:
    THIS_BOOKI_SERVER = settings.THIS_BOOKI_SERVER
except AttributeError:
    THIS_BOOKI_SERVER = constants.THIS_BOOKI_SERVER


# debug
    
def debug_redis(request):
    """
    Django View. This page shows basic debug information about redis.

    @todo: This should be removed. New Django Application for debuging and monitoring should be created.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    """

    import sputnik

    client_id = sputnik.get("sputnik:client_id")
    sputnikchannels = sputnik.smembers("sputnik:channels")

    chnl = {}
    for ch in sputnik.rkeys("sputnik:channel:*:channel"):
        chnl[ch] = sputnik.smembers(ch)

    usrs = {}
    for ch in sputnik.rkeys("sputnik:channel:*:users"):
        usrs[ch] = sputnik.smembers(ch)

#    for ch in r.keys('sputnik:*:messages'):
#        pass


    allValues = {}

    import time, decimal

    _now = time.time()

    for ses in [k[4:-9] for k in  sputnik.rkeys("ses:*:username")]:
        try:
            allValues[ses]  = {
                "channels": sputnik.smembers("ses:%s:channels" % ses),
                "last_access": sputnik.get("ses:%s:last_access" % ses),
                "access_since": decimal.Decimal("%f" % _now) - sputnik.get("ses:%s:last_access" % ses),
                "username": sputnik.get("ses:%s:username" % ses)
                }
        except:
            pass

    locks = {}
    for ch in sputnik.rkeys("booki:*:locks:*"):
        locks[ch] = sputnik.get(ch)

    killlocks = {}
    for ch in sputnik.rkeys("booki:*:killlocks:*"):
        killlocks[ch] = sputnik.get(ch)


    return render(request, 'bookiportal/debug_redis.html', {"request": request, 
                                                       "client_id": client_id,
                                                       "sputnikchannels": sputnikchannels,
                                                       "channel": chnl.items(),
                                                       "users": usrs.items(),
                                                       "sessions": allValues.items(),
                                                       "locks": locks.items(),
                                                       "killlocks": killlocks.items()
                                                       })

# FRONT PAGE

def view_frontpage(request):
    """
    Django View. This is main Booktype Front Page. 

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    """

    from booki.utils import config
    from booki.utils.misc import isUserLimitReached

    showHistory = config.getConfiguration('BOOKTYPE_FRONTPAGE_HISTORY', True)

    if showHistory:
        activityHistory = models.BookHistory.objects.filter(kind__in=[1, 10], book__hidden=False).order_by('-modified')[:20]
    else:
        activityHistory = []

    return render(request, 'bookiportal/frontpage.html', {"request": request, 
                                                     "activity_history": activityHistory,
                                                     "show_history": showHistory,
                                                     "limit_reached": isUserLimitReached(),
                                                    "title": "Booktype"})

# GROUPS

def view_group(request, groupid):
    """
    Django View. This is main Booktype Groups page.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type groupid: C{string}
    @param groupid: Unique group name
    """

    try:
        group = models.BookiGroup.objects.get(url_name=groupid)
    except models.BookiGroup.DoesNotExist:
        return pages.ErrorPage(request, "errors/group_does_not_exist.html", {"group_name": groupid})
    except models.BookiGroup.MultipleObjectsReturned:
        return pages.ErrorPage(request, "errors/group_does_not_exist.html", {"group_name": groupid})
        
    books = models.Book.objects.filter(group=group, hidden=False)
    members = group.members.all()

    isMember = request.user in members
    if request.user.is_authenticated():
        yourBooks = models.Book.objects.filter(owner=request.user, hidden=False)
    else:
        yourBooks = []

    bs = security.getUserSecurityForGroup(request.user, group)

    history = models.BookHistory.objects.filter(book__group=group)[:20]
    n_members = len(members)
    n_books = len(books)

    return render(request, 'bookiportal/group.html', {"request":    request, 
                                                 "title":      "Ovo je neki naslov",
                                                 "group":      group,
                                                 "books":      books,
                                                 "n_books":    n_books,
                                                 "your_books": yourBooks,
                                                 "members":    members,
                                                 "n_members": n_members,
                                                 "security":   bs,
                                                 "history": history,
                                                 "is_member":  isMember})
@transaction.commit_manually
def add_book(request, groupid):
    """
    Django View. Add new book to the group.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type groupid: C{string}
    @param groupid: Unique group name
    """

    if not request.POST.has_key("book"):
        return pages.ErrorPage(request, "500.html")

    book = models.Book.objects.get(url_title=request.POST["book"])

    group = models.BookiGroup.objects.get(url_name=groupid)
    book.group = group

    try:
        book.save()
    except:
        transaction.rollback()
    else:
        transaction.commit()

    try:
        resp = HttpResponseRedirect(reverse("view_group", args=[group.url_name]))
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()

    return resp

@transaction.commit_manually
def remove_book(request, groupid):
    """
    Django View. Remove book from the group.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type groupid: C{string}
    @param groupid: Unique group name
    """

    if not request.GET.has_key("book"):
        return pages.ErrorPage(request, "500.html")

    book = models.Book.objects.get(url_title=request.GET["book"])
    book.group = None

    try:
        book.save()
    except:
        transaction.rollback()
    else:
        transaction.commit()

    try:
        resp =HttpResponseRedirect(reverse("view_group", args=[groupid]))
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()

    return resp


#
# front page listings
#
def view_groups(request):
    """
    Django View. List all groups.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    """

    groups_list = models.BookiGroup.objects.all().extra(select={'lower_name': 'lower(name)'}).order_by('lower_name')

    paginator = Paginator(groups_list, 50) 

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        groups = paginator.page(page)
    except (EmptyPage, InvalidPage):
        groups = paginator.page(paginator.num_pages)

    return render(request, 'bookiportal/groups.html', {"request": request, 
                                                  "title": "Booktype groups", 
                                                  "groups": groups })

def view_books(request):
    """
    Django View. List all books.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    """

    if request.user.is_authenticated() and request.user.is_superuser:
        books = models.Book.objects.all()
    else:
        books = models.Book.objects.filter(hidden=False)

    books_list = books.extra(select={'lower_title': 'lower(title)'}).order_by('lower_title')

    paginator = Paginator(books_list, 50) 

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        books = paginator.page(page)
    except (EmptyPage, InvalidPage):
        books = paginator.page(paginator.num_pages)

    latest_books = models.Book.objects.filter(hidden=False).order_by('-created')[:5]

    import datetime
    # show active books in last 30 days
    now = datetime.datetime.now()-datetime.timedelta(30)

    from django.db.models import Count

    latest_active = [models.Book.objects.get(id=b['book']) for b in models.BookHistory.objects.filter(modified__gte = now, book__hidden=False).values('book').annotate(Count('book')).order_by("-book__count")[:5]]
    
    return render(request, 'bookiportal/books.html', {"request": request, 
                                                "title": "Booktype books", 
                                                "books":      books,
                                                "page": page, 
                                                "latest_books": latest_books,
                                                "latest_active": latest_active
                                                })

def view_people(request):
    """
    Django View. List all registered users.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    """

    people_list = User.objects.all().extra(select={'lower_username': 'lower(username)'}).order_by('lower_username')

    paginator = Paginator(people_list, 50) 

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        people = paginator.page(page)
    except (EmptyPage, InvalidPage):
        people = paginator.page(paginator.num_pages)

    latest_people = User.objects.all().order_by('-date_joined')[:5]

    import datetime
    now = datetime.datetime.now()-datetime.timedelta(30)

    from django.db.models import Count

    latest_active = [User.objects.get(id=b['user']) for b in models.BookHistory.objects.filter(modified__gte = now).values('user').annotate(Count('user')).order_by("-user__count")[:5]]

    return render(request, 'bookiportal/people.html', {"request":       request, 
                                                  "page":          page,
                                                  "latest_people": latest_people,
                                                  "latest_active": latest_active,
                                                  "title":         "Booktype people", 
                                                  "people":        people })

def maintenance(request):
    """
    Django View. Shows maintenance page.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    """

    return render(request, 'portal/maintenance.html', {"request":    request})


def _is_book_modified(book):
    """
    Checks if specific book has been modified.

    @todo: This has to be changed, this is terrible way to check difference in timestamps. This has been developed for archive.org, and is not in use anymore.

    @type book: C{booki.editor.models.Book}
    @param book: Book object
    @rtype: C{bool}
    @return: Returns True or False
    """

    from time import mktime

    bv = book.getVersion(None)
    created = mktime(book.created.timetuple())
    for chapter in models.Chapter.objects.filter(version=bv):
        logWarning("chapter %s created %s mod %s" % (chapter.id, book.created, chapter.modified))
        #5 seconds grace before a chapter is deemed modified
        if created + 5 < mktime(chapter.modified.timetuple()):
            return True
    return False


def view_books_by_id(request, scheme):
    """
    Find books with IDs of the requested schema, and return mapping of
    IDs to urls that match those books.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request.
    @type scheme: C{string}
    """
    logWarning("looking for books with %r identifier" % scheme)
    from booki.bookizip import DC
    from booki.editor.views import getVersion
    from urllib import urlencode
    namefilter = '{%s}identifier{%s}' % (DC, scheme)
    data = {}

    #from django.db import connection, transaction
    #cursor = connection.cursor()
    books = models.Book.objects.raw('SELECT editor_book.*, editor_info.value_string AS remote_id'
                                    ' FROM editor_book LEFT OUTER JOIN editor_info ON'
                                    ' (editor_book.id=editor_info.book_id) WHERE'
                                    ' editor_info.name=%s',  (namefilter,))

    for book in books:
        if book.hidden:
            continue
        values = data.setdefault(book.remote_id, [])
        values.append(book)
        logWarning(values)
    #data keys are identifiers in the set scheme, and the values are
    # a list of books with that identifier.
    #
    # depending on the mode, some books will be dropped.
    logWarning(data)
    selected_books = []
    for ID, books in data.iteritems():
        for book in books:
            if _is_book_modified(book):
                selected_books.append((ID, book.url_title, True))
                break
        else:
            selected_books.append((ID, books[0].url_title, False))

    msg = {}
    for ID, booki_id, modified in selected_books:
        msg[ID] = {'edit': '%s/%s/edit/' % (BOOKI_URL, booki_id), #edit link
                   'epub': (None if not modified                  #epub link
                            else  OBJAVI_URL + '?' + urlencode(
                                {'server': THIS_BOOKI_SERVER,
                                 'book': booki_id,
                                 'mode': 'epub',
                                 'destination': 'download',
                                 })
                            )
                   }

    s = json.dumps(msg)

    response = HttpResponse(s, mimetype="application/json")
    return response
