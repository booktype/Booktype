import sputnik

from django.db import transaction

from booki.utils.log import logBookHistory, logChapterHistory

from booki.editor import models
from booki.editor.views import getVersion


# this couple of functions should go to models.BookVersion

def getTOCForBook(version):
    def _getInfo(chap):
        if chap.chapter:
            return (chap.chapter.id, chap.chapter.title, chap.chapter.url_title, chap.typeof, chap.chapter.status.id)
        else:
            return ('s%s' % chap.id, chap.name, chap.name, chap.typeof)

    return [_getInfo(chap) for chap in list(version.getTOC())]


def getHoldChapters(book_version):
    return [(ch.id, ch.title, ch.url_title, 1, ch.status.id) for ch in book_version.getHoldChapters()]


def getAttachments(book_version):
    import os.path
    import Image

    def _getDimension(att):
        if att.attachment.name.endswith(".jpg"):
            try:
                im = Image.open(att.attachment.name)
                return im.size
            except:
                return (0, 0)
        return None
            

    attachments = [{"id":        att.id, 
                    "dimension": _getDimension(att), 
                    "status":    att.status.id, 
                    "name":      os.path.split(att.attachment.name)[1], 
                    "size":      att.attachment.size} 
                   for att in book_version.getAttachments() if att.attachment]

    return attachments


def remote_init_editor(request, message, bookid, version):
    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)

    ## get chapters

    chapters = getTOCForBook(book_version)
    holdChapters = getHoldChapters(book_version)

    ## get users
    def _getUserName(a):
        if a == request.sputnikID:
            return "<b>%s</b>" % a
        return a

    try:
        users = [_getUserName(m) for m in list(sputnik.smembers("sputnik:channel:%s:channel" % message["channel"]))]
    except:
        users = []

    ## get workflow statuses
    statuses = [(status.id, status.name) for status in models.BookStatus.objects.filter(book=book).order_by("-weight")]

    ## get attachments
    try:
        attachments = getAttachments(book_version)
    except:
        attachments = []

    ## get metadata
    metadata = [{'name': v.name, 'value': v.getValue()} for v in models.Info.objects.filter(book=book)]

    ## notify others
    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, 
                                {"command": "user_joined", 
                                 "user_joined": request.user.username}, 
                                myself = False)

    ## get licenses
    licenses =  [(elem.abbrevation, elem.name) for elem in models.License.objects.all().order_by("name")]

    ## get online users

    try:
        _onlineUsers = sputnik.smembers("sputnik:channel:%s:users" % message["channel"])
    except:
        _onlineUsers = []
        
    if request.user.username not in _onlineUsers:
        try:
            sputnik.sadd("sputnik:channel:%s:users" % message["channel"], request.user.username)
            _onlineUsers.append(request.user.username)
        except:
            pass

        ## get mood message for current user
        ## send mood as seperate message
  
        ## set notifications to other clients
        profile = request.user.get_profile()
        if profile:
            moodMessage = profile.mood;
        else:
            moodMessage = ''

        sputnik.addMessageToChannel(request, 
                                    "/booki/book/%s/%s/" % (bookid, version), 
                                    {"command": "user_add", 
                                     "username": request.user.username,
                                     "mood": moodMessage}
                                    )

    ## get online users and their mood messages

    from django.contrib.auth.models import User

    def _getUser(_user):
        try:
            _u = User.objects.get(username=_user)
            return (_user, _u.get_profile().mood)
        except:
            return None

    onlineUsers = [x for x in [_getUser(x) for x in _onlineUsers] if x]

    # for now, this is one big temp here

    import time, decimal, re
    _now = time.time()
    locks = {}

    try:
        for key in sputnik.rkeys("booki:*:locks:*"):
            lastAccess = sputnik.get(key)

            if type(lastAccess) in [type(' '), type(u' ')]:
                try:
                    lastAccess = decimal.Decimal(lastAccess)
                except:
                    continue

                if lastAccess and decimal.Decimal("%f" % _now) - lastAccess <= 30:
                    m = re.match("booki:(\d+):locks:(\d+):(\w+)", key)
                    if m:
                        if m.group(1) == bookid:
                            locks[m.group(2)] = m.group(3)
    except:
        pass
                
    return {"licenses": licenses, 
            "chapters": chapters, 
            "metadata": metadata, 
            "hold": holdChapters, 
            "users": users, 
            "locks": locks, 
            "statuses": statuses, 
            "attachments": attachments, 
            "onlineUsers": list(onlineUsers)}


def remote_attachments_list(request, message, bookid, version):
    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)

    try:
        attachments = getAttachments(book_version)
    except:
        attachments = []
    
    return {"attachments": attachments}


def remote_chapter_status(request, message, bookid, version):

    if message["status"] == "normal":
        sputnik.rdelete("booki:%s:locks:%s:%s" % (bookid, message["chapterID"], request.user.username))
        
    sputnik.addMessageToChannel(request, "/booki/book/%s/%s/" % (bookid, version), 
                                {"command": "chapter_status", 
                                 "chapterID": message["chapterID"], 
                                 "status": message["status"], 
                                 "username": request.user.username})

    return {}

def remote_change_status(request, message, bookid, version):
    # chapterID
    # statusID

    chapter = models.Chapter.objects.get(id=int(message["chapterID"]))
    status  = models.BookStatus.objects.get(id=int(message["statusID"]))

    chapter.status = status
    try:
        chapter.save()

        sputnik.addMessageToChannel(request, "/booki/book/%s/%s/" % (bookid, version), 
                                    {"command": "change_status", 
                                     "chapterID": message["chapterID"], 
                                     "statusID": int(message["statusID"]), 
                                     "username": request.user.username})
        
        sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, 
                                    {"command": "message_info", 
                                     "from": request.user.username, 
                                     "message": 'User %s has changed status of  chapter "%s" to "%s".' % (request.user.username, chapter.title, status.name)}, myself=True)
    except:
        transaction.rollback()
    else:
        transaction.commit()

    return {}


def remote_chapter_save(request, message, bookid, version):
    # TODO
    # put this outside in common module
    # or maybe even betterm put it in the Model

    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)
    chapter = models.Chapter.objects.get(id=int(message["chapterID"]))

    if message.get("minor", False) != True:
        history = logChapterHistory(chapter = chapter,
                                    content = message["content"],
                                    user = request.user,
                                    comment = message.get("comment", ""),
                                    revision = chapter.revision+1)
        
        logBookHistory(book = chapter.book,
                       version = book_version,
                       chapter = chapter,
                       chapter_history = history,
                       user = request.user,
                       args = {"comment": message.get("comment", ""),
                               "author": message.get("author", ""),
                               "authorcomment": message.get("authorcomment", "")},
                       kind = 'chapter_save')
        
        chapter.revision += 1

    chapter.content = message["content"];

    try:
        chapter.save()

        sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info", 
                                                                    "from": request.user.username, 
                                                                    "message": 'User %s has saved chapter "%s".' % (request.user.username, chapter.title)}, myself=True)
    except:
        transaction.rollback()
    else:
        transaction.commit()

    if not message['continue']:
        sputnik.addMessageToChannel(request, "/booki/book/%s/%s/" % (bookid, version), 
                                    {"command": "chapter_status", 
                                     "chapterID": message["chapterID"], 
                                     "status": "normal", 
                                     "username": request.user.username})
        
        sputnik.rdelete("booki:%s:locks:%s:%s" % (bookid, message["chapterID"], request.user.username))

    return {}

    
def remote_chapter_rename(request, message, bookid, version):
    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)
    chapter = models.Chapter.objects.get(id=int(message["chapterID"]))

    oldTitle = chapter.title
    chapter.title = message["chapter"];

    try:
        chapter.save()
    except:
        transaction.rollback()
    else:
        logBookHistory(book = chapter.book,
                       version = book_version,
                       chapter = chapter,
                       user = request.user,
                       args = {"old": oldTitle, "new": message["chapter"]},
                       kind = "chapter_rename")
        
        sputnik.addMessageToChannel(request, "/chat/%s/" %  bookid, 
                                    {"command": "message_info", 
                                     "from": request.user.username, 
                                     "message": 'User %s has renamed chapter "%s" to "%s".' % (request.user.username, oldTitle, message["chapter"])}, 
                                    myself=True)
        
        sputnik.addMessageToChannel(request, "/booki/book/%s/%s/" % (bookid, version), 
                                    {"command": "chapter_status", 
                                     "chapterID": message["chapterID"], 
                                     "status": "normal", 
                                     "username": request.user.username})
        
        sputnik.addMessageToChannel(request, "/booki/book/%s/%s/" % (bookid, version), 
                                    {"command": "chapter_rename", 
                                     "chapterID": message["chapterID"], 
                                     "chapter": message["chapter"]})
    
        transaction.commit()

    return {}


def remote_chapters_changed(request, message, bookid, version):
    lst = [chap[5:] for chap in message["chapters"]]
    lstHold = [chap[5:] for chap in message["hold"]]

    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)
    weight = len(lst)

    logBookHistory(book = book,
                   version = book_version,
                   user = request.user,
                   kind = "chapter_reorder")

    for chap in lst:
        if chap[0] == 's':
            m =  models.BookToc.objects.get(id__exact=int(chap[1:]))
            m.weight = weight
            m.save()
        else:
            try:
                m =  models.BookToc.objects.get(chapter__id__exact=int(chap))
                m.weight = weight
                m.save()
            except:
                chptr = models.Chapter.objects.get(id__exact=int(chap))
                m = models.BookToc(book = book,
                                   version = book_version,
                                   name = "SOMETHING",
                                   chapter = chptr,
                                   weight = weight,
                                   typeof=1)
                m.save()

        weight -= 1

    if message["kind"] == "remove":
        if type(message["chapter_id"]) == type(u' ') and message["chapter_id"][0] == 's':
            m =  models.BookToc.objects.get(id__exact=message["chapter_id"][1:])
            m.delete()
        else:
            m =  models.BookToc.objects.get(chapter__id__exact=int(message["chapter_id"]))
            m.delete()

#        addMessageToChannel(request, "/chat/%s/%s/" % (projectid, bookid), {"command": "message_info", "from": request.user.username, "message": 'User %s has rearranged chapters.' % request.user.username})

    sputnik.addMessageToChannel(request, "/booki/book/%s/%s/" % (bookid, version), 
                                {"command": "chapters_changed", 
                                 "ids": lst, 
                                 "hold_ids": lstHold, 
                                 "kind": message["kind"], 
                                 "chapter_id": message["chapter_id"]})

    # TODO
    # this should be changed, to check for errors

    transaction.commit()

    return {}


def remote_get_users(request, message, bookid, version):
    res = {}
    def vidi(a):
        if a == request.sputnikID:
            return "!%s!" % a
        return a

    res["users"] = [vidi(m) for m in list(sputnik.smembers("sputnik:channel:%s:channel" % message["channel"]))]
    return res 


def remote_get_chapter(request, message, bookid, version):
    res = {}
    
    chapter = models.Chapter.objects.get(id=int(message["chapterID"]))
    res["title"] = chapter.title
    res["content"] = chapter.content 

    import time

    # set the initial timer for editor
    sputnik.set("booki:%s:locks:%s:%s" % (bookid, message["chapterID"], request.user.username), time.time())

    sputnik.addMessageToChannel(request, "/booki/book/%s/%s/" % (bookid, version), 
                                {"command": "chapter_status", 
                                 "chapterID": message["chapterID"], 
                                 "status": "edit", 
                                 "username": request.user.username})
    
    return res


def remote_book_notification(request, message, bookid, version):
    res = {}
    
    import time

    # rcon.delete(key)
    # set the initial timer for editor

    if request.user.username and request.user.username != '':
        sputnik.set("booki:%s:locks:%s:%s" % (bookid, message["chapterID"], request.user.username), time.time())
        
        if sputnik.get("booki:%s:killlocks:%s:%s" % (bookid, message["chapterID"], request.user.username)) == 1:
            sputnik.rdelete("booki:%s:killlocks:%s:%s" % (bookid, message["chapterID"], request.user.username))
            res = {"kill": "please"}

    return res


def remote_chapter_split(request, message, bookid, version):
    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)


    logBookHistory(book = book,
                   version = book_version,
                   user = request.user,
                   kind = 'chapter_split')
    
    allChapters = []

    try:
        originalChapter = models.Chapter.objects.get(id=int(message["chapterID"]))
    except:
        originalChapter = None
        
    try:
        tocChapter = models.BookToc.objects.get(book=book, chapter__id__exact=message["chapterID"])
    except:
        tocChapter = None

    import datetime
    from django.template.defaultfilters import slugify

    if tocChapter:
        allChapters = [chap for chap in models.BookToc.objects.filter(book=book).order_by("-weight")]
        initialPosition =  len(allChapters)-tocChapter.weight
    else:
        initialPosition = 0

    s = models.BookStatus.objects.filter(book=book).order_by("weight")[0]

    n = 0
    for chap in message["chapters"]:
        chapter = models.Chapter(book = book,
                                 url_title = slugify(chap[0]),
                                 title = chap[0],
                                 status = s,
                                 content = '<h1>%s</h1>%s' % (chap[0], chap[1]),
                                 created = datetime.datetime.now(),
                                 modified = datetime.datetime.now())
        chapter.save()

        if tocChapter:
            m = models.BookToc(book = book,
                               chapter = chapter,
                               name = chap[0],
                               weight = 0,
                               typeof = 1)
            m.save()
            allChapters.insert(1+initialPosition+n, m)

        n += 1

    if originalChapter:
        sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info", "from": request.user.username, "message": 'User %s has split chapter "%s".' % (request.user.username, originalChapter.title)}, myself=True)

        originalChapter.delete()

    if tocChapter:
        tocChapter.delete()

    n = len(allChapters)
    for chap in allChapters:
        try:
            chap.weight = n
            chap.save()
            n -= 1
        except:
            pass

    ## get chapters

    chapters = getTOCForBook(book_version)
    holdChapters =  getHoldChapters(book_version)
        
    sputnik.addMessageToChannel(request, "/booki/book/%s/%s/" % (bookid, version), 
                                {"command": "chapter_split", 
                                 "chapterID": message["chapterID"], 
                                 "chapters": chapters, 
                                 "hold": holdChapters, 
                                 "username": request.user.username}, 
                                myself = True)

    transaction.commit()

    return {}


def remote_create_chapter(request, message, bookid, version):
    import datetime

    # BookVersion treba uzeti

    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)

    from django.template.defaultfilters import slugify

    url_title = slugify(message["chapter"])

    # here i should probably set it to default project status
    s = models.BookStatus.objects.filter(book=book).order_by("weight")[0]

    ch = models.Chapter.objects.filter(book=book, version=book_version, url_title=url_title)

    if len(list(ch)) > 0:
        return {"created": False}

    content = u'<h1>%s</h1>' % message["chapter"]

    chapter = models.Chapter(book = book,
                             version = book_version,
                             url_title = url_title,
                             title = message["chapter"],
                             status = s,
                             content = content,
                             created = datetime.datetime.now(),
                             modified = datetime.datetime.now())

    try:
        chapter.save()
    except:
        transaction.rollback()
        return {"created": False}
    else:
        history = logChapterHistory(chapter = chapter,
                                    content = content,
                                    user = request.user,
                                    comment = message.get("comment", ""),
                                    revision = chapter.revision)
        
        logBookHistory(book = book,
                       version = book_version,
                       chapter = chapter,
                       chapter_history = history,
                       user = request.user,
                       kind = 'chapter_create')

        transaction.commit()
        
    result = (chapter.id, chapter.title, chapter.url_title, 1, s.id)

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info", 
                                                                "from": request.user.username, 
                                                                "message": 'User %s has created new chapter "%s".' % (request.user.username, message["chapter"])}, 
                        myself=True)

    sputnik.addMessageToChannel(request, "/booki/book/%s/%s/" % (bookid, version),  {"command": "chapter_create", "chapter": result}, myself = True)


    return {"created": True}


def remote_publish_book(request, message, bookid, version):
    book = models.Book.objects.get(id=bookid)

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info", 
                                                                "from": request.user.username, 
                                                                "message": '"%s" is being published.' % (book.title, )}, 
                        myself=True)

    import urllib2
    import urllib
    urlPublish = "http://objavi.flossmanuals.net/objavi.cgi"
#        urlPublish = "http://objavi.halo.gen.nz/objavi.cgi"

    publishMode = message.get("publish_mode", "epub")
    destination = "nowhere"

    if message.get("is_archive", False):
        destination = "archive.org"

    args = {'book': book.url_title,
            'project': 'export',
            'mode': publishMode,
            'server': 'booki.flossmanuals.net',
            'destination': destination,
            }

    def _isSet(name):   
        if message.get(name, None):
            args[name] = message.get(name)

    _isSet('title')
    _isSet('license')
    _isSet('isbn')
    _isSet('toc_header')
    _isSet('booksize')
    _isSet('page_width')
    _isSet('page_height')
    _isSet('top_margin')
    _isSet('side_margin')
    _isSet('gutter')
    _isSet('columns')
    _isSet('column_margin')
    _isSet('grey_scale')
    _isSet('css')

    data = urllib.urlencode(args)

    req = urllib2.Request(urlPublish, data)
    f = urllib2.urlopen(req)

#    f = urllib2.urlopen("%s?book=%s&project=export&mode=%s&server=booki.flossmanuals.net&destination=%s" % (urlPublish, book.url_title, publishMode, destination))
    ta = f.read()
    lst = ta.split("\n")
    dta, dtas3 = "", ""

    if len(lst) > 0:
        dta = lst[0]

        if len(lst) > 1:
            dtas3 = lst[1]

    return {"dtaall": ta, "dta": dta, "dtas3": dtas3}
            

def remote_create_section(request, message, bookid, version):
    import datetime

    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)

    ch = models.BookToc.objects.filter(book=book, 
                                       version=book_version,
                                       name=message['chapter'],
                                       typeof=0)

    if len(list(ch)) > 0:
        return {"created": False}
    
    c = models.BookToc(book = book,
                       version = book_version,
                       name = message["chapter"],
                       chapter = None,
                       weight = 0,
                       typeof=0)

    result = True

    try:
        c.save()
    except:
        result = False
        transaction.rollback()
    else:
        logBookHistory(book = book,
                       version = book_version,
                       user = request.user,
                       args = {"title": message["chapter"]},
                       kind = 'section_create')
        transaction.commit()

        result = ("s%s" % c.id, c.name, None, c.typeof)
        
        sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info", 
                                                                    "from": request.user.username, 
                                                                    "message": 'User %s has created new section "%s".' % (request.user.username, message["chapter"])}, 
                                    myself=True)
        
        sputnik.addMessageToChannel(request, "/booki/book/%s/%s/" %  (bookid, version), 
                                    {"command": "chapter_create", 
                                     "chapter": result, 
                                     "typeof": c.typeof}, 
                                    myself = True)
        
    return {"created": result}


def remote_get_history(request, message, bookid, version):
    import datetime
    from booki.editor.common import parseJSON

    book = models.Book.objects.get(id=bookid)

    book_history = models.BookHistory.objects.filter(book=book).order_by("-modified")

    temp = {0: 'unknown',
            1: 'create',
            2: 'save',
            3: 'rename',
            4: 'reorder',
            5: 'split',
            6: 'section create',
            10: 'book create',
            11: 'minor',
            12: 'major',
            13: 'attachment'}


    history = []
    for entry in book_history:
        if entry.kind in [1, 2, 3] and entry.chapter:
            history.append({"chapter": entry.chapter.title, 
                            "chapter_url": entry.chapter.url_title, 
                            "modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"), 
                            "description": entry.args, 
                            "user": entry.user.username, 
                            "kind": temp.get(entry.kind,'')})
        elif entry.kind == 2 and entry.chapter:
            history.append({"chapter": entry.chapter.title, 
                            "chapter_url": entry.chapter.url_title, 
                            "chapter_history": entry.chapter_history.id, 
                            "modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"), 
                            "description": entry.args, 
                            "user": entry.user.username, 
                            "kind": temp.get(entry.kind,'')})
        elif entry.kind in [11, 12]:
            history.append({"modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"), 
                            "version": parseJSON(entry.args), 
                            "user": entry.user.username, 
                            "kind": temp.get(entry.kind,'')})
        elif entry.kind in [13]:
            history.append({"modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"), 
                            "args": parseJSON(entry.args), 
                            "user": entry.user.username, 
                            "kind": temp.get(entry.kind,'')})
        else:
            history.append({"modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"), 
                            "description": entry.args, 
                            "user": entry.user.username, 
                            "kind": temp.get(entry.kind,'')})

    return {"history": history}


def remote_get_chapter_history(request, message, bookid, version):
    import datetime
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    chapter_history = models.ChapterHistory.objects.filter(chapter__book=book, chapter__url_title=message["chapter"]).order_by("-modified")

    history = []

    for entry in chapter_history:
        history.append({"chapter": entry.chapter.title, 
                        "chapter_url": entry.chapter.url_title, 
                        "modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"), 
                        "user": entry.user.username, 
                        "revision": entry.revision,
                        "comment": entry.comment})

    return {"history": history}

def remote_revert_revision(request, message, bookid, version):
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    chapter = models.Chapter.objects.get(version=book_ver, url_title=message["chapter"])

    revision = models.ChapterHistory.objects.get(revision=message["revision"], chapter__url_title=message["chapter"], chapter__version=book_ver.id)

    # TODO
    # does chapter history really needs to keep content or it can only keep reference to chapter

    history = logChapterHistory(chapter = chapter,
                      content = revision.content,
                      user = request.user,
                      comment = "Reverted to revision %s." % message["revision"],
                      revision = chapter.revision+1)

    logBookHistory(book = book,
                   version = book_ver, 
                   chapter = chapter,
                   chapter_history = history,
                   user = request.user,
                   args = {},
                   kind = 'chapter_save')
    
    chapter.revision += 1
    chapter.content = revision.content;

    try:
        chapter.save()
    except:
        transaction.rollback()
    else:
        transaction.commit()

        sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, 
                                    {"command": "message_info", 
                                     "from": request.user.username, 
                                     "message": 'User %s has reverted chapter "%s" to revision %s.' % (request.user.username, chapter.title, message["revision"])}, myself=True)
        
    return {}



def remote_get_chapter_revision(request, message, bookid, version):
    import datetime
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)

    try:
        revision = models.ChapterHistory.objects.get(chapter__book=book, chapter__url_title=message["chapter"], revision=message["revision"])

        return {"chapter": revision.chapter.title, 
                "chapter_url": revision.chapter.url_title, 
                "modified": revision.modified.strftime("%d.%m.%Y %H:%M:%S"), 
                "user": revision.user.username, 
                "revision": revision.revision,
                "version": '%d.%d' % (revision.chapter.version.major, revision.chapter.version.minor),
                "content": revision.content,
                "comment": revision.comment}
    except:
        return {}


def remote_get_notes(request, message, bookid, version):
    import datetime

    book = models.Book.objects.get(id=bookid)

    book_notes = models.BookNotes.objects.filter(book=book)

    notes = []
    for entry in book_notes:
        notes.append({"notes": entry.notes})

    return {"notes": notes}

def remote_notes_save(request, message, bookid, version):
    book = models.Book.objects.get(id=bookid)
    book_notes = models.BookNotes.objects.filter(book=book)
    notes = message.get("notes")
    book_notes_obj = None

    if len(book_notes) == 0:
        book_notes_obj = models.BookNotes( book = book , notes = notes)
    else:
        book_notes_obj = book_notes[0]
	book_notes_obj.notes = notes 


    try:
        book_notes_obj.save()
    except:
        transaction.rollback()
    else:
        sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info", 
                                                                    "from": request.user.username, 
                                                                    "message": 'User %s has saved notes for book "%s".' % (request.user.username, book.title)}, myself=True)
        transaction.commit()

    return {}

 

def remote_unlock_chapter(request, message, bookid, version):
    import re

    for key in sputnik.rkeys("booki:%s:locks:%s:*" % (bookid, message["chapterID"])):
        m = re.match("booki:(\d+):locks:(\d+):(\w+)", key)

        if m:
            sputnik.set("booki:%s:killlocks:%s:%s" % (bookid, message["chapterID"], m.group(3)), 1)

    return {}


def remote_get_versions(request, message, bookid, version):
    book = models.Book.objects.get(id=bookid)

    book_versions = [{"major": v.major, 
                      "minor": v.minor, 
                      "name": v.name, 
                      "description": v.description, 
                      "created": str(v.created.strftime('%a, %d %b %Y %H:%M:%S GMT'))} 
                     for v in models.BookVersion.objects.filter(book=book).order_by("-created")]

    return {"versions": book_versions}



# put this outside of this module
def create_new_version(book, book_ver, message, major, minor):#request, message, bookid, version):
    new_version = models.BookVersion(book=book, 
                                     major=major,
                                     minor=minor,
                                     name=message.get("name", ""),
                                     description=message.get("description", ""))
    new_version.save()

    for toc in book_ver.getTOC():
        nchap = None

        if toc.chapter:
            chap = toc.chapter

            nchap = models.Chapter(version=new_version,
                                  book=book, # this should be removed
                                  url_title=chap.url_title,
                                  title=chap.title,
                                  status=chap.status,
                                  revision=chap.revision,
                                  content=chap.content)
            nchap.save()
            
        ntoc = models.BookToc(version=new_version,
                              book=book, # this should be removed
                              name=toc.name,
                              chapter=nchap,
                              weight=toc.weight,
                              typeof=toc.typeof)
        ntoc.save()
    
    # hold chapters

    for chap in book_ver.getHoldChapters():
        c = models.Chapter(version=new_version,
                           book=book, # this should be removed
                           url_title=chap.url_title,
                           title=chap.title,
                           status=chap.status,
                           revision=chap.revision,
                           content=chap.content)
        c.save()

    for att in book_ver.getAttachments():
        a = models.Attachment(version = new_version,
                              book = book,
                              status = att.status)
        a.attachment.save(att.getName(), att.attachment, save = False)
        a.save()
                              
                           
    book.version = new_version
    book.save()

    # probably it would be smart to throw exception from here

    return new_version


def remote_create_major_version(request, message, bookid, version):
    from booki.editor.views import getVersion
    
    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    try:
        new_version = create_new_version(book, book_ver, message, book_ver.major+1, 0)
    except:
        transaction.rollback()
    else:
        logBookHistory(book = book,
                       version = new_version, 
                       chapter = None,
                       chapter_history = None,
                       user = request.user,
                       args = {"version": new_version.getVersion()},
                       kind = 'major_version')
        transaction.commit()

    return {"version": new_version.getVersion()}

def remote_create_minor_version(request, message, bookid, version):
    from booki.editor.views import getVersion
    
    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    try:
        new_version = create_new_version(book, book_ver, message, book_ver.major, book_ver.minor+1)
    except:
        transaction.rollback()

        return {"result": False}
    else:
        logBookHistory(book = book,
                       version = new_version,
                       chapter = None,
                       chapter_history = None,
                       user = request.user,
                       args = {"version": new_version.getVersion()},
                       kind = 'minor_version')
        transaction.commit()

        return {"version": new_version.getVersion()}


def remote_chapter_diff(request, message, bookid, version):
    import datetime
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)

    revision1 = models.ChapterHistory.objects.get(chapter__book=book, chapter__url_title=message["chapter"], revision=message["revision1"])
    revision2 = models.ChapterHistory.objects.get(chapter__book=book, chapter__url_title=message["chapter"], revision=message["revision2"])


    import difflib

    output = []

#    for line in difflib.unified_diff(revision1.content.splitlines(1), revision2.content.splitlines(1)):
    for line in difflib.ndiff(revision1.content.splitlines(1), revision2.content.splitlines(1)):
        output.append(line)
    return {"output": '\n'.join(output)}


