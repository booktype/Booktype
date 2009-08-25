from django.shortcuts import render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from django.http import Http404, HttpResponse

from django import forms

from booki.editor import models

# BOOK

def edit_book(request, project, edition):
    project = models.Project.objects.get(url_name__iexact=project)
    book = models.Book.objects.get(project=project, url_title__iexact=edition)
    chapters = models.Chapter.objects.filter(book=book)


    return render_to_response('editor/edit_book.html', {"project": project, "book": book, "chapters": chapters, "request": request})

def view_book(request, project, edition):
    book = models.Book.objects.get(project__url_name__iexact=project, url_title__iexact=edition)
    chapters = models.Chapter.objects.filter(book=book)

    return render_to_response('editor/view_book.html', {"project": project, "book": book, "chapters": chapters})


# PROJECT

def view_project(request, project):
    books = list(models.Book.objects.filter(project__url_name__iexact=project))
    return render_to_response('editor/view_project.html', {"project": project, "books": books})

def view_attachment(request, project, attachment):
    return render_to_response('editor/view_attachment.html', {"project": project, "attachment": attachment})

def view_editor(request, project):
    return render_to_response('editor/view_editor.html', {"project": project})


# FRONT PAGE

def view_frontpage(request):
    return render_to_response('editor/view_frontpage.html', {"request": request, "title": "Ovo je neki naslov"})


import redis


# sputnik

# should be ids and not names

sputnik_mapper = (
  (r'^/booki/$', 'booki_main'),
#  (r'^/booki/book/(\d+)/(\d+)/$', "booki_book"),
  (r'^/booki/book/(?P<projectid>\d+)/(?P<bookid>\d+)/$', 'booki_book'),
  (r'^/chat/(?P<projectid>\d+)/(?P<bookid>\d+)/$', 'booki_chat')
)

def dispatcher(request):
    global _clientID

    import simplejson, re, sputnik

    inp =  request.POST

    results = []

    clientID = None
    messages = simplejson.loads(inp["messages"])

    r = redis.Redis()

    # nesto zajebava
    if inp.has_key("clientID") and inp["clientID"]:
        clientID = inp["clientID"]

    for message in messages:
        ret = None
        for mpr in sputnik_mapper:
            mtch = re.match(mpr[0], message["channel"])
            if mtch:
                a =  mtch.groupdict()
                fnc = getattr(sputnik, mpr[1])

                if not hasattr(request, "sputnikID"):
                    request.sputnikID = "%s:%s" % (request.session.session_key, clientID)
                    request.clientID  = clientID

                ret = fnc(request, message, **a)
                ret["uid"] = message.get("uid")

        if ret:
            results.append(ret)

    while True:
        v = r.pop("ses:%s:%s:messages" % (request.session.session_key, clientID), tail = False)
        if not v: break

        results.append(simplejson.loads(v))


    import time, decimal
    r.set("ses:%s:last_access" % request.sputnikID, time.time()) 

    # this should not be here!
    _now = time.time() 
    for k in r.keys("ses:*:last_access"):
        tm = r.get(k)

        if  decimal.Decimal("%f" % _now) - tm > 60*2:
            sputnik.removeClient(k[4:-12])

    ret = {"result": True, "messages": results}

    dt = simplejson.dumps(ret)

    return HttpResponse(dt, mimetype="text/json")

