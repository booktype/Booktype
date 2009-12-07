from django.shortcuts import render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from django.http import Http404, HttpResponse

from django import forms

from booki.editor import models

import logging

# BOOK

def view_export(request, project, edition):

    if edition == "None":
        edition = project

    project = models.Project.objects.get(url_name__iexact=project)

    book = models.Book.objects.get(project=project, url_title__iexact=edition)

    response = HttpResponse(mimetype='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % book.url_title

    # this is not good
    # should not do so much read/write in the memory

    from booki.editor import common
    
    fileName = common.exportBook(book)

    response.write(open(fileName, 'rb').read())

    import os
    os.unlink(fileName)

    return response

def edit_book(request, project, edition):
    project = models.Project.objects.get(url_name__iexact=project)
    book = models.Book.objects.get(project=project, url_title__iexact=edition)
    chapters = models.Chapter.objects.filter(book=book)


    return render_to_response('editor/edit_book.html', {"project": project, "book": book, "chapters": chapters, "request": request})

def view_book(request, project, edition):
    proj = models.Project.objects.get(url_name__iexact=project)
    # ovaj tu neshto zeza
    book = models.Book.objects.get(project=proj, url_title__iexact=edition)

    chapters = []
    for chapter in  models.BookToc.objects.filter(book=book).order_by("-weight"):
        if chapter.chapter:
            chapters.append({"url_title": chapter.chapter.url_title,
                             "name": chapter.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chapter.name})
        

    return render_to_response('editor/view_book.html', {"project": proj, "book": book, "chapters": chapters, "request": request})

def view_chapter(request, project, edition, chapter):
    proj = models.Project.objects.get(url_name__iexact=project)
    book = models.Book.objects.get(project=proj, url_title__iexact=edition)

    chapters = []
    for chap in  models.BookToc.objects.filter(book=book).order_by("-weight"):
        if chap.chapter:
            chapters.append({"url_title": chap.chapter.url_title,
                             "name": chap.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chap.name})

    content = models.Chapter.objects.get(book = book, url_title = chapter)

    return render_to_response('editor/view_chapter.html', {"chapter": chapter, "project": proj, "book": book, "chapters": chapters, "request": request, "content": content})


# PROJECT

def view_project(request, project):
    books = list(models.Book.objects.filter(project__url_name__iexact=project))
    return render_to_response('editor/view_project.html', {"project": project, "books": books})

def view_attachment(request, project, edition, attachment):
    from booki import settings
    from django.views import static

    #project = models.Project.objects.get(url_name__iexact=project)
    #book = models.Book.objects.get(project=project, url_title__iexact=edition)

    path = attachment
    document_root = '%s/static/%s/%s/' % (settings.STATIC_DOC_ROOT, project, edition)

    return static.serve(request, path, document_root)

def thumbnail_attachment(request, project, edition, attachment):
    from booki import settings
    from django.views import static

    path = attachment
    document_root = '%s/static/%s/%s/%s' % (settings.STATIC_DOC_ROOT, project, edition, path)

    # should have one  "broken image" in case of error
    import Image
    im = Image.open(document_root)
    im.thumbnail((200, 200), Image.ANTIALIAS)

    response = HttpResponse(mimetype='image/jpeg')
    im.save(response, "jpeg")
    return  response



def view_editor(request, project):
    return render_to_response('editor/view_editor.html', {"project": project})


# FRONT PAGE

def view_frontpage(request):
    return render_to_response('editor/view_frontpage.html', {"request": request, "title": "Ovo je neki naslov"})

# UPLOAD ATTACHMENT

def upload_attachment(request, project, edition):
    proj = models.Project.objects.get(url_name__iexact=project)
    book = models.Book.objects.get(project=proj, url_title__iexact=edition)

    stat = models.ProjectStatus.objects.filter(project = proj)[0]

    for name, fileData in request.FILES.items():
        att = models.Attachment(book = book,
                                status = stat)

        att.attachment.save(request.FILES[name].name, fileData, save = False)
        att.save()

        # maybe check file name now and save with new name

    return HttpResponse('<html><body><script> parent.closeAttachmentUpload(); </script></body></html>')


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
    import simplejson, re, sputnik

    inp =  request.POST

    results = []

    clientID = None
    messages = simplejson.loads(inp["messages"])

    # this should be changed
    r = redis.Redis()
    r.connect()

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

