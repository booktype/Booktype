from django.shortcuts import render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse,HttpResponseRedirect
from django.contrib.auth.models import User
from django.db import transaction

from booki.editor import models
from booki.utils import security, pages

# debug

def debug_redis(request):
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


    return render_to_response('portal/debug_redis.html', {"request": request, 
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
    return render_to_response('portal/frontpage.html', {"request": request, 
                                                        "title": "Booki"})

# GROUPS

def view_group(request, groupid):
    try:
        group = models.BookiGroup.objects.get(url_name=groupid)
    except models.BookiGroup.DoesNotExist:
        return pages.ErrorPage(request, "errors/group_does_not_exist.html", {"group_name": groupid})
        
    books = models.Book.objects.filter(group=group)
    members = group.members.all()

    isMember = request.user in members
    if request.user.is_authenticated():
        yourBooks = models.Book.objects.filter(owner=request.user)
    else:
        yourBooks = []

    bs = security.getUserSecurityForGroup(request.user, group)

    history = models.BookHistory.objects.filter(book__group=group)[:20]
    n_members = len(members)
    n_books = len(books)

    return render_to_response('portal/group.html', {"request":    request, 
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
    book = models.Book.objects.get(url_title=request.POST["book"])

    group = models.BookiGroup.objects.get(url_name=groupid)
    book.group = group

    try:
        book.save()
    except:
        transaction.rollback()
    else:
        transaction.commit()

    return HttpResponseRedirect(reverse("view_group", args=[group.url_name]))

@transaction.commit_manually
def remove_book(request, groupid):
    book = models.Book.objects.get(url_title=request.GET["book"])
    book.group = None

    try:
        book.save()
    except:
        transaction.rollback()
    else:
        transaction.commit()

    return HttpResponseRedirect(reverse("view_group", args=[groupid]))


#
# front page listings
#
def view_groups(request):
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

    return render_to_response('portal/groups.html', {"request": request, 
                                                     "title": "Booki groups", 
                                                     "groups": groups })

def view_books(request):
    books_list = models.Book.objects.all().extra(select={'lower_title': 'lower(title)'}).order_by('lower_title')

    paginator = Paginator(books_list, 50) 

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        books = paginator.page(page)
    except (EmptyPage, InvalidPage):
        books = paginator.page(paginator.num_pages)

    latest_books = models.Book.objects.all().order_by('-created')[:5]

    import datetime
    # show active books in last 30 days
    now = datetime.datetime.now()-datetime.timedelta(30)

    from django.db.models import Count

    latest_active = [models.Book.objects.get(id=b['book']) for b in models.BookHistory.objects.filter(modified__gte = now).values('book').annotate(Count('book')).order_by("-book__count")[:5]]
    
    return render_to_response('portal/books.html', {"request": request, 
                                                    "title": "Booki books", 
                                                    "books":      books,
                                                    "page": page, 
                                                    "latest_books": latest_books,
                                                    "latest_active": latest_active
                                                    })

def view_people(request):
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


    return render_to_response('portal/people.html', {"request":       request, 
                                                     "page":          page,
                                                     "latest_people": latest_people,
                                                     "latest_active": latest_active,
                                                     "title":         "Booki people", 
                                                     "people":        people })

def maintenance(request):
    return render_to_response('portal/maintenance.html', {"request":    request})
