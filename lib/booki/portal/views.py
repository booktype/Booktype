from django.shortcuts import render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import Http404, HttpResponse,HttpResponseRedirect
from django.contrib.auth.models import User
from django.db import transaction

from booki.editor import models
from booki.editor.views import getVersion

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
@transaction.commit_manually
def join_group(request, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    group.members.add(request.user)
    transaction.commit()

    return HttpResponseRedirect("/groups/%s/" % group.url_name)

@transaction.commit_manually
def remove_group(request, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    group.members.remove(request.user)
    transaction.commit()

    return HttpResponseRedirect("/groups/%s/" % group.url_name)

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

    return HttpResponseRedirect("/groups/%s/" % group.url_name)

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

    return HttpResponseRedirect("/groups/%s/" % groupid)


#
# front page listings
#
def view_groups(request):
    groups = models.BookiGroup.objects.all().extra(select={'lower_name': 'lower(name)'}).order_by('lower_name')

    return render_to_response('portal/groups.html', {"request": request, 
                                                     "title": "Booki groups", 
                                                     "groups": groups })

def view_books(request):
    books = models.Book.objects.all().extra(select={'lower_title': 'lower(title)'}).order_by('lower_title')

    return render_to_response('portal/books.html', {"request": request, 
                                                    "title": "Booki books", 
                                                    "books":      books })

def view_people(request):
    people = User.objects.all().extra(select={'lower_username': 'lower(username)'}).order_by('lower_username')
    return render_to_response('portal/people.html', {"request": request, 
                                                     "title": "Booki people", 
                                                     "people":      people })

def maintenance(request):
    return render_to_response('portal/maintenance.html', {"request":    request})
