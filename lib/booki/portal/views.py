from django.shortcuts import render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import Http404, HttpResponse,HttpResponseRedirect
from django.contrib.auth.models import User

from booki.editor import models
from booki.editor.views import getVersion

# debug

def debug_redis(request):
    import sputnik

    r = sputnik.redis.Redis()
    r.connect()

    client_id = r.get("sputnik:client_id")
    sputnikchannels = r.smembers("sputnik:channels")

    chnl = {}
    for ch in r.keys("sputnik:channel:*:channel"):
        chnl[ch] = r.smembers(ch)

    usrs = {}
    for ch in r.keys("sputnik:channel:*:users"):
        usrs[ch] = r.smembers(ch)


    allValues = {}

    import time, decimal

    _now = time.time()

    for ses in [k[4:-9] for k in  r.keys("ses:*:username")]:
        try:
            allValues[ses]  = {
                "channels": sputnik.smembers("ses:%s:channels" % ses),
                "last_access": r.get("ses:%s:last_access" % ses),
                "access_since": decimal.Decimal("%f" % _now) - r.get("ses:%s:last_access" % ses),
                "username": r.get("ses:%s:username" % ses)
                }
        except:
            pass

    locks = {}
    for ch in r.keys("booki:*:locks:*"):
        locks[ch] = r.get(ch)

    return render_to_response('portal/debug_redis.html', {"request": request, 
                                                          "client_id": client_id,
                                                          "sputnikchannels": sputnikchannels,
                                                          "channel": chnl.items(),
                                                          "users": usrs.items(),
                                                          "sessions": allValues.items(),
                                                          "locks": locks.items()
                                                          })


# FRONT PAGE

def view_frontpage(request):
    return render_to_response('portal/frontpage.html', {"request": request, 
                                                        "title": "Booki"})

# GROUPS

def view_group(request, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    books = models.Book.objects.filter(group=group)
    members = group.members.all()

    isMember = request.user in members
    yourBooks = models.Book.objects.filter(owner=request.user)

    return render_to_response('portal/group.html', {"request":    request, 
                                                    "title":      "Ovo je neki naslov",
                                                    "group":      group,
                                                    "books":      books,
                                                    "your_books": yourBooks,
                                                    "members":    members,
                                                    "is_member":  isMember})

def join_group(request, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    group.members.add(request.user)

    return HttpResponseRedirect("/groups/%s/" % group.url_name)


def remove_group(request, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    group.members.remove(request.user)

    return HttpResponseRedirect("/groups/%s/" % group.url_name)

def add_book(request, groupid):
    book = models.Book.objects.get(url_title=request.POST["book"])

    group = models.BookiGroup.objects.get(url_name=groupid)
    book.group = group
    book.save()

    return HttpResponseRedirect("/groups/%s/" % group.url_name)

def remove_book(request, groupid):
    book = models.Book.objects.get(url_title=request.GET["book"])
    book.group = None
    book.save()

    return HttpResponseRedirect("/groups/%s/" % groupid)


#
# front page listings
#
def view_groups(request):
    groups = models.BookiGroup.objects.all()
    return render_to_response('portal/groups.html', {"request": request, 
                                                     "title": "Booki groups", 
                                                     "groups": groups })

def view_books(request):
    books = models.Book.objects.all().order_by("title")
    return render_to_response('portal/books.html', {"request": request, 
                                                    "title": "Booki books", 
                                                    "books":      books })

def view_people(request):
    people = User.objects.all().order_by("username")
    return render_to_response('portal/people.html', {"request": request, 
                                                     "title": "Booki people", 
                                                     "people":      people })

def maintenance(request):
    return render_to_response('portal/maintenance.html', {"request":    request})
