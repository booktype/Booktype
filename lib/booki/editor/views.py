from django.shortcuts import render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import Http404, HttpResponse,HttpResponseRedirect
from django import forms
from django.contrib.auth.models import User

from booki.editor import models

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

@login_required
def edit_book(request, bookid):
    book = models.Book.objects.get(url_title__iexact=bookid)
    chapters = models.Chapter.objects.filter(book=book)


    return render_to_response('editor/edit_book.html', {"book": book, "chapters": chapters, "request": request})

def view_full(request, bookid):
    chapters = []

    book = models.Book.objects.get(url_title__iexact=bookid)

    for chapter in  models.BookToc.objects.filter(book=book).order_by("-weight"):
        if chapter.typeof == 1:
            chapters.append({"type": "chapter",
                             "title": chapter.chapter.title,
                             "content": chapter.chapter.content,
                             "chapter": chapter.chapter})
        else:
            chapters.append({"type": "section",
                             "title": chapter.name})

    return render_to_response('editor/view_full.html', {"book": book, 
                                                        "chapters": chapters, 
                                                        "request": request})



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


    return render_to_response('editor/debug_redis.html', {"request": request, 
                                                          "client_id": client_id,
                                                          "sputnikchannels": sputnikchannels,
                                                          "channel": chnl.items(),
                                                          "users": usrs.items(),
                                                          "sessions": allValues.items(),
                                                          "locks": locks.items()
                                                          })


#def view_editor(request, bookid):
#    return render_to_response('editor/view_editor.html', {"bookid": bookid})


# FRONT PAGE

def view_frontpage(request):
    books = models.Book.objects.all().order_by("title")
    groups = models.BookiGroup.objects.all().order_by("name")

    return render_to_response('editor/view_frontpage.html', {"request": request, 
                                                             "title": "Ovo je neki naslov",
                                                             "books": books,
                                                             "error": request.REQUEST.get("error", "0"), "username" : request.REQUEST.get("username",""), "email":request.REQUEST.get("email",""), "fullname" : request.REQUEST.get("fullname",""),
                                                             "groups": groups})

# GROUPS

def view_group(request, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    books = group.books.all()
    members = group.members.all()

    isMember = request.user in members
    yourBooks = models.Book.objects.filter(owner=request.user)

    return render_to_response('editor/view_group.html', {"request":    request, 
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

#
# front page listings
#
def view_groups(request):
    groups = models.BookiGroup.objects.all()
    return render_to_response('editor/view_groups.html', {"request":    request, "title":      "Ovo je neki naslov", "groups":      groups, })

def view_books(request):
    books = models.Book.objects.all().order_by("title")
    return render_to_response('editor/view_books.html', {"request":    request, "title":      "Ovo je neki naslov", "books":      books, })

def view_people(request):
    people = User.objects.all()
    return render_to_response('editor/view_people.html', {"request":    request, "title":      "Ovo je neki naslov", "people":      people, })

