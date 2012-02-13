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

from lxml import etree, html

import sputnik

from django.db import transaction
from django.db.models import Q

from booki.utils.log import logBookHistory, logChapterHistory, printStack

from booki.editor import models
from booki.editor.views import getVersion
from booki.utils import security
from booki.utils.misc import bookiSlugify

from django.conf import settings

try:
    OBJAVI_URL = settings.OBJAVI_URL
except AttributeError:
    OBJAVI_URL = "http://objavi.booki.cc/objavi.cgi"

try:
    THIS_BOOKI_SERVER = settings.THIS_BOOKI_SERVER
except AttributeError:
    import os
    THIS_BOOKI_SERVER = os.environ.get('HTTP_HOST', 'booktype-demo.sourcefabric.org')


# this couple of functions should go to models.BookVersion
def getTOCForBook(version):
    """
    Function returns list of TOC elements. Elements of list are tuples. 
     - If chapter - (chapter_id, chapter_title, chapter_url_title, type_of, chapter_status_ud)
     - If section - (s + section_id, section_name, section_name, type_of)
    
    @rtype: C{list}
    @return: Returns list of TOC elements
    """

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
    """
    Function returns list of hold chapters. Elements of list are tuples with structure - (chapter_id, chapter_title, chapter_url_title, 1, chapter_status_id).

    @type book_version: C{booki.editor.models.BookVersion}
    @param book_version: Book version object
    @rtype: C{list}
    @return: Returns list with hold chapters
    """

    return [(ch.id, ch.title, ch.url_title, 1, ch.status.id) for ch in book_version.getHoldChapters()]


def getAttachments(book_version):
    """
    Function returns list of attachments for L{book_version}. Elements of list are dictionaries and are sorted by attachment name. Each dictionary has keys:
      - id (attachment id)
      - dimension (tuple with width and height for image)
      - status (status id for this attachment)
      - name (name of the attachment)
      - created (when attachmend was created)
      - size (size of attachment in bytes)

    @type book_version: C{booki.editor.models.BookVersion}
    @param book_version: Booki version object
    @rtype: C{list}
    @return: Returns list of dictionaries with info about attachment
    """

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
    """
    Called when Booki editor is being initialized. 

    "user_add" message is send to all users currently on this channel and notification is send to all online users on the chat.

    Returns:
     - licenses - list of tuples (abbrevation, name)
     - chapters - result of getTOCForBook function 
     - metadata - list of dictionaries {'name': ..., 'value': ...}
     - hold - result of getHoldChapters function
     - users - list of active users
     - locks - list of currently locked chapters
     - statuses - list of tuples (status_id, status_name)
     - attachments - result of getAttachments function
     - onlineUsers - list of online users

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns info needed for editor initialization
    """

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
        try:
            profile = request.user.get_profile()
        except AttributeError:
            profile = None

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
    """
    Calls function L{getAttachments} and returns info about attachments for the specific version of the book.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns list of attachments
    """

    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)

    try:
        attachments = getAttachments(book_version)
    except:
        attachments = []

    return {"attachments": attachments}

def remote_attachments_delete(request, message, bookid, version):
    """
    Deletes specific attachment. 

    Input:
      - attachment - Attachment id

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns success of this command
    """

    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)

    bookSecurity = security.getUserSecurityForBook(request.user, book)
    
    if bookSecurity.isAdmin():
        for att_id in message['attachments']:
            # should check if you can delete it
            att = models.Attachment.objects.get(pk=att_id)

            from booki.utils import log
            import os.path

            log.logBookHistory(book = book,
                               version = book_version,
                               args = {'filename': os.path.split(att.attachment.name)[1]},
                               user = request.user,
                               kind = 'attachment_delete')

            att.delete()

            
            
        transaction.commit()

        return {"result": True}

    return {"result": False}

def remote_chapter_status(request, message, bookid, version):
    """
    Sets new status for the specific chapter. Sends "chapter_status" with new status to all users on the channel.

    Input:
      - chapterID
      - status

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    """

    if message["status"] == "normal":
        sputnik.rdelete("booki:%s:locks:%s:%s" % (bookid, message["chapterID"], request.user.username))

    sputnik.addMessageToChannel(request, "/booki/book/%s/%s/" % (bookid, version),
                                {"command": "chapter_status",
                                 "chapterID": message["chapterID"],
                                 "status": message["status"],
                                 "username": request.user.username})

    return {}

def remote_change_status(request, message, bookid, version):
    """
    Change status for the chapter.

    Message "change_status" is send to all users on the channel. Notification is send to chat.

    Input:
      - chapterID
      - statusID

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns success of this command
    """

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
    """
    Saves new chapter content.

    Writes log to Chapter and Book history. Sends notification to chat. Removes lock. Sends "chapter_status" messahe to the channel. Fires the chapter_modified signal.

    Input:
      - chapterID
      - content

    @todo: Check security

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns success of this command
    """

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
    """
    Renames chapter name.

    Creates Book history record. Sends notification to chat. Sends "chapter_status" message to the channel. Sends "chapter_rename" message to the channel.

    @todo: check security

    Input:
     - chapterID
     - chapter - new chapter name

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    """

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
    """
    Reorders the TOC.

    Creates Book history record. Sends "chapters_changed" message to the channel.

    @todo: check security

    Input:
     - chapters
     - hold

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    """

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
    """
    Returns list of users currently editing L{bookid}.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: List of users
    """

    res = {}
    def vidi(a):
        if a == request.sputnikID:
            return "!%s!" % a
        return a

    res["users"] = [vidi(m) for m in list(sputnik.smembers("sputnik:channel:%s:channel" % message["channel"]))]
    return res


def remote_get_chapter(request, message, bookid, version):
    """
    This is called when you fire up WYSWYG editor or Chapter viewer. It sends back basic chapter information.

    If lock flag is send then it will Sends message "chapter_status" to the channel and create lock for this chapter.

    Input:
     - chapterID
     - lock (True or False)
     - revisions (True or False)
     - revision 

    Output:
     - title 
     - content
     - current_revision
     - revisions - list of all revisions
     
    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Chapter info
    """

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
    """
    Editor is constantly sending ping message to notify us that it is still alive.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Should it kill the seasson
    """

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
    """
    Not used at the moment.
    """
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

    if tocChapter:
        allChapters = [chap for chap in models.BookToc.objects.filter(book=book).order_by("-weight")]
        initialPosition =  len(allChapters)-tocChapter.weight
    else:
        initialPosition = 0

    s = models.BookStatus.objects.filter(book=book).order_by("-weight")[0]

    n = 0
    for chap in message["chapters"]:
        chapter = models.Chapter(book = book,
                                 url_title = bookiSlugify(chap[0]),
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
    """
    Creates new chapters. New chapter is always added at the end of the TOC. Creates empty chapter content only with chapter title as heading.

    Record for Chapter and Book history is created. Message "chapter_create" is send to the channel. Notification is send to the chat.

    Input:
     - chapter - chapter name
     - comment (optional)

    @todo: Should check security.
     
    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Return if it was successful
    """

    import datetime

    # BookVersion treba uzeti

    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)

    url_title = bookiSlugify(message["chapter"])

    if len(url_title) == 0:
        return {"created": False, "silly_url": True}


    # here i should probably set it to default project status
    s = models.BookStatus.objects.filter(book=book).order_by("-weight")[0]

    ch = models.Chapter.objects.filter(book=book, version=book_version, url_title=url_title)

    if len(list(ch)) > 0:
        return {"created": False, "silly_url": False}

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

        for itm in models.BookToc.objects.filter(version = book_version, book = book).order_by("-weight"):
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
    """
    Creates new attachment in L{target_book} and copies attachments content there.

    @type attachment: C{booki.editor.models.Attachment}
    @param attachment: Attachment object
    @type target_book: C{booki.editor.models.Book}
    @param target_book: Book version object
    @rtype: C{booki.editor.models.Attachment}
    @return: Returns new Attachment object
    """
    import os.path

    att = models.Attachment(book = target_book,
                            version = target_book.version,
                            status = target_book.status)

    att.attachment.save(os.path.basename(attachment.attachment.name), attachment.attachment, save=False)
    att.save()
    return att

def remote_clone_chapter(request, message, bookid, version):
    """
    Clones chapter in another book. It also recreates TOC and copies attachments. It parsesr HTML content to check for used attachments.

    Creates entry in Chapter and Book history. Sends "chapter_create" message to the channel. Sends notification to chat.

    Input:
     - book - url name for the book
     - chaptter - chapter title
     - renameTitle - New chapter name (optional)

    @todo: Should check security.
     
    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Return if it was successful
    """

    import datetime

    # BookVersion treba uzeti

    book = models.Book.objects.get(id=bookid)
    book_version = getVersion(book, version)
    
    source_book = models.Book.objects.get(url_title=message["book"])
    source_book_version = source_book.version
    source_url_title = message["chapter"]
    try:
        source_chapter = models.Chapter.objects.get(book=source_book, version=source_book_version, url_title=source_url_title)
    except models.Chapter.DoesNotExist:
        return {"created": True}
    except models.Chapter.MultipleObjectsReturned:
        return {"created": True}

    title = message.get("renameTitle", "")
    if title.strip():
        url_title = bookiSlugify(title)
    else:
        title = source_chapter.title
        url_title = source_url_title

    # here i should probably set it to default project status
    s = models.BookStatus.objects.filter(book=book).order_by("-weight")[0]

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
    """
    This is called when you want to publish your book. HTTP Request is sent to Objavi. Objavi then grabs content from Booki, renders it and creates output file.

    Sends notification to chat.

    Input:
     - publish_mode
     - is_archive
     - is_lulu
     - lulu_user
     - lulu_password
     - lulu_api_key
     - lulu_project
     - book
     - project
     - mode
     - server
     - destination
     - max-age
     - grey_scale
     - title
     - license
     - isbn
     - toc_header
     - booksize
     - page_width
     - page_height
     - top_margin
     - side_margin
     - gutter
     - columns
     - column_margin
     - grey_scale
     - css
     - cover_url


    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns info with URL-s where to fetch the result
    """

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

    def _isSet(name, default=None):
        if message.get(name, None):
            if name == 'grey_scale':
                args['grey_scale'] = 'yes'
            else:
                if type(message.get(name)) == type(u' '):
                    args[name] = message.get(name).encode('utf8')
                else:
                    args[name] = message.get(name)
        elif default:
            args[name] = default

    if message.get("is_lulu", False):
        args["to_lulu"] = "yes"
        _isSet("lulu_user", settings.LULU_USER)
        _isSet("lulu_password", settings.LULU_PASSWORD)

        if settings.LULU_API_KEY:
            args["lulu_api_key"] = settings.LULU_API_KEY

        _isSet("lulu_project")

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

    _isSet('cover_url')

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
    """
    Creates new section. Sections is added at the end of the TOC.

    Creates Book history entry. Sends "chapter_create" message to the channel. Sends notification to chat.

    Input:
     - chapter - name for the section. i know :)


    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns if command was successful
    """

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
    """
    Returns Book history entries.

    Input:
     - page

    Output:
     - history

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns history entries
    """

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
            13: 'attachment',
            14: 'attachment_delete'}


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
        elif entry.kind in [13, 14]:
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
    """
    Returns Chapter history entries.

    Input:
     - chapter

    Output:
     - history

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns history entries
    """

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
    """
    Revert chapter content to previous version.

    Creates entry for Chapter and Book history. Sends notification to chat.

    Input:
     - chapter
     - revision

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    """


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
    """
    Returns Chapter data for specific revision.

    Input:
     - chapter
     - revision

    Output:
     - chapter - chapter title
     - chapter_url - chapter url title
     - modified
     - user
     - revision
     - version - book version
     - content
     - comment
     
    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Chapter data
    """

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
    """
    Gets notes for this book.

    Output:
     - notes
     
    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Notes data
    """

    import datetime

    book = models.Book.objects.get(id=bookid)

    book_notes = models.BookNotes.objects.filter(book=book)

    notes = []
    for entry in book_notes:
        notes.append({"notes": entry.notes})

    return {"notes": notes}


def remote_notes_save(request, message, bookid, version):
    """
    Saves notes for this book.

    Sends notification to chat.

    Input:
     - notes
     
    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    """

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
    """
    Removes lock for chapter. Only booki user can do this. Lock is removed from Redis database.

    Sends notification to chat.

    Input:
     - chapterID
     
    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    """

    import re

    if request.user.username == 'booki':
        for key in sputnik.rkeys("booki:%s:locks:%s:*" % (bookid, message["chapterID"])):
            m = re.match("booki:(\d+):locks:(\d+):(\w+)", key)

            if m:
                sputnik.set("booki:%s:killlocks:%s:%s" % (bookid, message["chapterID"], m.group(3)), 1)

    return {}


def remote_get_versions(request, message, bookid, version):
    """
    Returns data about all Book versions.

    Output:
     - versions
        - major
        - minor
        - name
        - description
        - created
     
    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns list of dictionaries with data about all Book versions
    """

    book = models.Book.objects.get(id=bookid)

    book_versions = [{"major": v.major,
                      "minor": v.minor,
                      "name": v.name,
                      "description": v.description,
                      "created": str(v.created.strftime('%a, %d %b %Y %H:%M:%S GMT'))}
                     for v in models.BookVersion.objects.filter(book=book).order_by("-created")]

    return {"versions": book_versions}



# put this outside of this module
def create_new_version(book, book_ver, message, major, minor):
    """
    Creates new version of the book. Copies TOC, copies all attachments and etc...

    Input:
     - name
     - description

    @type book: C{booki.editor.models.Book}
    @param book: Book object
    @type book_ver: C{booki.editor.models.BookVersion}
    @param book_ver: Book version object
    @type message: C{dict}
    @param message: Sputnik message
    @type major: C{int}
    @param major: Major version
    @type minor: C{int}
    @param minor: Minor version
    @rtype: C{booki.editor.models.BookVersion}
    @return: Returns Book version object
    """

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
    """
    Creates new major version of the book.

    Creates new entry in the Book history.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns new version number
    """

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
    """
    Creates new minor version of the book.

    Creates new entry in the Book history.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns new version number
    """

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

            out += '<span class="diff changed">'+color_me(l[pos[0]:pos[1]], rgb, None)+'</span>'
            out += l[pos[1]:]
        else:
            out = l
        return out

    out = '<span class="%s">' % rgb

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

                        out += tag+'<span class="%s">' % rgb
                    else:
                        out += tag

                    n = j
        m = n
            

    out += l[n:]+'</span>'

    return out

def remote_chapter_diff(request, message, bookid, version):
    """
    Returns diff between two revisions of the chapter. Diff is returned as HTML string.

    Input:
     - message
     - revision1
     - revision2

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns text with diff between two chapters
    """

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
    """
    Returns diff between two revisions of the chapter. Diff is returned as HTML string and is used for parallel comparison.

    Input:
     - message
     - revision1
     - revision2

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns text with diff between two chapters
    """

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

            output_right +=  '<div class="diff changed">'+color_me(line[2:], 'diff added', plus_pos)+'</div>'
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
            output_left +=  '<div class="diff changed">'+color_me(line[2:], 'diff deleted', minus_pos)+'</div>'
        elif line[:2] == '  ':
            if line[2:].strip() != '':
                output_left  += line[2:]+'<br/><br/>'
                output_right += line[2:]+'<br/><br/>'

        n += 1

    output.append('<tr>'+output_left+'</td>'+output_right+'</td></tr>')
    
    info = '''<div style="padding-bottom: 5px"><span class="diff changed" style="width: 10px; height: 10px; display: inline-block;"></span> Changed <span class="diff added" style="width: 10px; height: 10px; display: inline-block;"></span> Added <span class="diff deleted" style="width: 10px; height: 10px; display: inline-block;"></span> Deleted </div>'''
    
    return {"output": info+'<table border="0" width="100%%"><tr><td width="50%%"><div style="border-bottom: 1px solid #c0c0c0; font-weight: bold;">Revision: '+message["revision1"]+'</div></td><td width="50%%"><div style="border-bottom: 1px solid #c0c0c0; font-weight: bold">Revision: '+message["revision2"]+'</div></td></tr>\n'.join(output)+'</table>\n'}



def remote_settings_options(request, message, bookid, version):
    """
    Returns minimal amount of data needed to show on the Settings tab in the Editor. This call is used when user clicks on the Settings tab.

    Output:
     - licenses
     - permission
     - current_licence
     - languages
     - current_language
     - rtl

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns needed data for Settings tab
    """

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
            "permission": book.permission,
            "current_licence": current_license,
            "languages": languages,
            "current_language": current_language,
            "rtl": rtl
            }


def remote_license_save(request, message, bookid, version):
    """
    This call is used from the Settings tab. It is used to save new license data for the book.

    Input:
     - license

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns if operation was successful
    """

    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)
    #book_ver = getVersion(book, version)

    lic = models.License.objects.filter(abbrevation=message["license"])[0]
    book.license = lic
    book.save()

    transaction.commit()

    return {"status": 1}

def remote_license_attributions(request, message, bookid, version):
    """
    This call is used from the Settings tab. You get list of users who have attribution rights and list of people who have been excluded from the list.

    Output:
     - users
     - users_exclude

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns if operation was successful
    """

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
    """
    This call is used from the Settings tab. Saves new list of excluded users from the attribution rights.

    Input:
     - excluded_users

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns if operation was successful
    """

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
    """
    This call is used from the Settings tab. Saves new book language and rtl setting for the book.

    Input:
     - language
     - rtl

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns if operation was successful
    """

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
    """
    This call is used from the Settings tab, Manage roles dialog. This called is used to autofill username field.

    Input:
     - possible_user

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns list of users
    """

    from booki.editor.views import getVersion

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)

    from django.contrib.auth.models import User

#    users = ['%s' % (u.username, ) for u in User.objects.filter(Q(username__contains=message["possible_user"]) | Q(first_name__contains=message["possible_user"]))[:20]]
    users = ['%s (%s)' % (u.username, u.first_name) for u in User.objects.filter(Q(username__contains=message["possible_user"]) | Q(first_name__contains=message["possible_user"]))[:20]]

    transaction.commit()

    return {"status": True, "possible_users": users}


def remote_roles_list(request, message, bookid, version):
    """
    Returns list of users who have specific role on this book.
   
    Input:
     - role

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns list of users
    """

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
    """
    Adds user to specific role.
   
    Input:
     - username
     - role

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns True if operation was successful
    """

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
    """
    Removes role from this specific user.
   
    Input:
     - username
     - role

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns True if operation was successful
    """

    from booki.editor.views import getVersion
    from django.contrib.auth.models import User

    # check permissions

    book = models.Book.objects.get(id=bookid)
    book_ver = getVersion(book, version)


    try:
        for up in models.BookiPermission.objects.filter(book = book, 
                                                     user__username = message["username"], 
                                                     permission = message["role"]):
            up.delete()
    except models.BookiPermission.DoesNotExist:
        pass

    transaction.commit()

    return {"status": True}


def remote_book_status_create(request, message, bookid, version):
    """
    Creates new book status.

    Sends notification to chat.
   
    Input:
     - status_name
     
    Output:
     - status
     - status_id
     - statuses
   
    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns list of all statuses and id of the newly created one
    """

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
    """
    Removes book status.

    Sends notification to chat.
   
    Input:
     - status_id
     
    Output:
     - status
     - result
     - statuses
   
    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns list of all statuses
    """

    book = models.Book.objects.get(id=bookid)

    bookSecurity = security.getUserSecurityForBook(request.user, book)

    if not bookSecurity.isAdmin():
        return {"status": False}        

    result = True
    
    try:
        up = models.BookStatus.objects.get(book = book, id = message["status_id"])
        # this is a quick fix
        # check - no chapter has this status + no attachment has this status and no book has this status
        if len(list(models.Chapter.objects.filter(status = up, book = book))) == 0 and \
                len(list(models.Attachment.objects.filter(status = up, version__book = book))) == 0 and \
                book.status != up:
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
    """
    Reorders list of book statuses.

    Sends notification to chat.
   
    Input:
     - order
     
    Output:
     - status
     - statuses
   
    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns list of all statuses
    """

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


def remote_book_permission_save(request, message, bookid, version):
    """
    Sets book permissions.

    Input:
     - permission
     
    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns True if operation was successful
    """

    book = models.Book.objects.get(id=bookid)

    bookSecurity = security.getUserSecurityForBook(request.user, book)

    if not bookSecurity.isAdmin():
        return {"status": False}        
    
    book.permission = message["permission"]
    book.save()
        
    transaction.commit()

    return {"status": True}


###############################################################################################################

PUBLISH_OPTIONS = {
    'book': [{"name": "booksize", "value": "COMICBOOK"}, {"name": "custom_width", "value": ""}, {"name": "custom_height", "value": ""}, {"name": "body_font-family", "value": "Fontin_Sans"}, {"name": "body_font-size", "value": "10"}, {"name": "h1_font-family", "value": "Fontin_Sans"}, {"name": "h1_font-size", "value": "14"}, {"name": "h1_text-transform", "value": "uppercase"}, {"name": "h1_font-weight", "value": "heavy"}, {"name": "h2_font-family", "value": "Fontin_Sans"}, {"name": "h2_font-size", "value": "12"}, {"name": "h2_text-transform", "value": "uppercase"}, {"name": "h2_font-weight", "value": "heavy"}, {"name": "h3_font-family", "value": "Fontin_Sans"}, {"name": "h3_font-size", "value": "10"}, {"name": "h3_text-transform", "value": "uppercase"}, {"name": "h3_font-weight", "value": "heavy"}, {"name": "pre_font-family", "value": "Courier"}, {"name": "pre_font-size", "value": "10"}, {"name": "p_pagebreak", "value": "on"}, {"name": "footnotes_pagebreak", "value": "on"}, {"name": "control-css", "value": "on"}, {"name": "page-numbers", "value": "auto"}, {"name": "embed-fonts", "value": "on"}, {"name": "toc_header", "value": ""}, {"name": "top_margin", "value": ""}, {"name": "side_margin", "value": ""}, {"name": "bottom_margin", "value": ""}, {"name": "gutter", "value": ""}, {"name": "columns", "value": ""}, {"name": "column_margin", "value": ""}, {"name": "additional_css", "value": ""}, {"name": "special_css", "value": ".objavi-chapter{\n  color: #000;\n  display:none;\n} \n\na {\n  text-decoration:none;\n  color:#000;\n} \n\nh1 .initial{\n  color: #000;\n  display:none;\n} \n\n.objavi-subsection{\n  display: block;\n  page-break-before: always;\n} \n\nbody .objavi-subsection:first-child{\n   page-break-before: avoid;\n} \n\n.objavi-subsection .initial {\n   color: #000;\n   display:none;\n} \n\n.objavi-subsection-heading {\n   font-size: 20pt;\n   text-align: center;\n   line-height: 300px;\n   font-weight: normal;\n} \n\ntable {\n   float: none;\n} \n\nh1.frontpage{\n  page-break-after:always;\n  margin-top:70%;\n  font-size: 20pt;\n  text-align: center;\n  page-break-before: avoid;\n  max-width: 700pt;\n  font-weight: normal;\n} \n\ndiv.copyright{\n  padding: 1em;\n}\n\n/* TOC ******************************/\ntable {\n  float: none;\n} \n\ntable.toc {\n  font-size: 1.1em;\n  width: 95%;\n} \n\ntable.toc td{\n  vertical-align:top\n  padding-left: 0.5em;\n} \n\ntd.chapter {\n  padding: 0 0.5em;\n  text-align: right;\n} \n\ntable.toc td.pagenumber {\n  text-align: right;\n  vertical-align:bottom;\n} \n\ntd.section {\n  padding-top: 1.1em;\n  font-weight: bold;\n}\n\n/* End TOC **************************/ \n\nimg {\n  max-width: 500px;\n  height: auto;\n} \n\n.objavi-no-page-break {\n  page-break-inside: avoid;\n} \n\n.unseen{\n  z-index: -66;\n  margin-left: -1000pt;\n} \n\n.objavi-subsection-heading{\n  height:860px;\n  font-size:0px;\n  display:block;\n}\n\t  "}, {"name": "grey_scale", "value": "off"}, {"name": "rotate", "value": "off"}, {"name": "allow-breaks", "value": "off"}, {"name": "custom_override", "value": "off"}, {"name": "", "value": "off"}, {"name": "", "value": "off"}],
    'ebook': [{"name": "body_font-family", "value": "Fontin_Sans"}, {"name": "body_font-size", "value": "10"}, {"name": "h1_font-family", "value": "Fontin_Sans"}, {"name": "h1_font-size", "value": "14"}, {"name": "h1_text-transform", "value": "uppercase"}, {"name": "h1_font-weight", "value": "heavy"}, {"name": "h2_font-weightamily", "value": "Fontin_Sans"}, {"name": "h2_font-size", "value": "12"}, {"name": "h2_text-transform", "value": "uppercase"}, {"name": "h2_font-weight", "value": "heavy"}, {"name": "h3_font-family", "value": "Fontin_Sans"}, {"name": "h3_font-size", "value": "10"}, {"name": "h3_text-transform", "value": "uppercase"}, {"name": "h3_font-weight", "value": "heavy"}, {"name": "pre_font-family", "value": "Courier"}, {"name": "pre_font-size", "value": "10"}, {"name": "additional_css", "value": ""}, {"name": "special_css", "value": ".objavi-chapter{\n  color: #000;\n  display:none;\n} \n\na {\n  text-decoration:none;\n  color:#000;\n} \n\nh1 .initial{\n  color: #000;\n  display:none;\n} \n\n.objavi-subsection{\n  display: block;\n  page-break-before: always;\n} \n\nbody .objavi-subsection:first-child{\n  page-break-before: avoid;\n} \n\n.objavi-subsection .initial {\n  color: #000;\n  display:none;\n} \n\n.objavi-subsection-heading {\n  font-size: 20pt;\n  text-align: center;\n  line-height: 300px;\n  font-weight: normal;\n} \n\ntable {\n  float: none;\n} \n\nh1.frontpage{\n  page-break-after:always;\n  margin-top:70%;\n  font-size: 20pt;\n  text-align: center;\n  page-break-before: avoid;\n  max-width: 700pt;\n  font-weight: normal;\n} \n\ndiv.copyright{\n  padding: 1em;\n}\n/* TOC ******************************/\ntable {\n  float: none;\n} \n\ntable.toc {\n  font-size: 1.1em;\n  width: 95%;\n} \n\ntable.toc td {\n  vertical-align:top\n  padding-left: 0.5em;\n} \n\ntd.chapter {\n  padding: 0 0.5em;\n  text-align: right;\n} \n\ntable.toc td.pagenumber {\n  text-align: right;\n  vertical-align:bottom;\n} \n\ntd.section {\n  padding-top: 1.1em;\n  font-weight: bold;\n}\n\t\t\t\t\t\n/* End TOC **************************/ \nimg {\n   max-width: 500px;\n   height: auto;\n} \n\n.objavi-no-page-break {\n   page-break-inside: avoid;\n} \n\n.unseen {\n   z-index: -66;\n   margin-left: -1000pt;\n} \n\n.objavi-subsection-heading{\n  height:860px;\n  font-size:0px;\n  display:block;\n}\n"}, {"name": "ebook_format", "value": "epub"},  {"name": "custom_override", "value": "off"}, {"name": "", "value": "off"}, {"name": "", "value": "off"}],
    'lulu': [{"name": "lulu_user", "value": ""}, {"name": "lulu_password", "value": ""}, {"name": "lulu_title", "value": ""}, {"name": "description", "value": ""}, {"name": "authors", "value": ""}, {"name": "lulu_download_price", "value": ""}, {"name": "lulu_print_price", "value": ""}, {"name": "lulu_currency_code", "value": "EUR"}, {"name": "pagesize", "value": "COMICBOOK"}, {"name": "body_font-family", "value": "Fontin_Sans"}, {"name": "body_font-size", "value": "10"}, {"name": "heading_font", "value": "Fontin_Sans"}, {"name": "h1_font-size", "value": "14"}, {"name": "h1_text-transform", "value": "uppercase"}, {"name": "h1_fontweight", "value": "heavy"}, {"name": "h2_font-family", "value": "Fontin_Sans"}, {"name": "h2_font-size", "value": "12"}, {"name": "h2_text-transform", "value": "uppercase"}, {"name": "h2_font-weight", "value": "heavy"}, {"name": "h3_font-family", "value": "Fontin_Sans"}, {"name": "h3_font-size", "value": "10"}, {"name": "h3_texttransform", "value": "uppercase"}, {"name": "h3_font-weight", "value": "heavy"}, {"name": "pre_font-family", "value": "Courier"}, {"name": "pre_font-size", "value": "10"}, {"name": "p_pagebreak", "value": "on"}, {"name": "footnotes_pagebreak", "value": "on"}, {"name": "additional_css", "value": ""}, {"name": "special_css", "value": "\n\t    .objavi-chapter{\n\t    color: #000;\n\t    display:none;\n\t    } \n\n\t    a {\n\t    text-decoration:none;\n\t    color:#000;\n\t    } \n\n\t    h1 .initial{\n\t    color: #000;\n\t    display:none;\n\t    } \n\n\n\t    .objavi-subsection{\n\t    display: block;\n\t    page-break-before: always;\n\t    } \n\n\t    body .objavi-subsection:first-child{\n\t    page-break-before: avoid;\n\t    } \n\n\t    .objavi-subsection .initial {\n\t    color: #000;\n\t    display:none;\n\t    } \n\n\t    .objavi-subsection-heading {\n\t    font-size: 20pt;\n\t    text-align: center;\n\t    line-height: 300px;\n\t    font-weight: normal;\n\t    } \n\n\t    table {\n\t    float: none;\n\t    } \n\n\t    h1.frontpage{\n\t    page-break-after:always;\n\t    margin-top:70%;\n\t    font-size: 20pt;\n\t    text-align: center;\n\t    page-break-before: avoid;\n\t    max-width: 700pt;\n\t    font-weight: normal;\n\t    } \n\n\t    div.copyright{\n\t    padding: 1em;\n\t    }\n\t    /* TOC ******************************/\n\t    table {\n\t    float: none;\n\t    } \n\n\t    table.toc {\n\t    font-size: 1.1em;\n\t    width: 95%;\n\t    } \n\n\t    table.toc td{\n\t    vertical-align:top\n\t    padding-left: 0.5em;\n\t    } \n\n\t    td.chapter {\n\t    padding: 0 0.5em;\n\t    text-align: right;\n\t    } \n\n\t    table.toc td.pagenumber {\n\t    text-align: right;\n\t    vertical-align:bottom;\n\t    } \n\n\t    td.section {\n\t    padding-top: 1.1em;\n\t    font-weight: bold;\n\t    }\n\t    /* End TOC **************************/ \n\n\t    img {\n\t    max-width: 500px;\n\t    height: auto;\n\t    } \n\n\t    .objavi-no-page-break {\n\t    page-break-inside: avoid;\n\t    } \n\n\t    .unseen{\n\t    z-index: -66;\n\t    margin-left: -1000pt;\n\t    } \n\n\n\t    .objavi-subsection-heading{\n\t    height:860px;\n\t    font-size:0px;\n\t    display:block;\n\t    }\n\t  "}, {"name": "custom_override", "value": "off"}, {"name": "", "value": "off"}, {"name": "", "value": "off"}],
    'odt': [{"name": "body_font-weight", "value": "Fontin_Sans"}, {"name": "body_font-size", "value": "10"}, {"name": "h1_font-weight", "value": "Fontin_Sans"}, {"name": "h1_font-size", "value": "14"}, {"name": "h1_text-transform", "value": "uppercase"}, {"name": "h1_font-weight", "value": "heavy"}, {"name": "h2_font-weight", "value": "Fontin_Sans"}, {"name": "h2_font-size", "value": "12"}, {"name": "h2_text-transform", "value": "uppercase"}, {"name": "h2_font-weight", "value": "heavy"}, {"name": "h3_font-weight", "value": "Fontin_Sans"}, {"name": "h3_font-size", "value": "10"}, {"name": "h3_text-transform", "value": "uppercase"}, {"name": "h3_font-weight", "value": "heavy"}, {"name": "pre_font-weight", "value": "Courier"}, {"name": "pre_font-size", "value": "10"}, {"name": "p_pagebreak", "value": "on"}, {"name": "footnotes_pagebreak", "value": "on"}, {"name": "additional_css", "value": ""}, {"name": "special_css", "value": "body {\n}\n\n#book-title {\n    font-size: 64pt;\n    page-break-before: avoid;\n    margin-bottom: 12em;  \n    max-width: 700px;\n}\n\n.unseen {\n    display: none;\n}\n\n.chapter {\n    color: #000;\n}\n\nh1 .initial {\n    color: #000;\n    font-size: 2em;\n}\n\nbody .subsection:first-child {\n}\n\nh1 {\n  page-break-before: always;\n}\n\n.objavi-subsection{\n   text-transform: uppercase;\n   font-size: 20pt;\n}\n\n.objavi-subsection .initial {\n   font-size: 1em;\n   color: #000;\n}\n\n.objavi-subsection-heading{\n   font-size: 36pt;\n   font-weight: bold;\n   page-break-before: always;\n}\n\ntable {\n   float: none;\n}\n\nh1.frontpage{\n   font-size: 64pt;\n   text-align: center;\n   max-width: 700px;\n}\n\ndiv.copyright{\n    padding: 1em;\n}\n\npre {\n   max-width:700px;\n   overflow: hidden;\n}\n\nimg {\n   max-width: 700px;\n   height: auto;\n}\n"}, {"name": "custom_override", "value": "off"}, {"name": "", "value": "off"}, {"name": "", "value": "off"}],
    'pdf': [{"name": "booksize", "value": "A4"}, {"name": "custom_width", "value": ""}, {"name": "custom_height", "value": ""}, {"name": "body_font-family", "value": "Fontin_Sans"}, {"name": "body_font-size", "value": "10"}, {"name": "h1_font-family", "value": "Fontin_Sans"}, {"name": "h1_font-size", "value": "14"}, {"name": "h1_text-transform", "value": "uppercase"}, {"name": "h1_font-weight", "value": "heavy"}, {"name": "h2_font-family", "value": "Fontin_Sans"}, {"name": "h2_font-size", "value": "12"}, {"name": "h2_text-transform", "value": "uppercase"}, {"name": "h2_font-weight", "value": "heavy"}, {"name": "h3_font-family", "value": "Fontin_Sans"}, {"name": "h3_font-size", "value": "10"}, {"name": "h3_text-transform", "value": "uppercase"}, {"name": "h3_font-weight", "value": "heavy"}, {"name": "pre_font-family", "value": "Courier"}, {"name": "pre_font-size", "value": "10"}, {"name": "p_pagebreak", "value": "on"}, {"name": "footnotes_pagebreak", "value": "on"}, {"name": "control-css", "value": "on"}, {"name": "page-numbers", "value": "auto"}, {"name": "embed-fonts", "value": "yes"}, {"name": "top_margin", "value": ""}, {"name": "side_margin", "value": ""}, {"name": "bottom_margin", "value": ""}, {"name": "gutter", "value": ""}, {"name": "columns", "value": ""}, {"name": "column_margin", "value": ""}, {"name": "additional_css", "value": ""}, {"name": "special_css", "value": ".objavi-subsection{ \n  display: block; \n  page-break-before: always; \n/* page-break-after: always;*/ \n  text-transform: uppercase; \n  font-size: 20pt; \n} \n\nbody .objavi-subsection:first-child{ \n  page-break-before: avoid; \n} \n\n\n.objavi-subsection .initial { \n  font-size: 1em; \n  color: #000; \n} \n\n.objavi-subsection-heading { \n  font-size: 20pt; \n  text-align: center; \n  line-height: 300px; \n  font-weight: normal; \n} \n\n\nh1 { \n  page-break-before: always; \n} \n\n\ntable { \n  float: none; \n} \n\nh1.frontpage{ \n  page-break-after:always; \n  margin-top:70%; \n  font-size: 20pt; \n  text-align: center; \n  page-break-before: avoid; \n  font-weight: normal; \n} \n\ndiv.copyright{ \n  padding: 1em; \n} \n/* TOC ******************************/ \ntable { \n  float: none; \n} \n\ntable.toc { \n  font-size: 1.1em; \n  width: 95%; \n} \n\ntable.toc td{ \n  vertical-align:top \n  padding-left: 0.5em; \n} \n\ntd.chapter { \n  padding: 0 0.5em; \n  text-align: right; \n} \n\ntable.toc td.pagenumber { \n  text-align: right; \n  vertical-align:bottom; \n} \n\ntd.section { \n  padding-top: 1.1em; \n  font-weight: bold; \n} \n/* End TOC **************************/ \n\n\n\npre { \n  overflow: hidden; \n  white-space: pre-wrap; \n} \n\n\nh1, h2, h3, h4, h5, h6{ \n  page-break-after: avoid; \n  page-break-inside: avoid; \n} \n\n\n.page-break{ \n  page-break-before: always; \n  height: 7em; \n  display: block; \n} \n\na { \n  word-wrap: break-word; \n} \n\n.objavi-no-page-break { \n  page-break-inside: avoid; \n} \n\n/*To force a blank page it is sometimes necessary to add unseen \n content. Display:none and visibility: hidden don't work -- the \n renderer realises that they're not there and skips the page. So we \n add a tiny bit of text beyond the margin of the page. \n*/ \n.unseen{ \n  z-index: -66; \n  margin-left: -1000pt; \n}"}, {"name": "grey_scale", "value": "off"}, {"name": "rotate", "value": "off"}, {"name": "allow-breaks", "value": "off"}, {"name": "custom_override", "value": "off"}, {"name": "", "value": "off"}, {"name": "", "value": "off"}]
}


def remote_get_wizzard(request, message, bookid, version):
    from booki.editor import models
    from booki.utils.json_wrapper import simplejson

    book = models.Book.objects.get(id=bookid)

    options = []

    try:
        pw = models.PublishWizzard.objects.get(book=book,
                                               user=request.user,
                                               wizz_type=message['wizzard_type']
                                               )
        
        try:
            options = simplejson.loads(pw.wizz_options)
        except:
            options = PUBLISH_OPTIONS[message.get('wizzard_type', 'book')]

    except models.PublishWizzard.DoesNotExist:
        options = PUBLISH_OPTIONS[message.get('wizzard_type', 'book')]

    import django.template.loader
    from django.template import Context

    # book, ebook, pdf, odt, lulu

    c = Context({})
    tmpl = django.template.loader.get_template('editor/wizzard_%s.html' % message.get('wizzard_type', 'book')) 
    html = tmpl.render(c)
        
    return {"status": True, "options": options, "html": html}


def remote_set_wizzard(request, message, bookid, version):
    from booki.editor import models
    from booki.utils.json_wrapper import simplejson

    book = models.Book.objects.get(id=bookid)
    

    options = message.get('wizzard_options', '')
    
    pw, created = models.PublishWizzard.objects.get_or_create(book=book, 
                                                              user=request.user,
                                                              wizz_type=message.get('wizzard_type', 'book'))
    
    pw.wizz_options=simplejson.dumps(options)
    pw.save()

#    f = open('/tmp/opcije_%s.json' % message['wizzard_type'], 'wt')
#    f.write(simplejson.dumps(options))
#    f.close()

    transaction.commit()

    return {"status": True, "options": {}}


def remote_publish_book2(request, message, bookid, version):
    """
    This is called when you want to publish your book. HTTP Request is sent to Objavi. Objavi then grabs content from Booki, renders it and creates output file.

    Sends notification to chat.

    Input:
     - publish_mode
     - is_archive
     - is_lulu
     - lulu_user
     - lulu_password
     - lulu_api_key
     - lulu_project
     - book
     - project
     - mode
     - server
     - destination
     - max-age
     - grey_scale
     - title
     - license
     - isbn
     - toc_header
     - booksize
     - page_width
     - page_height
     - top_margin
     - side_margin
     - gutter
     - columns
     - column_margin
     - grey_scale
     - css
     - cover_url


    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns info with URL-s where to fetch the result
    """

    from booki.utils.json_wrapper import simplejson

    book = models.Book.objects.get(id=bookid)

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info",
                                                                "from": request.user.username,
                                                                "message": '"%s" is being published.' % (book.title, )},
                        myself=True)

    import urllib2
    import urllib

    # read all default options


    book = models.Book.objects.get(id=bookid)

    options = []

    try:
        pw = models.PublishWizzard.objects.get(book=book,
                                               user=request.user,
                                               wizz_type= message.get("publish_mode", "epub")
                                               )
        try:
            options = simplejson.loads(pw.wizz_options)
        except:
            options = PUBLISH_OPTIONS[message.get('wizzard_type', 'book')]

    except models.PublishWizzard.DoesNotExist:
        options = PUBLISH_OPTIONS[message.get('wizzard_type', 'book')]
    

    # converstion for names
    publishOptions = {'ebook': 'epub',
                      'book': 'book',
                      'odt': 'openoffice',
                      'newpaper': 'pdf',
                      'lulu': 'book',
                      'pdf': 'web'}

    licenses = {'PD': 'public domain',
                'MIT': 'MIT',
                'CC0': 'CC-BY',
                'CC BY': 'CC-BY',
                'CC BY-SA': 'CC-BY',
                'CC BY-ND': 'CC BY',
                'CC BY-NC': 'CC BY',
                'CC BY-NC-SA': 'CC-BY',
                'CC BY-NC-ND': 'CC-BY',
                'GPL': 'GPL'
        }

    publishMode = publishOptions[message.get("publish_mode", "epub")]

    destination = "nowhere"

    args = {'book': book.url_title.encode('utf8'),
            'license': licenses.get(book.license.abbrevation, 'GPL'),
            'project': 'export',
            'mode': publishMode,
            'server': THIS_BOOKI_SERVER,
            'destination': destination,
            'max-age': 0,
            }

    def _isSet(name, default=None):
        isInside = False

        for opt in options:
            if opt['name'] == name:
                isInside = True
                value = opt['value']

                if value == 'on':
                    value = 'yes'

                if type(opt['value']) == type(u' '):
                    args[name] = value.encode('utf8')
                else:
                    args[name] = value

        if not isInside and default:
            args[name] = default

    def _getValue(name):
        for opt in options:
            if opt['name'] == name:
                return opt['value']

        return None

    # todo
    # - title
    # - licence        
    # - css ove da slaze
    # - isbn

    def _formatCSS(name, family, size, transform=None, weight=None):
        s  = "%s {\n" % name
        if family:
            s += "    font-family: %s;\n" % family
        if size:
            s += "    font-size: %spt;\n" % size
        if transform:
            s += "    text-transform: %s;\n" % transform
        if weight:
            s += "    font-weight: %s;\n" % weight
        s += "}\n"

        return s
 

    if publishMode == 'book' and message.get("publish_mode", "") != 'lulu':
        _isSet('booksize')
        _isSet('custom_width')
        _isSet('custom_height')
        _isSet('p_pagebreak')
        _isSet('footnotes_pagebreak')
        _isSet('grey_scale')
        _isSet('page-numbers')
        _isSet('rotate')
        _isSet('embed-fonts')
        _isSet('allow-breaks')
        _isSet('toc_header')
        _isSet('top_margin')
        _isSet('side_margin')
        _isSet('bottom_margin')
        _isSet('gutter')
        _isSet('columns')
        _isSet('column_margin')

        # in this case, just the css you entered
        if _getValue('custom_override') == 'on':
            _css = _getValue('additional_css') or ''
            _css += _getValue('special_css') or ''
        else:
            _css = _getValue('special_css') or ''
            _css += _formatCSS("BODY, P", _getValue('body_font-family'), _getValue('body_font-size'))
            _css += _formatCSS("H1", _getValue('h1_font-family'), _getValue('h1_font-size'), _getValue('h1_text-transform'), _getValue('h1_font-weight'))
            _css += _formatCSS("H2", _getValue('h2_font-family'), _getValue('h2_font-size'), _getValue('h2_text-transform'), _getValue('h2_font-weight'))
            _css += _formatCSS("H3", _getValue('h3_font-family'), _getValue('h3_font-size'), _getValue('h3_text-transform'), _getValue('h3_font-weight'))
            _css += _formatCSS("PRE", _getValue('pre_font-family'), _getValue('pre_font-size'))

        if _getValue('control-css') == 'on':
            args['css'] = _css


    if publishMode == 'book' and message.get("publish_mode", "") == 'lulu':
        args['to_lulu'] = 'yes' 
        args['lulu_user'] = message.get('lulu_user', '')
        args['lulu_password'] = message.get('lulu_password', '')

        _isSet('lulu_title')
        _isSet('description')
        _isSet('authors')
        _isSet('lulu_download_price')
        _isSet('lulu_print_price')
        _isSet('lulu_currency_code')
        _isSet('pagesize')

        if _getValue('custom_override') == 'on':
            _css = _getValue('additional_css') or ''
            _css += _getValue('special_css') or ''
        else:
            _css = _getValue('special_css') or ''
            _css += _formatCSS("BODY, P", _getValue('body_font-family'), _getValue('body_font-size'))
            _css += _formatCSS("H1", _getValue('h1_font-family'), _getValue('h1_font-size'), _getValue('h1_text-transform'), _getValue('h1_font-weight'))
            _css += _formatCSS("H2", _getValue('h2_font-family'), _getValue('h2_font-size'), _getValue('h2_text-transform'), _getValue('h2_font-weight'))
            _css += _formatCSS("H3", _getValue('h3_font-family'), _getValue('h3_font-size'), _getValue('h3_text-transform'), _getValue('h3_font-weight'))
            _css += _formatCSS("PRE", _getValue('pre_font-family'), _getValue('pre_font-size'))

        args['css'] = _css
        
        _isSet('p_pagebreak')
        _isSet('footnotes_pagebreak')
        

    if publishMode == 'epub':
        # ebook_format ipad,kindle,epub

        ebookFormat = _getValue('ebook_format')

        if ebookFormat == 'kindle':
            args['output_profile'] = 'kindle'
            args['output_format'] = 'mobi'

        if ebookFormat == 'ipad':
            args['output_profile'] = 'ipad'
            args['output_format'] = 'epub'

        if _getValue('custom_override') == 'on':
            _css = _getValue('additional_css') or ''
        else:
            _css = ''
            _css += _formatCSS("BODY, P", _getValue('body_font-family'), _getValue('body_font-size'))
            _css += _formatCSS("H1", _getValue('h1_font-family'), _getValue('h1_font-size'), _getValue('h1_text-transform'), _getValue('h1_font-weight'))
            _css += _formatCSS("H2", _getValue('h2_font-family'), _getValue('h2_font-size'), _getValue('h2_text-transform'), _getValue('h2_font-weight'))
            _css += _formatCSS("H3", _getValue('h3_font-family'), _getValue('h3_font-size'), _getValue('h3_text-transform'), _getValue('h3_font-weight'))
            _css += _formatCSS("PRE", _getValue('pre_font-family'), _getValue('pre_font-size'))

        args['css'] = _css

    if publishMode == 'web':
        _isSet('booksize')
        _isSet('custom_width')
        _isSet('custom_height')

        if _getValue('custom_override') == 'on':
            _css = _getValue('additional_css') or ''
            _css += _getValue('special_css') or ''
        else:
            _css = _getValue('special_css') or ''
            _css += _formatCSS("BODY, P", _getValue('body_font-family'), _getValue('body_font-size'))
            _css += _formatCSS("H1", _getValue('h1_font-family'), _getValue('h1_font-size'), _getValue('h1_text-transform'), _getValue('h1_font-weight'))
            _css += _formatCSS("H2", _getValue('h2_font-family'), _getValue('h2_font-size'), _getValue('h2_text-transform'), _getValue('h2_font-weight'))
            _css += _formatCSS("H3", _getValue('h3_font-family'), _getValue('h3_font-size'), _getValue('h3_text-transform'), _getValue('h3_font-weight'))
            _css += _formatCSS("PRE", _getValue('pre_font-family'), _getValue('pre_font-size'))

        args['css'] = _css

        # fix rotate u pdf verziji
        _isSet('p_pagebreak')
        _isSet('footnotes_pagebreak')
        _isSet('grey_scale')
        _isSet('page-numbers')
        _isSet('rotate')
        _isSet('embed-fonts')
        _isSet('allow-breaks')
        _isSet('toc_header')
        _isSet('top_margin')
        _isSet('side_margin')
        _isSet('bottom_margin')
        _isSet('gutter')
        _isSet('columns')
        _isSet('column_margin')
                       

    data = urllib.urlencode(args)
    req = urllib2.Request(OBJAVI_URL, data)

    try:
        f = urllib2.urlopen(req)
    except urllib2.URLError:
        return {"status": False}

    try:
        ta = f.read()
    except IOError:
        return {"status": False}
        
    lst = ta.split("\n")
    dta, dtas3 = "", ""

    if len(lst) > 0:
        dta = lst[0]

        if len(lst) > 1:
            dtas3 = lst[1]

    return {"status": True, "dtaall": ta, "dta": dta, "dtas3": dtas3}
