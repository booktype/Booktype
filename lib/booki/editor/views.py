from django.shortcuts import render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from django.http import Http404, HttpResponse

from django import forms

from booki.editor import models

from django.http import Http404, HttpResponse, HttpResponseRedirect


import logging

# BOOK

def view_export(request, bookid):

    book = models.Book.objects.get(url_title__iexact=bookid)

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

def edit_book(request, bookid):
    book = models.Book.objects.get(url_title__iexact=bookid)
    chapters = models.Chapter.objects.filter(book=book)


    return render_to_response('editor/edit_book.html', {"book": book, "chapters": chapters, "request": request})

def view_book(request, bookid):
    book = models.Book.objects.get(url_title__iexact=bookid)

    chapters = []
    for chapter in  models.BookToc.objects.filter(book=book).order_by("-weight"):
        if chapter.typeof == 1:
            chapters.append({"url_title": chapter.chapter.url_title,
                             "name": chapter.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chapter.name})
        

    return render_to_response('editor/view_book.html', {"book": book, "chapters": chapters, "request": request})

def view_chapter(request, bookid, chapter):
    book = models.Book.objects.get(url_title__iexact=bookid)

    chapters = []
    for chap in  models.BookToc.objects.filter(book=book).order_by("-weight"):
        if chap.typeof == 1:
            chapters.append({"url_title": chap.chapter.url_title,
                             "name": chap.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chap.name})

    content = models.Chapter.objects.get(book = book, url_title = chapter)

    return render_to_response('editor/view_chapter.html', {"chapter": chapter, "book": book, "chapters": chapters, "request": request, "content": content})


# PROJECT

def view_attachment(request, bookid, attachment):
    from booki import settings
    from django.views import static

    path = attachment
    document_root = '%s/static/%s/' % (settings.STATIC_DOC_ROOT, bookid)

    return static.serve(request, path, document_root)

def thumbnail_attachment(request, bookid, attachment):
    from booki import settings
    from django.views import static

    path = attachment
    document_root = '%s/static/%s/%s' % (settings.STATIC_DOC_ROOT, bookid, path)

    # should have one  "broken image" in case of error
    import Image
    im = Image.open(document_root)
    im.thumbnail((200, 200), Image.ANTIALIAS)

    response = HttpResponse(mimetype='image/jpeg')
    im.save(response, "jpeg")
    return  response



#def view_editor(request, bookid):
#    return render_to_response('editor/view_editor.html', {"bookid": bookid})


# FRONT PAGE

def view_frontpage(request):
    books = models.Book.objects.all().order_by("title")
    groups = models.BookiGroup.objects.all().order_by("name")

    return render_to_response('editor/view_frontpage.html', {"request": request, 
                                                             "title": "Ovo je neki naslov",
                                                             "books": books,
                                                             "groups": groups})

# GROUPS

def view_group(request, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    books = group.books.all()
    members = group.members.all()

    isMember = request.user in members
    yourBooks = models.Book.objects.filter(owner=request.user)

    return render_to_response('editor/view_group.html', {"request": request, 
                                                         "title": "Ovo je neki naslov",
                                                         "group": group,
                                                         "books": books,
                                                         "your_books": yourBooks,
                                                         "members": members,
                                                         "is_member": isMember})

def join_group(request, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    group.members.add(request.user)

    return HttpResponseRedirect("/groups/%s/" % group.url_name)


def remove_group(request, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    group.members.remove(request.user)

    return HttpResponseRedirect("/groups/%s/" % group.url_name)

def add_book(request, groupid):
    print "---------"
    print request.POST["book"]
    book = models.Book.objects.get(url_title=request.POST["book"])

    group = models.BookiGroup.objects.get(url_name=groupid)
    group.books.add(book)

    return HttpResponseRedirect("/groups/%s/" % group.url_name)

def remove_book(request, groupid):
    book = models.Book.objects.get(url_title=request.GET["book"])

    group = models.BookiGroup.objects.get(url_name=groupid)
    group.books.remove(book)

    return HttpResponseRedirect("/groups/%s/" % group.url_name)


# UPLOAD ATTACHMENT

def upload_attachment(request, bookid):
    book = models.Book.objects.get(url_title__iexact=bookid)
    stat = models.BookStatus.objects.filter(book = book)[0]

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
  (r'^/booki/book/(?P<bookid>\d+)/$', 'booki_book'),
  (r'^/chat/(?P<bookid>\d+)/$', 'booki_chat')
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
    try:
        r.set("ses:%s:last_access" % request.sputnikID, time.time())
    except:
        pass

    # this should not be here!
    _now = time.time() 
    for k in r.keys("ses:*:last_access"):
        tm = r.get(k)
        print k,  decimal.Decimal("%f" % _now) - tm 
        if  decimal.Decimal("%f" % _now) - tm > 60*2:
            sputnik.removeClient(request, k[4:-12])

    ret = {"result": True, "messages": results}

    dt = simplejson.dumps(ret)

    return HttpResponse(dt, mimetype="text/json")

