
from lxml import etree, html

import sputnik

from django.db import transaction
from django.db.models import Q

from booki.utils.log import logBookHistory, logChapterHistory, printStack

from booki.editor import models
from booki.editor.views import getVersion
from booki.utils import security

from django.conf import settings

try:
    OBJAVI_URL = settings.OBJAVI_URL
except AttributeError:
    OBJAVI_URL = "http://objavi.flossmanuals.net/objavi.cgi"

try:
    THIS_BOOKI_SERVER = settings.THIS_BOOKI_SERVER
except AttributeError:
    import os
    THIS_BOOKI_SERVER = os.environ.get('HTTP_HOST', 'booki.flossmanuals.net')


# this couple of functions should go to models.BookVersion
def getTOCForBook(version):
    results = []
    for chap in version.getTOC():
        # is it a section or chapter?
        if chap.chapter:
            results.append((chap.chapter.id,
                            chap.chapter.title,
                            chap.chapter.url_title,
                            chap.typeof,
                            chap.chapter.status.id))
        else:
            results.append(('s%s' % chap.id, chap.name, chap.name, chap.typeof))
    return results



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
                    "created":   str(att.created.strftime("%d.%m.%Y %H:%M:%S")),
                    "size":      att.attachment.size} 
                   for att in book_version.getAttachments().order_by("attachment") if att.attachment]

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

def remote_attachments_delete(request, message, bookid, version):
    # TODO: must check security
    book = models.Book.objects.get(id=bookid)
    bookSecurity = security.getUserSecurityForBook(request.user, book)
    
    if bookSecurity.isAdmin():
        for att_id in message['attachments']:
            att = models.Attachment.objects.get(pk=att_id)
            att.delete()
            
        transaction.commit()

        return {"result": True}

    return {"result": False}

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

    # fire the signal
    import booki.editor.signals
    booki.editor.signals.chapter_modified.send(sender = book_version, chapter = chapter, user = request.user)

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
    res["current_revision"] = chapter.revision

    if message.get("revisions", False):
        res["revisions"] = [x.revision for x in models.ChapterHistory.objects.filter(chapter=chapter).order_by("revision")]


    if message.get("revision", chapter.revision) != chapter.revision:
        ch = models.ChapterHistory.objects.get(chapter=chapter, revision=message.get("revision"))
        res["content"] = ch.content


    if not message.get("lock", True):
        return res

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

        if '%s' % sputnik.get("booki:%s:killlocks:%s:%s" % (bookid, message["chapterID"], request.user.username)) == '1':
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
        # this should be solved in better way
        # should have createChapter in booki.utils.book module

        toc_items = len(book_version.getTOC())+1

        for itm in models.BookToc.objects.filter(version = book_version, book = book):
            itm.weight = toc_items
            itm.save()

            toc_items -= 1
            
        tc = models.BookToc(version = book_version,
                            book = book,
                            name = message["chapter"],
                            chapter = chapter,
                            weight = 1,
                            typeof = 1)

        try:
            tc.save()
        except:
            transaction.rollback()
            return {"created": False}

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

def copy_attachment(attachment, target_book):
    import os.path

    att = models.Attachment(book = target_book,
                            version = target_book.version,
                            status = target_book.status)

    att.attachment.save(os.path.basename(attachment.attachment.name), attachment.attachment, save=False)
    att.save()
    return att

def remote_clone_chapter(request, message, bookid, version):
    import datetime

    # BookVersion treba uzeti

    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)
    
    source_book = models.Book.objects.get(url_title=message["book"])
    source_book_version = source_book.version
    source_url_title = message["chapter"]
    source_chapter = models.Chapter.objects.get(book=source_book, version=source_book_version, url_title=source_url_title)

    title = message.get("renameTitle", "")
    if title.strip():
        from django.template.defaultfilters import slugify
        url_title = slugify(title)
    else:
        title = source_chapter.title
        url_title = source_url_title

    # here i should probably set it to default project status
    s = models.BookStatus.objects.filter(book=book).order_by("weight")[0]

    ch = models.Chapter.objects.filter(book=book, version=book_version, url_title=url_title)

    if len(list(ch)) > 0:
        return {"created": False, "errormsg": "chapter already exists"}

    chapter = models.Chapter(book = book,
                             version = book_version,
                             url_title = url_title,
                             title = title,
                             status = s,
                             content = source_chapter.content,
                             created = datetime.datetime.now(),
                             modified = datetime.datetime.now())

    try:
        chapter.save()
    except:
        transaction.rollback()
        return {"created": False, "errormsg": "chapter.save() failed"}
    else:
        # this should be solved in better way
        # should have createChapter in booki.utils.book module

        toc_items = len(book_version.getTOC())+1

        for itm in models.BookToc.objects.filter(version = book_version, book = book):
            itm.weight = toc_items
            itm.save()

            toc_items -= 1
            
        tc = models.BookToc(version = book_version,
                            book = book,
                            name = title,
                            chapter = chapter,
                            weight = 1,
                            typeof = 1)

        try:
            tc.save()
        except:
            transaction.rollback()
            return {"created": False, "errormsg": "tc.save() failed"}

        try:
            history = logChapterHistory(chapter = chapter,
                                        content = chapter.content,
                                        user = request.user,
                                        comment = message.get("comment", ""),
                                        revision = chapter.revision)
        except:
            transaction.rollback()
            import traceback
            return {"created": False, "errormsg": "logChapterHistory failed", "stacktrace": traceback.format_exc()}

        try:
            logBookHistory(book = book,
                           version = book_version,
                           chapter = chapter,
                           chapter_history = history,
                           user = request.user,
                           kind = 'chapter_clone')
        except:
            transaction.rollback()
            return {"created": False, "errormsg": "logBookHistory failed"}

        transaction.commit()

    try:
        attachments = source_book_version.getAttachments()
        attachmentnames = dict([(att.getName(), att) for att in attachments])

        target_attachments = book_version.getAttachments()
        target_attachmentnames = dict([(att.getName(), att) 
                                       for att in target_attachments])

        # keep track of already copied source and destination names
        name2copy = {}

        tree = html.document_fromstring(chapter.content)

        for e in tree.iter():
            src = e.get('src')
            if src is not None:
                dirname, rest = src.split('/', 1)
                if dirname ==  "static":
                    name = src.split('/',1)[1]
                    att = attachmentnames.get(name)
                    if att and not name in name2copy:
                        new_att = copy_attachment(att, book)
                        name2copy[name] = new_att.getName()
                    if att and name in name2copy:
                        e.set('src', "static/"+name2copy[name])

        chapter.content = etree.tostring(tree, encoding='UTF-8', method='html')
        chapter.save()
        transaction.commit()
    except:
        printStack()
        transaction.rollback()

    result = (chapter.id, chapter.title, chapter.url_title, 1, s.id)

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info",
                                                                "from": request.user.username,
                                                                "message": 'User %s has cloned chapter "%s" from book "%s".' % (request.user.username, chapter.title, source_book.title)},
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

    publishMode = message.get("publish_mode", "epub")
    destination = "nowhere"

    if message.get("is_archive", False):
        destination = "archive.org"

    args = {'book': book.url_title.encode('utf8'),
            'project': 'export',
            'mode': publishMode,
            'server': THIS_BOOKI_SERVER,
            'destination': destination,
            'max-age': 0,
            }

    def _isSet(name):
        if message.get(name, None):
            if name == 'grey_scale':
                args['grey_scale'] = 'yes'
            else:
                if type(message.get(name)) == type(u' '):
                    args[name] = message.get(name).encode('utf8')
                else:
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

    req = urllib2.Request(OBJAVI_URL, data)
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

    page = int(message.get("page", 1))

    book_history = models.BookHistory.objects.filter(book=book).order_by("-modified")[(page-1)*50:(page-1)*50+50]

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

    if request.user.username == 'booki':
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


def color_me(l, rgb, pos):
    if pos:
        t1 = l.find('>', pos[0]) 
        t2 = l.find('<', pos[0])

        if (t1 == t2) or (t1 > t2 and t2 != -1):
            out  = l[:pos[0]]

            out += '<span style="background-color: yellow">'+color_me(l[pos[0]:pos[1]], rgb, None)+'</span>'
            out += l[pos[1]:]
        else:
            out = l
        return out

    out = '<span style="%s">' % rgb

    n = 0
    m = 0
    while True:
        n = l.find('<', n)

        if n == -1: # no more tags
            out += l[m:n]
            break
        else: 
            if l[n+1] == '/': # tag ending
                # closed tag
                out += l[m:n]

                j = l.find('>', n)+1
                tag = l[n:j]
                out += '</span>'+tag
                n = j
            else: # tag start
                out += l[m:n]

                j = l.find('>', n)+1

                if j == 0:
                    out = l[n:]
                    n = len(l)
                else:
                    tag = l[n:j]
 
                    if not tag.replace(' ','').replace('/','').lower() in ['<br>', '<hr>']:
                        if n != 0:
                            out += '</span>'

                        out += tag+'<span style="%s">' % rgb
                    else:
                        out += tag

                    n = j
        m = n
            

    out += l[n:]+'</span>'

    return out

def remote_chapter_diff(request, message, bookid, version):
    import datetime
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)

    revision1 = models.ChapterHistory.objects.get(chapter__book=book, chapter__url_title=message["chapter"], revision=message["revision1"])
    revision2 = models.ChapterHistory.objects.get(chapter__book=book, chapter__url_title=message["chapter"], revision=message["revision2"])


    import difflib

    output = []

#    from lxml import etree
#    content1 = unicode(etree.tostring(etree.fromstring(u'<html>'+revision1.content.replace('</p>', '</p>\n').replace('. ', '. \n')+u'</html>'), method="text", encoding='UTF-8'), 'utf8').splitlines(1)
#    content2 = unicode(etree.tostring(etree.fromstring(u'<html>'+revision2.content.replace('</p>', '</p>\n').replace('. ', '. \n')+u'</html>'), method="text", encoding='UTF-8'), 'utf8').splitlines(1)

    content1 = revision1.content.replace('</p>', '</p>\n').replace('. ', '. \n').splitlines(1)
    content2 = revision2.content.replace('</p>', '</p>\n').replace('. ', '. \n').splitlines(1)

    lns = [line for line in difflib.ndiff(content1, content2)]

    n = 0
    minus_pos = None
    plus_pos = None

    def my_find(s, wh, x = 0):
        n = x

        for ch in s[n:]:
            if ch in wh:
                return n
            n += 1

        return -1

            

    while True:
        if n >= len(lns): 
            break
    
        line = lns[n]

        if line[:2] == '+ ':
            if n+1 < len(lns) and lns[n+1][0] == '?':
                lns[n+1] += lns[n+1] + ' '

                x = my_find(lns[n+1][2:], '+?^-')
#                x = my_find(lns[n+1][2:], '+?-')
                y = lns[n+1][2:].find(' ', x)-2

                plus_pos = (x, y)
            else:
                plus_pos = None

            output.append('<div style="background-color: yellow">'+color_me(line[2:], 'background-color: green;', plus_pos)+'</div>')
        elif line[:2] == '- ':
            if n+1 < len(lns) and lns[n+1][0] == '?':
                lns[n+1] += lns[n+1] + ' '

                x = my_find(lns[n+1][2:], '+?^-')
#                x = my_find(lns[n+1][2:], '+?-')
                y = lns[n+1][2:].find(' ', x)-2

                minus_pos = (x, y)
            else:
                minus_pos = None

            output.append('<div style="background-color: orange">'+color_me(line[2:], 'background-color: red;', minus_pos)+'</div>')
        elif line[:2] == '  ':
            output.append(line[2:])

        n += 1

    return {"output": '\n'.join(output)}

def remote_chapter_diff_parallel(request, message, bookid, version):
    import datetime
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)

    revision1 = models.ChapterHistory.objects.get(chapter__book=book, chapter__url_title=message["chapter"], revision=message["revision1"])
    revision2 = models.ChapterHistory.objects.get(chapter__book=book, chapter__url_title=message["chapter"], revision=message["revision2"])


    import difflib

    output = []

    output_left = '<td valign="top">'
    output_right = '<td valign="top">'
    
    import re
    content1 = re.sub('<[^<]+?>', '', revision1.content.replace('<p>', '\n<p>').replace('. ', '. \n')).splitlines(1)
    content2 = re.sub('<[^<]+?>', '', revision2.content.replace('<p>', '\n<p>').replace('. ', '. \n')).splitlines(1)

    lns = [line for line in difflib.ndiff(content1, content2)]

    n = 0
    minus_pos = None
    plus_pos = None

    def my_find(s, wh, x = 0):
        n = x

        for ch in s[n:]:
            if ch in wh:
                return n
            n += 1

        return -1

    
    while True:
        if n >= len(lns): 
            break
    
        line = lns[n]

        if line[:2] == '+ ':
            if n+1 < len(lns) and lns[n+1][0] == '?':
                lns[n+1] += lns[n+1] + ' '

                x = my_find(lns[n+1][2:], '+?^-')
                y = lns[n+1][2:].find(' ', x)-2

                plus_pos = (x, y)
            else:
                plus_pos = None

            output_right +=  '<div style="background-color: orange;">'+color_me(line[2:], 'background-color: green;', plus_pos)+'</div>'
            output.append('<tr>'+output_left+'</td>'+output_right+'</td></tr>')
            output_left = output_right = '<td valign="top">'
        elif line[:2] == '- ':
            if n+1 < len(lns) and lns[n+1][0] == '?':
                lns[n+1] += lns[n+1] + ' '

                x = my_find(lns[n+1][2:], '+?^-')
                y = lns[n+1][2:].find(' ', x)-2

                minus_pos = (x, y)
            else:
                minus_pos = None

            output.append('<tr>'+output_left+'</td>'+output_right+'</td></tr>')

            output_left = output_right = '<td valign="top">'
            output_left +=  '<div style="background-color: orange">'+color_me(line[2:], 'background-color: red;', minus_pos)+'</div>'
        elif line[:2] == '  ':
            if line[2:].strip() != '':
                output_left  += line[2:]+'<br/><br/>'
                output_right += line[2:]+'<br/><br/>'

        n += 1

    output.append('<tr>'+output_left+'</td>'+output_right+'</td></tr>')
    
    info = '''<div style="padding-bottom: 5px"><span style="width: 10px; height: 10px; background-color: orange; display: inline-block;"></span> Changed <span style="width: 10px; height: 10px; background-color: green; display: inline-block;"></span> Added <span style="width: 10px; height: 10px; background-color: red; display: inline-block;"></span> Deleted </div>'''
    
    return {"output": info+'<table border="0" width="100%%"><tr><td width="50%%"><div style="border-bottom: 1px solid #c0c0c0; font-weight: bold;">Revision: '+message["revision1"]+'</div></td><td width="50%%"><div style="border-bottom: 1px solid #c0c0c0; font-weight: bold">Revision: '+message["revision2"]+'</div></td></tr>\n'.join(output)+'</table>\n'}


def remote_settings_options(request, message, bookid, version):
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    licenses = [(lic.abbrevation, lic.name)  for lic in models.License.objects.all().order_by("name") if lic]
    languages = [(lic.abbrevation, lic.name) for lic in models.Language.objects.all().order_by("name") if lic] + [('unknown', 'Unknown')]
    
    current_license = getattr(book.license, "abbrevation","")
    current_language = getattr(book.language, "abbrevation", "unknown")

    # get rtl
    try:
        rtl = models.Info.objects.get(book=book, name='{http://booki.cc/}dir', kind=0).getValue()
    except models.Info.DoesNotExist:
        rtl = "LTR"

    transaction.commit()

    return {"licenses": licenses, 
            "current_licence": current_license,
            "languages": languages,
            "current_language": current_language,
            "rtl": rtl
            }

def remote_license_save(request, message, bookid, version):
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)
    #book_ver = getVersion(book, version)

    lic = models.License.objects.filter(abbrevation=message["license"])[0]
    book.license = lic
    book.save()

    transaction.commit()

    return {"status": 1}

def remote_license_attributions(request, message, bookid, version):
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    from django.contrib.auth.models import User

    # not so cool idea
    excl = [a.user.username for a in models.AttributionExclude.objects.filter(book = book)]
    users = [(u['user__username'], u['user__first_name']) for u in models.ChapterHistory.objects.filter(chapter__version__book=book).values("user", "user__username", "user__first_name").distinct()  if u['user__username'] not in excl]
    users_exclude = [(u.user.username, u.user.first_name) for u in models.AttributionExclude.objects.filter(book = book).order_by("user__username")]


    transaction.commit()

    return {"users": users,
            "users_exclude": users_exclude }

def remote_license_attributions_save(request, message, bookid, version):
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    from django.contrib.auth.models import User

    # delete all elements
    models.AttributionExclude.objects.filter(book=book).delete()

    for userName in message["excluded_users"]:
        u = User.objects.get(username = userName)
        a = models.AttributionExclude(book = book, user = u)
        a.save()

    transaction.commit()

    return {"status": True}


def remote_settings_language_save(request, message, bookid, version):
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    if message['language'] != 'unknown':
        l = models.Language.objects.get(abbrevation=message['language'])

        book.language = l
        book.save()

    if message['rtl']:
        rtl_value = "RTL"
    else:
        rtl_value = "LTR"

    try:
        rtl = models.Info.objects.get(book=book, name='{http://booki.cc/}dir', kind = 0)
        rtl.value_string = rtl_value
        rtl.save()
    except models.Info.DoesNotExist:

        rtl = models.Info(book = book,
                          name = '{http://booki.cc/}dir',
                          kind = 0,
                          value_string = rtl_value)
        rtl.save()

    transaction.commit()

    return {"status": True}

def remote_users_suggest(request, message, bookid, version):
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    from django.contrib.auth.models import User

#    users = ['%s' % (u.username, ) for u in User.objects.filter(Q(username__contains=message["possible_user"]) | Q(first_name__contains=message["possible_user"]))[:20]]
    users = ['%s (%s)' % (u.username, u.first_name) for u in User.objects.filter(Q(username__contains=message["possible_user"]) | Q(first_name__contains=message["possible_user"]))[:20]]

    transaction.commit()

    return {"status": True, "possible_users": users}

def remote_roles_list(request, message, bookid, version):
    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    users = [(u.user.username, '%s (%s)' % (u.user.username, u.user.first_name)) for u in models.BookiPermission.objects.filter(book = book, permission = message["role"]).order_by("user__username")]

    if int(message["role"]) == 1:
        users.append((book.owner.username, '%s (%s) [owner]' % (book.owner.username, book.owner.first_name)))

    transaction.commit()

    return {"status": True, "users": users}

# remove this
def _remote_roles_save(request, message, bookid, version):
    from booki.editor.views import getVersion
    from django.contrib.auth.models import User

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    userList = set(message["users"][:])
    usersExisting = set([u.user.username for u in models.BookiPermission.objects.filter(book = book, permission = 1) if u.user])

    newUsers =  userList - usersExisting
    removedUsers = usersExisting-userList

    for userName in newUsers:
        try:
            u = User.objects.get(username = userName)
            up = models.BookiPermission(book = book,
                                        user = u,
                                        permission = 1)
            up.save()
        except User.DoesNotExist:
            pass

    for userName in removedUsers:
        try:
            up = models.BookiPermission.objects.get(book = book, user__username = userName, permission = 1)
            up.delete()
        except models.BookiPermission.DoesNotExist:
            pass

    transaction.commit()

    return {"status": True}

def remote_roles_add(request, message, bookid, version):
    from booki.editor.views import getVersion
    from django.contrib.auth.models import User

    # check permissions

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    try:
        u = User.objects.get(username = message["username"])
        up = models.BookiPermission(book = book,
                                    user = u,
                                    permission = message["role"])
        up.save()
    except User.DoesNotExist:
        pass

    transaction.commit()

    return {"status": True}


def remote_roles_delete(request, message, bookid, version):
    from booki.editor.views import getVersion
    from django.contrib.auth.models import User

    # check permissions

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)


    try:
        up = models.BookiPermission.objects.get(book = book, 
                                                user__username = message["username"], 
                                                permission = message["role"])
        up.delete()
    except models.BookiPermission.DoesNotExist:
        pass

    transaction.commit()

    return {"status": True}

def remote_book_status_create(request, message, bookid, version):
    book = models.Book.objects.get(id=bookid)
    status_id = None

    bookSecurity = security.getUserSecurityForBook(request.user, book)

    if not bookSecurity.isAdmin():
        return {"status": False}        

    from django.utils.html import strip_tags

    try:
        bs = models.BookStatus(book = book,
                               name = strip_tags(message["status_name"].strip()),
                               weight = 0)
        bs.save()
    except:
        transaction.rollback()
    else:
        status_id = bs.id
        transaction.commit()

    allStatuses = [(status.id, status.name) for status in models.BookStatus.objects.filter(book=book).order_by("-weight")]

    sputnik.addMessageToChannel(request,
                                "/booki/book/%s/%s/" % (bookid, version),
                                {"command": "chapter_status_changed",
                                 "statuses": allStatuses},
                                myself = False
                                )
    
    return {"status": True,
            "status_id": status_id,
            "statuses": allStatuses
            }

def remote_book_status_remove(request, message, bookid, version):
    book = models.Book.objects.get(id=bookid)

    bookSecurity = security.getUserSecurityForBook(request.user, book)

    if not bookSecurity.isAdmin():
        return {"status": False}        

    result = True
    
    try:
        up = models.BookStatus.objects.get(book = book, id = message["status_id"])
        if len(list(models.Chapter.objects.filter(status = up, book = book))) == 0:
            up.delete()
        else:
            result = False
    except models.BookStatus.DoesNotExist:
        transaction.rollback()
    else:
        transaction.commit()

    allStatuses = [(status.id, status.name) for status in models.BookStatus.objects.filter(book=book).order_by("-weight")]

    sputnik.addMessageToChannel(request,
                                "/booki/book/%s/%s/" % (bookid, version),
                                {"command": "chapter_status_changed",
                                 "statuses": allStatuses},
                                myself = False
                                )

    return {"status": True,
            "result": result,
            "statuses": allStatuses}

def remote_book_status_order(request, message, bookid, version):
    book = models.Book.objects.get(id=bookid)

    bookSecurity = security.getUserSecurityForBook(request.user, book)

    if not bookSecurity.isAdmin():
        return {"status": False}        
    
    weight = 100

    for status_id in [x[11:] for x in message["order"]]:
        up = models.BookStatus.objects.get(book = book, id = status_id)
        up.weight = weight
        up.save()

        weight -= 1
        
    transaction.commit()

    allStatuses = [(status.id, status.name) for status in models.BookStatus.objects.filter(book=book).order_by("-weight")]

    sputnik.addMessageToChannel(request,
                                "/booki/book/%s/%s/" % (bookid, version),
                                {"command": "chapter_status_changed",
                                 "statuses": allStatuses},
                                myself = False
                                )

    return {"status": True,
            "statuses": allStatuses }


