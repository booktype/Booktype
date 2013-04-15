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
from booki.utils import security
from booki.utils.misc import bookiSlugify
from booki import constants

from django.conf import settings

from booki.utils import config

try:
    OBJAVI_URL = settings.OBJAVI_URL
except AttributeError:
    OBJAVI_URL = constants.OBJAVI_URL

try:
    THIS_BOOKI_SERVER = settings.THIS_BOOKI_SERVER
except AttributeError:
    THIS_BOOKI_SERVER = constants.THIS_BOOKI_SERVER


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
    book_version = book.getVersion(version)

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
    book_version = book.getVersion(version)

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
    book_version = book.getVersion(version)

    bookSecurity = security.getUserSecurityForBook(request.user, book)
    
    if bookSecurity.isAdmin():
        for att_id in message['attachments']:
            # should check if you can delete it
            try:
                att = models.Attachment.objects.get(pk=att_id)

                from booki.utils import log
                import os.path

                log.logBookHistory(book = book,
                                   version = book_version,
                                   args = {'filename': os.path.split(att.attachment.name)[1]},
                                   user = request.user,
                                   kind = 'attachment_delete')
                
                att.delete()
            except models.Attachment.DoesNotExist:
                # should i return some kind of error now?!
                pass
                       
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
                                     "message_id": "user_changed_chapter_status",
                                     "message_args": [request.user.username, chapter.title, status.name]},
                                    myself=True)
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
    book_version = book.getVersion(version)
    chapter = models.Chapter.objects.get(id=int(message["chapterID"]))

    if message.get("minor", False) != True:
        history = logChapterHistory(chapter = chapter,
                                    content = message["content"],
                                    user = request.user,
                                    comment = message.get("comment", ""),
                                    revision = chapter.revision+1)

        if history:
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
                                                                    "message_id": "user_saved_chapter",
                                                                    "message_args": [request.user.username, chapter.title]},
                                    myself=True)
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
    book_version = book.getVersion(version)
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
                                     "message_id": "user_renamed_chapter",
                                     "message_args": [request.user.username, oldTitle, message["chapter"]]},
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
    book_version = book.getVersion(version)
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
    book_version = book.getVersion(version)


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
        sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info", 
                                                                    "from": request.user.username, 
                                                                    "message": 'User %s has split chapter "%s".' % (request.user.username, originalChapter.title)}, myself=True)

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
    book_version = book.getVersion(version)

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

        if history:
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
                                                                "message_id": "user_new_chapter",
                                                                "message_args": [request.user.username, message["chapter"]]},
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
                            status = target_book.status,
                            created = datime.datetime.now())

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
    book_version = book.getVersion(version)

    try:
        source_book = models.Book.objects.get(url_title=message["book"])
    except models.Book.DoesNotExist:
        return {"created": False}
    except models.Book.MultipleObjectsReturned:
        return {"created": False}

    source_book_version = source_book.version
    source_url_title = message["chapter"]

    try:
        source_chapter = models.Chapter.objects.get(book=source_book, version=source_book_version, url_title=source_url_title)
    except models.Chapter.DoesNotExist:
        return {"created": False}
    except models.Chapter.MultipleObjectsReturned:
        return {"created": False}

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
                                                                "message_id": "user_cloned_chapter",
                                                                "message_args": [request.user.username, chapter.title, source_book.title]},
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
                                                                "message_id": "published",
                                                                "message_args": [book.title]},
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
    book_version = book.getVersion(version)

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
                                                                    "message_id": "user_new_section",
                                                                    "message_args": [request.user.username, message["chapter"]]},
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
            14: 'attachment_delete',
            15: 'clone'}


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
        elif entry.kind in [15]:
            history.append({"chapter": entry.chapter.title,
                            "chapter_url": entry.chapter.url_title,
                            "description": entry.args,
                            "modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"),
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

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

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


    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

    chapter = models.Chapter.objects.get(version=book_ver, url_title=message["chapter"])

    revision = models.ChapterHistory.objects.get(revision=message["revision"], chapter__url_title=message["chapter"], chapter__version=book_ver.id)

    # TODO
    # does chapter history really needs to keep content or it can only keep reference to chapter

    history = logChapterHistory(chapter = chapter,
                      content = revision.content,
                      user = request.user,
                      comment = "Reverted to revision %s." % message["revision"],
                      revision = chapter.revision+1)

    if history:
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
                                     "message_id": "user_reverted_chapter",
                                     "message_args": [request.user.username, chapter.title, message["revision"]]}, 
                                    myself=True)

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
                                                                    "message_id": "user_saved_notes",
                                                                    "message_args": [request.user.username, book.title]},
                                    myself=True)
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

    book = models.Book.objects.get(id=bookid)

    bookSecurity = security.getUserSecurityForBook(request.user, book)

    if bookSecurity.isAdmin():
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

    import datetime

    new_version = models.BookVersion(book=book,
                                     major=major,
                                     minor=minor,
                                     name=message.get("name", ""),
                                     description=message.get("description", ""),
                                     created=datetime.datetime.now())
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
                                   created=datetime.datetime.now(),
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
                           created=datetime.datetime.now(),
                           content=chap.content)
        c.save()

    for att in book_ver.getAttachments():
        a = models.Attachment(version = new_version,
                              book=book,
                              status=att.status,
                              created=datetime.datetime.now())
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

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

    try:
        new_version = create_new_version(book, book_ver, message, book_ver.major+1, 0)
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

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

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


def remote_covers_data(request, message, bookid, version):
    """
    Get info about covers.


    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns needed data for Cover Manager tab
    """

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

    bookSecurity = security.getUserSecurityForBook(request.user, book)
    
    covers = []

    for cover in models.BookCover.objects.filter(book = book).order_by("title"):
        frm = []
        
        if cover.is_book:
            frm.append("book")
            
        if cover.is_ebook:
            frm.append("ebook")

        if cover.is_pdf:
            frm.append("pdf")

        title = cover.title.strip() or cover.filename

        if len(title) > 50:
            title = title[:50] + '...'

        covers.append({'cid': cover.cid,
                       'placement': cover.cover_type,
                       'format': frm,
                       'title': title,
                       'approved': cover.approved})

    transaction.commit()
    covers.reverse()

    return {"covers": covers, "can_update": bookSecurity.isAdmin()}


def remote_cover_approve(request, message, bookid, version):
    """
    Set cover approve status.


    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns needed data for Cover Manager tab
    """

    book = models.Book.objects.get(id=bookid)
    bookSecurity = security.getUserSecurityForBook(request.user, book)

    if not bookSecurity.isAdmin():
        transaction.rollback()
        return {"result": False}

    try:
        cover =  models.BookCover.objects.get(book = book, cid = message.get('cid', ''))
        cover.approved = message.get('cover_status', False)
        cover.save()
    except models.BookCover.DoesNotExist:

        transaction.rollback()
        return {"result": False}
    else:
        transaction.commit()

    return {"result": True}


def remote_cover_delete(request, message, bookid, version):
    """
    Set cover approve status.


    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns needed data for Cover Manager tab
    """

    book = models.Book.objects.get(id=bookid)

    try:
        cover =  models.BookCover.objects.get(book = book, cid = message.get('cid', ''))

        filename = cover.attachment.name[:]

        cover.delete()
    except models.BookCover.DoesNotExist:

        transaction.rollback()
        return {"result": False}
    else:
        transaction.commit()

    try:
        import os

        os.remove(cover.attachment.name)
    except OSError:
        pass

    return {"result": True}


def remote_cover_save(request, message, bookid, version):
    """
    Update cover data.


    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns needed data for Cover Manager tab
    """

    book = models.Book.objects.get(id=bookid)

    try:
        cover =  models.BookCover.objects.get(book = book, cid = message.get('cid', ''))
        cover.title =  message.get('title', '').strip()[:250]

        try:
            width = int(message.get('width', 0))
        except ValueError:
            width = 0
            
        try:
            height = int(message.get('height', 0))
        except ValueError:
            height = 0

        cover.width = width
        cover.height = height
        cover.unit = message.get('units', 'mm')
        cover.booksize = message.get('booksize', '')

        license = models.License.objects.get(abbrevation=message.get('license', ''))
        
        cover.license = license
        cover.notes = message.get('notes', '')[:500]

        frm = message.get('format', '').split(',')
        cover.is_book = "book" in frm
        cover.is_ebook = "ebook" in frm
        cover.is_pdf = "pdf" in frm

        cover.creator = message.get('creator', '')[:40]
        cover.cover_type = message.get('cover_type', '')

        cover.save()
    except models.BookCover.DoesNotExist:
        transaction.rollback()
        return {"result": False}
    else:
        transaction.commit()

    return {"result": True}


def remote_cover_upload(request, message, bookid, version):
    """
    Get info about specific cover.


    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns needed data for Cover panel.
    """

    licenses =  [(elem.abbrevation, elem.name) for elem in models.License.objects.all().order_by("name")]

    transaction.commit()

    return {"licenses": licenses}


def remote_cover_load(request, message, bookid, version):
    """
    Get info about specific cover.


    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns needed data for Cover panel.
    """

    book = models.Book.objects.get(id=bookid)

    cover = models.BookCover.objects.get(book=book, cid=message.get('cid', ''))

    # TODO 
    # - placement
    # - filename

    frm = []

    if cover.is_book:
        frm.append("book")

    if cover.is_ebook:
        frm.append("ebook")

    if cover.is_pdf:
        frm.append("pdf")

    import Image

    size = (0, 0)
    filetype = ""

    try:
        im = Image.open(cover.attachment.name)
        size = im.size

        filetype = cover.filename.split('.')[-1].upper()
    except:
        pass

    # temporary data
    cover = {"cid": cover.cid,
             "filename": cover.filename,
             "cover_type": cover.cover_type,
             "format": frm,
             "width": cover.width,
             "filetype": filetype,
             "img_size": size,
             "height": cover.height,
             "units": cover.unit, 
             "booksize": cover.booksize,
             "title": cover.title,
             "type": cover.cover_type,
             "creator": cover.creator,
             "notes": cover.notes,
             "license": cover.license.abbrevation,
             "approved": cover.approved}

    licenses =  [(elem.abbrevation, elem.name) for elem in models.License.objects.all().order_by("name")]

    transaction.commit()

    return {"cover": cover, "licenses": licenses}


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

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

    licenses = [(lic.abbrevation, lic.name)  for lic in models.License.objects.all().order_by("name") if lic]
    languages = [(lic.abbrevation, lic.name) for lic in models.Language.objects.all().order_by("name") if lic] + [('unknown', 'Unknown')]
    
    current_license = getattr(book.license, "abbrevation","")
    current_language = getattr(book.language, "abbrevation", "unknown")

    # get rtl
    try:
        rtl = models.Info.objects.get(book=book, name='{http://booki.cc/}dir', kind=0).getValue()
    except (models.Info.DoesNotExist, models.Info.MultipleObjectsReturned):
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

    book = models.Book.objects.get(id=bookid)

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

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

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

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

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

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

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

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

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

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

    users = [(u.user.username, '%s (%s)' % (u.user.username, u.user.first_name)) for u in models.BookiPermission.objects.filter(book = book, permission = message["role"]).order_by("user__username")]

    if int(message["role"]) == 1:
        users.append((book.owner.username, '%s (%s) [owner]' % (book.owner.username, book.owner.first_name)))

    transaction.commit()

    return {"status": True, "users": users}


# remove this
def _remote_roles_save(request, message, bookid, version):
    from django.contrib.auth.models import User

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

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

    from django.contrib.auth.models import User

    # check permissions

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)

    result = False

    try:
        u = User.objects.get(username = message["username"])

        # we do some black magic if user is book owner and we try to make him administrator        
        if not (book.owner == u and message["role"] == 1):
            # Do not add if user is already in the list
            if not models.BookiPermission.objects.filter(book = book, user = u, permission = message["role"]).exists():
                up = models.BookiPermission(book = book,
                                            user = u,
                                            permission = message["role"])
                up.save()

                result = True
    except User.DoesNotExist:
        pass

    transaction.commit()

    return {"status": result}


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

    from django.contrib.auth.models import User

    # check permissions

    book = models.Book.objects.get(id=bookid)
    book_ver = book.getVersion(version)


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
    'book': [{"name": "booksize", "value": "COMICBOOK"}, {"name": "custom_width", "value": ""}, {"name": "custom_height", "value": ""}, {"name": "body_font-family", "value": "Fontin_Sans"}, {"name": "body_font-size", "value": "10"}, {"name": "h1_font-family", "value": "Fontin_Sans"}, {"name": "h1_font-size", "value": "14"}, {"name": "h1_text-transform", "value": "uppercase"}, {"name": "h1_font-weight", "value": "heavy"}, {"name": "h2_font-family", "value": "Fontin_Sans"}, {"name": "h2_font-size", "value": "12"}, {"name": "h2_text-transform", "value": "uppercase"}, {"name": "h2_font-weight", "value": "heavy"}, {"name": "h3_font-family", "value": "Fontin_Sans"}, {"name": "h3_font-size", "value": "10"}, {"name": "h3_text-transform", "value": "uppercase"}, {"name": "h3_font-weight", "value": "heavy"}, {"name": "pre_font-family", "value": "Courier"}, {"name": "pre_font-size", "value": "10"}, {"name": "p_pagebreak", "value": "on"}, {"name": "footnotes_pagebreak", "value": "on"}, {"name": "control-css", "value": "on"}, {"name": "page-numbers", "value": "auto"}, {"name": "embed-fonts", "value": "on"}, {"name": "toc_header", "value": ""}, {"name": "top_margin", "value": ""}, {"name": "side_margin", "value": ""}, {"name": "bottom_margin", "value": ""}, {"name": "gutter", "value": ""}, {"name": "columns", "value": ""}, {"name": "column_margin", "value": ""}, {"name": "additional_css", "value": ""}, {"name": "special_css", "value": ""}, {"name": "grey_scale", "value": "off"}, {"name": "rotate", "value": "off"}, {"name": "allow-breaks", "value": "off"}, {"name": "custom_override", "value": "off"}, {"name": "", "value": "off"}, {"name": "", "value": "off"}],

    'bookjs': [{"name": "booksize", "value": "COMICBOOK"}, {"name": "custom_width", "value": ""}, {"name": "custom_height", "value": ""}, {"name": "body_font-family", "value": "Liberation Serif"}, {"name": "body_font-size", "value": "18"}, {"name": "h1_font-family", "value": "Liberation Serif"}, {"name": "h1_font-size", "value": "24"}, {"name": "h1_text-transform", "value": "uppercase"}, {"name": "h1_font-weight", "value": "heavy"}, {"name": "h2_font-family", "value": "Liberation Serif"}, {"name": "h2_font-size", "value": "24"}, {"name": "h2_text-transform", "value": "uppercase"}, {"name": "h2_font-weight", "value": "heavy"}, {"name": "h3_font-family", "value": "Liberation Serif"}, {"name": "h3_font-size", "value": "20"}, {"name": "h3_text-transform", "value": "uppercase"}, {"name": "h3_font-weight", "value": "heavy"}, {"name": "pre_font-family", "value": "Courier"}, {"name": "pre_font-size", "value": "10"}, {"name": "p_pagebreak", "value": "on"}, {"name": "footnotes_pagebreak", "value": "on"}, {"name": "control-css", "value": "on"}, {"name": "page-numbers", "value": "auto"}, {"name": "embed-fonts", "value": "on"}, {"name": "toc_header", "value": ""}, {"name": "top_margin", "value": ""}, {"name": "side_margin", "value": ""}, {"name": "bottom_margin", "value": ""}, {"name": "gutter", "value": ""}, {"name": "columns", "value": ""}, {"name": "column_margin", "value": ""}, {"name": "additional_css", "value": ""}, {"name": "special_css", "value": ""}, {"name": "grey_scale", "value": "off"}, {"name": "rotate", "value": "off"}, {"name": "allow-breaks", "value": "off"}, {"name": "custom_override", "value": "off"}, {"name": "", "value": "off"}, {"name": "", "value": "off"}],

    'ebook': [{"name": "body_font-family", "value": "Fontin_Sans"}, {"name": "body_font-size", "value": "10"}, {"name": "h1_font-family", "value": "Fontin_Sans"}, {"name": "h1_font-size", "value": "14"}, {"name": "h1_text-transform", "value": "uppercase"}, {"name": "h1_font-weight", "value": "heavy"}, {"name": "h2_font-weightamily", "value": "Fontin_Sans"}, {"name": "h2_font-size", "value": "12"}, {"name": "h2_text-transform", "value": "uppercase"}, {"name": "h2_font-weight", "value": "heavy"}, {"name": "h3_font-family", "value": "Fontin_Sans"}, {"name": "h3_font-size", "value": "10"}, {"name": "h3_text-transform", "value": "uppercase"}, {"name": "h3_font-weight", "value": "heavy"}, {"name": "pre_font-family", "value": "Courier"}, {"name": "pre_font-size", "value": "10"}, {"name": "additional_css", "value": ""}, {"name": "special_css", "value": ""}, {"name": "ebook_format", "value": "epub"},  {"name": "custom_override", "value": "off"}, {"name": "", "value": "off"}, {"name": "", "value": "off"}],

    'odt': [{"name": "body_font-weight", "value": "Fontin_Sans"}, {"name": "body_font-size", "value": "10"}, {"name": "h1_font-weight", "value": "Fontin_Sans"}, {"name": "h1_font-size", "value": "14"}, {"name": "h1_text-transform", "value": "uppercase"}, {"name": "h1_font-weight", "value": "heavy"}, {"name": "h2_font-weight", "value": "Fontin_Sans"}, {"name": "h2_font-size", "value": "12"}, {"name": "h2_text-transform", "value": "uppercase"}, {"name": "h2_font-weight", "value": "heavy"}, {"name": "h3_font-weight", "value": "Fontin_Sans"}, {"name": "h3_font-size", "value": "10"}, {"name": "h3_text-transform", "value": "uppercase"}, {"name": "h3_font-weight", "value": "heavy"}, {"name": "pre_font-weight", "value": "Courier"}, {"name": "pre_font-size", "value": "10"}, {"name": "p_pagebreak", "value": "on"}, {"name": "footnotes_pagebreak", "value": "on"}, {"name": "additional_css", "value": ""}, {"name": "special_css", "value": ""}, {"name": "custom_override", "value": "off"}, {"name": "", "value": "off"}, {"name": "", "value": "off"}],

    'pdf': [{"name": "booksize", "value": "A4"}, {"name": "custom_width", "value": ""}, {"name": "custom_height", "value": ""}, {"name": "body_font-family", "value": "Fontin_Sans"}, {"name": "body_font-size", "value": "10"}, {"name": "h1_font-family", "value": "Fontin_Sans"}, {"name": "h1_font-size", "value": "14"}, {"name": "h1_text-transform", "value": "uppercase"}, {"name": "h1_font-weight", "value": "heavy"}, {"name": "h2_font-family", "value": "Fontin_Sans"}, {"name": "h2_font-size", "value": "12"}, {"name": "h2_text-transform", "value": "uppercase"}, {"name": "h2_font-weight", "value": "heavy"}, {"name": "h3_font-family", "value": "Fontin_Sans"}, {"name": "h3_font-size", "value": "10"}, {"name": "h3_text-transform", "value": "uppercase"}, {"name": "h3_font-weight", "value": "heavy"}, {"name": "pre_font-family", "value": "Courier"}, {"name": "pre_font-size", "value": "10"}, {"name": "p_pagebreak", "value": "on"}, {"name": "footnotes_pagebreak", "value": "on"}, {"name": "control-css", "value": "on"}, {"name": "page-numbers", "value": "auto"}, {"name": "embed-fonts", "value": "yes"}, {"name": "top_margin", "value": ""}, {"name": "side_margin", "value": ""}, {"name": "bottom_margin", "value": ""}, {"name": "gutter", "value": ""}, {"name": "columns", "value": ""}, {"name": "column_margin", "value": ""}, {"name": "additional_css", "value": ""}, {"name": "special_css", "value": ""}, {"name": "grey_scale", "value": "off"}, {"name": "rotate", "value": "off"}, {"name": "allow-breaks", "value": "off"}, {"name": "custom_override", "value": "off"}, {"name": "", "value": "off"}, {"name": "", "value": "off"}]}


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

    # book, ebook, pdf, odt

    output_type = message.get('wizzard_type', '').upper()

    for op in options:
        if op.get('name', '') == 'special_css':
            op['value'] = config.getConfiguration('BOOKTYPE_CSS_%s' % output_type, '')

    covers = []
    
    class DummyCover(object):
        def __init__(self, title):
            self.cid = title
            
    def _getCovers(coverType):
        ls =  [cover for cover in models.BookCover.objects.filter(book=book, is_book=True, cover_type = coverType)]

        if len(ls) > 0:
            return [DummyCover(coverType)] + ls

        return ls


    def _getOtherCovers(coverType):
        ls = []

        for cover in models.BookCover.objects.filter(book=book):
            if cover.is_book == True:
                if cover.cover_type != 'digital':
                    continue
            ls.append(cover)

        if len(ls) > 0:
            return [DummyCover(coverType)] + ls

        return ls

    if output_type in ['BOOK', 'BOOKJS']:        
        _front = _getCovers('front')
        _back = _getCovers('back')
        _spine = _getCovers('spine')
        _whole = _getCovers('whole')
        _other = _getOtherCovers('other')

        covers = _front + _back + _spine + _whole + _other

    if output_type in ['EBOOK', 'PDF', 'ODT']:
        covers = []

        for cover in models.BookCover.objects.filter(book=book):
            title = cover.title or cover.filename
            is_ok = False

            for e in ['.jpg', 'jpe', '.jpeg', '.gif', '.png']:
                if cover.filename.lower().endswith(e):
                    is_ok = True

            if not is_ok:
                continue

            if len(title) > 50:
                title = title[:50]+'...'
 
            _class = ''
            if cover.is_book or cover.is_ebook or cover.is_pdf:
                if cover.is_book:
                    _class += ' coverbook' 
                if cover.is_ebook:
                    _class += ' coverebook'
                if cover.is_pdf:
                    _class += ' coverpdf'

            if not cover.approved:
                _class += ' notapproved'

#            if cover.approved:
#                _class += ' approved'

            covers.append({'cid': cover.cid,
                           'class': _class, 
                           'approved': cover.approved,
                           'title': title})

#    if output_type in ['PDF']:
#        covers = models.BookCover.objects.filter(book=book, is_pdf=True)

    c = Context({"covers": covers})
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

    transaction.commit()

    return {"status": True, "options": {}}

# Two predefined themes

THEME_STYLE1 = '/* DOCUMENT */\n\n@page {\n    size: auto;\n}\n\n\nbody {\n    font-family: "Nimbus Sans L";\n    background-color: white;\n}\n\n\n/* CONTENT */\n\nimg {\n    max-width: 90%;\n    height: auto;\n    image-resolution: from-image;\n}\n\nsup  {\n    font-size: 18pt;\n}\n\np {\n    font-size: 20pt;\n    line-height: 30pt;\n    word-break: break-word;\n    /* text-align: justify; */\n    text-align: left;\n}\n\na {\n    color: #000;\n    text-decoration: none;\n    word-wrap: break-word;\n}\n\nol, ul {\n    font-size: 20pt; \n    text-align: justify;\n}\n\nli {\n    margin-left: 1em;\n    word-wrap: break-word;\n    page-break-inside: avoid;\n    windows: 4;\n    orphans: 4;\n}\n\n/* HEADINGS */\n\nh1 {\n    font-size: 26pt;\n}\n\nh1 .initial {\n    display: none;\n}\n\nh1 .subtitle {\n}\n\nh1 .author {\n    display: block;\n    margin-top: 0.2in;\n    font-weight: normal;\n}\n\nh1 .comma {\n    display: none;\n}\n\nh2 {\n    font-size: 24pt;\n    page-break-after: avoid;\n}\n\nh3 {\n    font-size: 22pt;\n    font-weight: normal;\n    page-break-after: avoid;\n}\n\nh4 {\n    font-size: 22pt;\n    page-break-after: avoid;\n}\n\nh5 {\n    font-size: 22pt;\n    font-weight: normal;\n    text-align: justify;\n    padding-left: .4in;\n    display: block;\n    page-break-after: avoid;\n}\n\n/* CODE BLOCKS */\n\npre {\n    white-space: pre-wrap;       /* css-3 */\n    white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */\n    white-space: -pre-wrap;      /* Opera 4-6 */\n    white-space: -o-pre-wrap;    /* Opera 7 */\n    word-wrap: break-word;       /* Internet Explorer 5.5+ */\n    font-family: courier !important;\n    font-size: 20pt;\n    widows:4;\n    orphans:4;\n}\n\ncode {\n   font-family: courier !important;\n   font-size: 20pt; \n}\n\n\n\n/* TOC */\n\n#pagination-toc-title {\n    font-size: 20pt;\n    font-weight: 700;\n    text-align: left;\n    padding-bottom: .4in;\n}\n\n.pagination-toc-entry {\n/*    width: 6.2in; */\n    width: 90%;\n    display: block;\n    padding-bottom: .3in;\n    font-size: 20pt;\n}\n\n.pagination-toc-entry .pagination-toc-pagenumber {\n    font-weight: 400;\n    display: inline-block;\n    vertical-align: text-bottom;\n    font-size: 20pt;\n    float:right; /* SET AUTOMATICALLY */\n}\n\n.pagination-toc-entry.section {\n    font-weight:700;\n    font-size: 20pt;\n    text-transform: uppercase;\n    padding-bottom: .3in;\n}\n\n\n/* FRONT MATTER */\n\n#booktitle {\n    margin-top: 1.7in;\n    font-size: 28pt;\n    font-weight: normal;\n    text-align: center;\n    text-transform: uppercase;\n}\n\n#booksubtitle {\n    font-size: 24pt;\n    margin-top: 0.2in;\n    font-weight: normal;\n    text-align: center;\n}\n\n#bookeditors {\n    padding-top: 1.5in;\n    font-weight: normal;\n    text-align: center;\n    font-size: 24pt;\n}\n\n#bookpress {\n    padding-top: 1.8in;\n    font-weight: normal;\n    text-align: center;\n    font-size: 20pt;\n}\n\n#copyrightpage {\n    font-weight: normal;\n    font-size: 20pt;\n    padding-top: 0.2in;\n}\n\n\n/* HEADER */\n\n.pagination-header {\n   font-size: 16pt;\n   font-weight: light;\n}\n\n.pagination-pagenumber {\n   font-size: 16pt;\n}\n\n.pagination-header .pagination-section { display: none; }\n\n\n.pagination-toc-text .initial { display: none; }\n.pagination-chapter .initial { display: none; }\n\n\n/* MISC */\n\n.imagecaption {\n    font-size: 9pt;\n    padding-left: 0.2in;\n    line-height: 18px;\n    text-align: justify;\n    font-weight: normal;\n    display: block;\n}\n\n\n.pagebreak {\n    -webkit-region-break-after: always;\n}\n\n.pagebreakbefore {\n    -webkit-region-break-before: always;\n}\n\n.objavi-chapter .initial {\n    display: none;\n}\n\n.objavi-subsection {\n    display: none;\n}\n\n.objavi-subsection-heading {\n    line-height: 120px !important;\n    /* work-around to make section title pages no longer than one page */\n    font-size: 22px;\n    font-weight: bold;\n    text-align: left;\n    display: none;\n}\n\n@media screen {\n    .page {\n        border: solid 1px #000;\n        margin-bottom: .2in;\n    }\n\n    body {\n	background-color: #efefef;\n    }\n}\n\n\n'
THEME_STYLE2 = '/* DOCUMENT */\n\n@page {\n    size: auto;\n}\n\n\nbody {\n    font-family: "Gentium", "Times New Roman";\n    background-color: white;\n}\n\n\n/* CONTENT */\n\nimg {\n    max-width: 90%;\n    height: auto;\n    image-resolution: from-image;\n}\n\nsup  {\n    font-size: 18pt;\n}\n\np {\n    font-size: 24pt;\n    line-height: 30pt;\n    word-break: break-word;\n    /* text-align: justify; */\n    text-align: left;\n}\n\np + p {\n text-indent: 1em;\n}\n\n\na {\n    color: #000;\n    text-decoration: none;\n    word-wrap: break-word;\n}\n\nol, ul {\n    font-size: 24pt; \n    text-align: justify;\n}\n\nli {\n    margin-left: 1em;\n    word-wrap: break-word;\n    page-break-inside: avoid;\n    windows: 4;\n    orphans: 4;\n}\n\n/* HEADINGS */\n\nh1 {\n    font-size: 32pt;\n    text-align: center;\n    padding-bottom: 50px;\n}\n\nh1 .initial {\n    display: none;\n}\n\nh1 .subtitle {\n}\n\nh1 .author {\n    display: block;\n    margin-top: 0.2in;\n    font-weight: normal;\n}\n\nh1 .comma {\n    display: none;\n}\n\nh2 {\n    font-size: 26pt;\n    page-break-after: avoid;\n}\n\nh3 {\n    font-size: 24pt;\n    font-weight: normal;\n    page-break-after: avoid;\n}\n\nh4 {\n    font-size: 24pt;\n    page-break-after: avoid;\n}\n\nh5 {\n    font-size: 24pt;\n    font-weight: normal;\n    text-align: justify;\n    line-height: 18px;\n    padding-left: .4in;\n    display: block;\n    page-break-after: avoid;\n}\n\n/* CODE BLOCKS */\n\npre {\n    white-space: pre-wrap;       /* css-3 */\n    white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */\n    white-space: -pre-wrap;      /* Opera 4-6 */\n    white-space: -o-pre-wrap;    /* Opera 7 */\n    word-wrap: break-word;       /* Internet Explorer 5.5+ */\n    font-family: courier !important;\n    font-size: 22pt;\n    widows:4;\n    orphans:4;\n}\n\ncode {\n   font-family: courier !important;\n   font-size: 24pt; \n}\n\n\n\n/* TOC */\n\n#pagination-toc-title {\n    font-size: 24pt;\n    font-weight: 700;\n    text-align: left;\n    padding-bottom: .4in;\n}\n\n.pagination-toc-entry {\n/*    width: 6.2in; */\n    width: 90%;\n    display: block;\n    padding-bottom: .3in;\n    font-size: 24pt;\n}\n\n.pagination-toc-entry .pagination-toc-pagenumber {\n    font-weight: 400;\n    display: inline-block;\n    vertical-align: text-bottom;\n    font-size: 24pt;\n    float:right; /* SET AUTOMATICALLY */\n}\n\n.pagination-toc-entry.section {\n    font-weight:700;\n    font-size: 24pt;\n    text-transform: uppercase;\n    padding-bottom: .3in;\n}\n\n\n/* FRONT MATTER */\n\n#booktitle {\n    margin-top: 1.7in;\n    font-size: 32pt;\n    font-weight: normal;\n    text-align: center;\n}\n\n#booksubtitle {\n    font-size: 22px;\n    margin-top: 0.2in;\n    font-weight: normal;\n    text-align: center;\n}\n\n#bookeditors {\n    padding-top: 1.5in;\n    font-weight: normal;\n    text-align: center;\n    font-size: 24pt;\n}\n\n#bookpress {\n    padding-top: 1.8in;\n    font-weight: normal;\n    text-align: center;\n    font-size: 24pt;\n}\n\n#copyrightpage {\n    font-weight: normal;\n    font-size: 24pt;\n    padding-top: 0.2in;\n}\n\n\n/* HEADER */\n\n.pagination-header {\n   font-size: 18pt;\n   font-weight: light;\n}\n\n.pagination-pagenumber {\n   font-size: 18pt;\n   color: black;\n}\n\n.pagination-header .pagination-section { display: none; }\n.pagination-header .pagination-chapter { color: white; }\n\n\n.pagination-toc-text .initial { display: none; }\n.pagination-chapter .initial { display: none; }\n\n\n/* MISC */\n\n.imagecaption {\n    font-size: 9pt;\n    padding-left: 0.2in;\n    line-height: 18px;\n    text-align: justify;\n    font-weight: normal;\n    display: block;\n}\n\n\n.pagebreak {\n    -webkit-region-break-after: always;\n}\n\n.pagebreakbefore {\n    -webkit-region-break-before: always;\n}\n\n.objavi-chapter .initial {\n    display: none;\n}\n\n.objavi-subsection {\n    display: none;\n}\n\n.objavi-subsection-heading {\n    line-height: 120px !important;\n    /* work-around to make section title pages no longer than one page */\n    font-size: 22px;\n    font-weight: bold;\n    text-align: left;\n    display: none;\n}\n\n@media screen {\n    .page {\n        border: solid 1px #000;\n        margin-bottom: .2in;\n    }\n\n    body {\n	background-color: #efefef;\n    }\n}\n\n\n'

def remote_publish_book2(request, message, bookid, version):
    """
    This is called when you want to publish your book. HTTP Request is sent to Objavi. Objavi then grabs content from Booki, renders it and creates output file.

    Sends notification to chat.

    Input:
     - publish_mode
     - is_archive
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

    try:
        publish_options = settings.PUBLISH_OPTIONS
    except AttributeError:
        publish_options = constants.PUBLISH_OPTIONS

    if not message.get('publish_mode', 'epub') in publish_options:
        return {"status": False}


    from booki.utils.json_wrapper import simplejson

    book = models.Book.objects.get(id=bookid)

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info",
                                                                "from": request.user.username,
                                                                "message_id": "published",
                                                                "message_args": [book.title]},
                                myself=True)

    import urllib2
    import urllib

    # read all default options


    book = models.Book.objects.get(id=bookid)

    options = []


    # so we can steel book options even when we are bookjs/pdf
    pm = message.get("publish_mode", "epub")

    try:
        pw = models.PublishWizzard.objects.get(book=book,
                                               user=request.user,
                                               wizz_type=pm
                                               )
        try:
            options = simplejson.loads(pw.wizz_options)
        except:
            options = PUBLISH_OPTIONS[pm]

    except models.PublishWizzard.DoesNotExist:
        options = PUBLISH_OPTIONS[pm]

    # converstion for names
    publishOptions = {'ebook': 'epub',
                      'book': 'book',
                      'bookjs': 'bookjs/pdf',
                      'odt': 'openoffice',
                      'newpaper': 'pdf',
                      'pdf': 'web'}

    # At one point Booktype and Objavi did not have same list of licenses.
    # This would create problems and this was a dirty way how it was
    # "solved". This will be changed in the future protocol for communication
    # between Booktype and Objavi
    licenses = {'PD': 'public domain'}
    licenseText = 'CC BY'

    if book.license:
        # If you can find it in the list then return how the license should be called.
        # Otherwise just return abbrevation name.
        licenseText = licenses.get(book.license.abbrevation, book.license.abbrevation)

    publishMode = publishOptions[message.get("publish_mode", "epub")]

    destination = "nowhere"

    args = {'book': book.url_title.encode('utf8'),
            'license': licenseText,
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

    def _getCover():
        cover = None
        cid = _getValue('cover_image')

        if type(cid) == type([]):
            return cover

        if cid and cid.strip() != '':
            try:
                cover = models.BookCover.objects.get(book=book, cid=cid)
            except models.BookCover.DoesNotExist:
                pass

        return cover

    def _getCoverList():
        cid = _getValue('cover_image')
        clist = []
        cres = []

        if type(cid) != type([]):
            clist = [cid]
        else:
            clist = cid

        for c in clist:
            try:
                cvr = models.BookCover.objects.get(book=book, cid=c)
                cres.append(cvr)
            except models.BookCover.DoesNotExist:
                pass

        return cres


    def _getCoverSize(c):
        try:
            import Image

            im = Image.open(c.attachment.name)
            size = im.size
            return '#%s,%s' % size
        except:
            # In case of any kind of error
            return ''

    cover = _getCover()
    coverList = _getCoverList()

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
 

    if publishMode in ['book']:
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
            _css = config.getConfiguration('BOOKTYPE_CSS_BOOK', '')

            _css += _getValue('additional_css') or ''
        else:
            _css = config.getConfiguration('BOOKTYPE_CSS_BOOK', '')

            _css += _formatCSS("BODY, P", _getValue('body_font-family'), _getValue('body_font-size'))
            _css += _formatCSS("H1", _getValue('h1_font-family'), _getValue('h1_font-size'), _getValue('h1_text-transform'), _getValue('h1_font-weight'))
            _css += _formatCSS("H2", _getValue('h2_font-family'), _getValue('h2_font-size'), _getValue('h2_text-transform'), _getValue('h2_font-weight'))
            _css += _formatCSS("H3", _getValue('h3_font-family'), _getValue('h3_font-size'), _getValue('h3_text-transform'), _getValue('h3_font-weight'))
            _css += _formatCSS("PRE", _getValue('pre_font-family'), _getValue('pre_font-size'))
            _css += _getValue('additional_css') or ''

        if _getValue('control-css') == 'on':
            args['css'] = _css

        # We have been using wrong argument name for this. Considering people have saved in their publishing settings old values this 
        # seems to be best way to fix this issue for now.

        if args.get('booksize', '') == 'custom':
            args['page_width']  = args.get('custom_width', '')
            args['page_height'] = args.get('custom_height', '')

    if publishMode in ['bookjs/pdf']:
        theme = message.get('theme', 'style3')

        _isSet('booksize')
        _isSet('custom_width')
        _isSet('custom_height')

        _isSet('top_margin')
        _isSet('side_margin')
        _isSet('bottom_margin')
        _isSet('gutter')

        # in this case, just the css you entered
        if _getValue('custom_override') == 'on':
            _css = config.getConfiguration('BOOKTYPE_CSS_BOOKJS', '')

            _css += _getValue('additional_css') or ''
        else:
            _css = config.getConfiguration('BOOKTYPE_CSS_BOOKJS', '')

            if theme == 'style3':
                _css += _formatCSS("BODY, P", _getValue('body_font-family'), _getValue('body_font-size'))
                _css += _formatCSS("H1", _getValue('h1_font-family'), _getValue('h1_font-size'), _getValue('h1_text-transform'), _getValue('h1_font-weight'))
                _css += _formatCSS("H2", _getValue('h2_font-family'), _getValue('h2_font-size'), _getValue('h2_text-transform'), _getValue('h2_font-weight'))
                _css += _formatCSS("H3", _getValue('h3_font-family'), _getValue('h3_font-size'), _getValue('h3_text-transform'), _getValue('h3_font-weight'))
                _css += _formatCSS("PRE", _getValue('pre_font-family'), _getValue('pre_font-size'))
                _css += _getValue('additional_css') or ''

        if theme == 'style3' and _getValue('control-css') == 'on':
            args['css'] = _css

        if theme == 'style1':
            args['css'] = THEME_STYLE1

        if theme == 'style2':
            args['css'] = THEME_STYLE2

        # We have been using wrong argument name for this. Considering people have saved in their publishing settings old values this
        # seems to be best way to fix this issue for now.

        if args.get('booksize', '') == 'custom':
            args['page_width']  = args.get('custom_width', '')
            args['page_height'] = args.get('custom_height', '')

    if publishMode == 'epub':
        # ebook_format ipad,kindle,epub

        ebookFormat = _getValue('ebook_format')

        if cover:
            _extra = _getCoverSize(cover)
            args['cover_url'] = settings.BOOKI_URL+'/%s/_cover/%s/%s%s' % (book.url_title, cover.cid, urllib.quote(cover.filename), _extra)

        if ebookFormat == 'kindle':
            args['output_profile'] = 'kindle'
            args['output_format'] = 'mobi'

        if ebookFormat == 'ipad':
            args['output_profile'] = 'ipad'
            args['output_format'] = 'epub'

        if _getValue('custom_override') == 'on':
            _css = config.getConfiguration('BOOKTYPE_CSS_EBOOK', '')

            _css += _getValue('additional_css') or ''
        else:
            _css = config.getConfiguration('BOOKTYPE_CSS_EBOOK', '')

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
            _css = config.getConfiguration('BOOKTYPE_CSS_PDF', '')

            _css += _getValue('additional_css') or ''
        else:
            _css = config.getConfiguration('BOOKTYPE_CSS_PDF', '')

            _css += _formatCSS("BODY, P", _getValue('body_font-family'), _getValue('body_font-size'))
            _css += _formatCSS("H1", _getValue('h1_font-family'), _getValue('h1_font-size'), _getValue('h1_text-transform'), _getValue('h1_font-weight'))
            _css += _formatCSS("H2", _getValue('h2_font-family'), _getValue('h2_font-size'), _getValue('h2_text-transform'), _getValue('h2_font-weight'))
            _css += _formatCSS("H3", _getValue('h3_font-family'), _getValue('h3_font-size'), _getValue('h3_text-transform'), _getValue('h3_font-weight'))
            _css += _formatCSS("PRE", _getValue('pre_font-family'), _getValue('pre_font-size'))
            _css += _getValue('additional_css') or ''

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

        # We have been using wrong argument name for this. Considering people have saved in their publishing settings old values this 
        # seems to be best way to fix this issue for now.

        if args.get('booksize', '') == 'custom':
            args['page_width']  = args.get('custom_width', '')
            args['page_height'] = args.get('custom_height', '')

        if cover:
            _extra = _getCoverSize(cover)
            args['cover_url'] = settings.BOOKI_URL+'/%s/_cover/%s/%s%s' % (book.url_title, cover.cid, urllib.quote(cover.filename), _extra)


    if publishMode in ['openoffice']:
        if cover:
            _extra = _getCoverSize(cover)
            args['cover_url'] = settings.BOOKI_URL+'/%s/_cover/%s/%s%s' % (book.url_title, cover.cid, urllib.quote(cover.filename), _extra)
        
    for key in args.keys():
        if isinstance(args[key], basestring):
            # Ignore any kind of error. There will be no time to test this fully so just ignore everything for now
            try:
                args[key] = unicode(args[key]).encode('utf8')
            except:
                pass

    try:
        data = urllib.urlencode(args)
    except UnicodeEncodeError:
        return {"status": False}

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

    # out of all this, only 
    result = {"status": True, "dtaall": ta, "dta": dta, "dtas3": dtas3}
    
    if len(coverList) > 0:
        r = [(c.cover_type, settings.BOOKI_URL+'/%s/_cover/%s/' % (book.url_title, c.cid), c.cid, c.title, c.filename) for c in coverList]
                
        result['covers'] = r

    return result
