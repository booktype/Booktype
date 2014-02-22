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
    try:
        from PIL import Image
    except ImportError:
        import Image

    def _getDimension(att):
        try:
            im = Image.open(att.attachment.name)
            return im.size
        except:
            pass

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
                                    "/booktype/book/%s/%s/" % (bookid, version),
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

    bookSecurity = security.getUserSecurityForBook(request.user, book)
    
    return {"licenses": licenses,
            "chapters": chapters,
            "metadata": metadata,
            "hold": holdChapters,
            "users": users,
            "is_admin":  bookSecurity.isAdmin(),
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

    sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),
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

        sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),
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
    content = message['content']

    if len(message['footnotes']) > 0:
        from lxml import html

        utf8_parser = html.HTMLParser(encoding='utf-8')
        tree = html.document_fromstring(content, parser=utf8_parser)

        root = tree.getroottree()

        for _footnote in root.find('body').xpath('//sup[@class="footnote"]'):
            footID = _footnote.get('id')
            footnote_content = message['footnotes']['content_'+footID]

            _footnote.text = ''
            ftn = etree.SubElement(_footnote, 'span')
            ftn.text = footnote_content

        content = etree.tostring(tree, pretty_print=True, encoding='utf-8')

    if message.get("minor", False) != True:
        history = logChapterHistory(chapter = chapter,
                                    content = content,
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

    chapter.content = content

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


def remote_chapter_delete(request, message, bookid, version):
    """
    Delete chapter.

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

    # check security

    bookSecurity = security.getUserSecurityForBook(request.user, book)

    if not bookSecurity.isAdmin():
        transaction.commit()

        return {"result": False, "permission": False}

    try:
        chap = models.Chapter.objects.get(id=int(message["chapterID"]))
        chap.delete()

        # MUST DELETE FROM TOC ALSO

        sputnik.addMessageToChannel(request, "/chat/%s/" %  bookid,
                                    {"command": "message_info",
                                     "from": request.user.username,
                                     "message_id": "user_delete_chapter",
                                     "message_args": [request.user.username, chap.title]},
                                    myself=True)
        logBookHistory(book = book,
                       version = book_version,
                       args = {'chapter': chap.title},
                       user = request.user,
                       kind = 'chapter_delete')

        sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),
                                    {"command": "chapter_delete",
                                     "chapterID": message["chapterID"]},
                                    myself = True)
    except:
        transaction.rollback()
    else:

        transaction.commit()

    return {"status": True, "result": True}

def remote_section_delete(request, message, bookid, version):
    """
    Delete chapter.

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

    # check security

    bookSecurity = security.getUserSecurityForBook(request.user, book)

    if not bookSecurity.isAdmin():
        transaction.commit()

        return {"result": False, "permission": False}

    try:
        section_id = str(message["chapterID"])[1:]

        sec = models.BookToc.objects.get(pk=section_id)
        sec.delete()

        # MUST DELETE FROM TOC ALSO

        # sputnik.addMessageToChannel(request, "/chat/%s/" %  bookid,
        #                             {"command": "message_info",
        #                              "from": request.user.username,
        #                              "message_id": "user_delete_chapter",
        #                              "message_args": [request.user.username, chap.title]},
        #                             myself=True)
        # logBookHistory(book = book,
        #                version = book_version,
        #                args = {'chapter': chap.title},
        #                user = request.user,
        #                kind = 'chapter_delete')

        sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),
                                    {"command": "section_delete",
                                     "chapterID": message["chapterID"]},
                                    myself = True)
    except:
        transaction.rollback()
    else:

        transaction.commit()

    return {"status": True, "result": True}

def remote_chapter_rename(request, message, bookid, version):
    """
    Rename chapter name.

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
    # check security
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

        # sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),
        #                             {"command": "chapter_status",
        #                              "chapterID": message["chapterID"],
        #                              "status": "normal",
        #                              "username": request.user.username})

        sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),
                                    {"command": "chapter_rename",
                                     "chapterID": message["chapterID"],
                                     "chapter": message["chapter"]}, myself=True)

        transaction.commit()

    return {"status": True}

def remote_section_rename(request, message, bookid, version):
    """
    Rename section name.

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

    # check security
    sectionID = message["chapterID"][1:]

    m =  models.BookToc.objects.get(id__exact=int(sectionID))
    oldTitle = m.name
    m.name = message["chapter"]

    try:
        m.save()
    except:
        transaction.rollback()
    else:
        logBookHistory(book = book,
                       version = book_version,
                       chapter = None,
                       user = request.user,
                       args = {"old": oldTitle, "new": message["chapter"]},
                       kind = "section_rename")

        sputnik.addMessageToChannel(request, "/chat/%s/" %  bookid,
                                    {"command": "message_info",
                                     "from": request.user.username,
                                     "message_id": "user_renamed_section",
                                     "message_args": [request.user.username, oldTitle, message["chapter"]]},
                                    myself=True)

        # sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),
        #                             {"command": "chapter_status",
        #                              "chapterID": message["chapterID"],
        #                              "status": "normal",
        #                              "username": request.user.username})


        sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),
                                    {"command": "section_rename",
                                     "chapterID": message["chapterID"],
                                     "chapter": message["chapter"]}, myself=True)

        transaction.commit()

    return {"status": True}


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

    lst = [chap['item_id'] for chap in message["chapters"]]
    lstHold = []

#    lst = [chap[5:] for chap in message["chapters"]]
#    lstHold = [chap[5:] for chap in message["hold"]]


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

    sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),
                                {"command": "chapters_changed",
                                 "ids": lst,
                                 "hold_ids": lstHold,
                                 "kind": message["kind"],
                                 "chapter_id": message["chapter_id"]})

    # TODO
    # this should be changed, to check for errors

    transaction.commit()

    return {}


def remote_chapter_hold(request, message, bookid, version):

    book = models.Book.objects.get(id=bookid)
    book_version = book.getVersion(version)

    chapterID = message["chapterID"]

    m =  models.BookToc.objects.get(chapter__id__exact=chapterID)
    m.delete()

    sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),
                                {"command": "chapter_hold",
                                 "chapterID": chapterID}, myself=True)
    transaction.commit()

    return {}


def remote_chapter_unhold(request, message, bookid, version):

    book = models.Book.objects.get(id=bookid)
    book_version = book.getVersion(version)

    chapterID = message["chapterID"]

    chptr = models.Chapter.objects.get(id__exact=chapterID)

    m = models.BookToc(book = book,
                       version = book_version,
                       name = chptr.title,
                       chapter = chptr,
                       weight = -1,
                       typeof=1)
    m.save()

    sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),
                                {"command": "chapter_unhold",
                                 "chapterID": chapterID}, myself=True)
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

    try:
        book = models.Book.objects.get(id=bookid)
    except models.Book.DoesNotExist:
        return {"status": False}

    # check if you can access book on this channel
    bookSecurity = security.getUserSecurityForBook(request.user, book)
    hasPermission = security.canEditBook(book, bookSecurity)
    
    if not hasPermission:
        return {"status": False}

    # check if you can access book this chapter belongs to
    chapter = models.Chapter.objects.get(id=int(message["chapterID"]))

    bookSecurity = security.getUserSecurityForBook(request.user, chapter.version.book)
    hasPermission = security.canEditBook(chapter.version.book, bookSecurity)
    
    if not hasPermission:
        return {"status": False}

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

    book = models.Book.objects.get(id=bookid)
    book_version = book.getVersion(version)

    url_title = bookiSlugify(message["chapter"])

    if len(url_title) == 0:
        return {"created": False, "silly_url": True}

    # for now, just limit it to max 100 characters
    url_title = url_title[:100]

    # here i should probably set it to default project status
    s = models.BookStatus.objects.filter(book=book).order_by("-weight")[0]

    ch = models.Chapter.objects.filter(book=book, version=book_version, url_title=url_title)

    if len(list(ch)) > 0:
        return {"created": False, "chapter_exists": True}

    content = u'<h1>%s</h1><p><br/></p>' % message["chapter"]

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

    sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),  {"command": "chapter_create", "chapter": result}, myself = True)


    return {"status": True, "created": True, "chapter_id": chapter.id}

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
    import datetime

    att = models.Attachment(book = target_book,
                            version = target_book.version,
                            status = target_book.status,
                            created = datetime.datetime.now())

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
        return {"created": False, "section_exists": True}

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

        sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" %  (bookid, version),
                                    {"command": "chapter_create",
                                     "chapter": result,
                                     "typeof": c.typeof},
                                    myself = True)

    return {"status": True, "created": result, "chapter_id": 's{}'.format(c.id)}


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
            15: 'clone',
            16: 'cover_upload',
            17: 'cover_delete',
            18: 'cover_update',
            19: 'chapter_delete'}


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
        elif entry.kind in [13, 14, 16, 17, 18]:
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
        elif entry.kind in [19]:
            history.append({"args": parseJSON(entry.args),
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
    book_version = book.getVersion(version)

    bookSecurity = security.getUserSecurityForBook(request.user, book)

    if not bookSecurity.isAdmin():
        transaction.rollback()
        return {"result": False}

    try:
        cover =  models.BookCover.objects.get(book = book, cid = message.get('cid', ''))
        cover.approved = message.get('cover_status', False)
        cover.save()

        from booki.utils import log

        log.logBookHistory(book = book,
                           version = book_version,
                           args = {'filename': cover.filename, 'title': cover.title, 'cid': cover.pk},
                           user = request.user,
                           kind = 'cover_update'
                           )
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
    book_version = book.getVersion(version)

    try:
        cover =  models.BookCover.objects.get(book = book, cid = message.get('cid', ''))

        filename = cover.attachment.name[:]

        cover.delete()

        from booki.utils import log

        log.logBookHistory(book = book,
                           version = book_version,
                           args = {'filename': cover.filename, 'title': cover.title, 'cid': cover.pk},
                           user = request.user,
                           kind = 'cover_delete'
                           )
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
    book_version = book.getVersion(version)

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

        license_id = message.get('license', '')

        if license_id != '':
            license = models.License.objects.get(abbrevation=license_id)
            cover.license = license

        cover.notes = message.get('notes', '')[:500]

        frm = message.get('format', '').split(',')
        cover.is_book = "book" in frm
        cover.is_ebook = "ebook" in frm
        cover.is_pdf = "pdf" in frm

        cover.creator = message.get('creator', '')[:40]
        cover.cover_type = message.get('cover_type', '')

        cover.save()

        from booki.utils import log

        log.logBookHistory(book = book,
                           version = book_version,
                           args = {'filename': cover.filename, 'title': cover.title, 'cid': cover.pk},
                           user = request.user,
                           kind = 'cover_update'
                           )

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

    try:
        from PIL import Image
    except ImportError:
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


######################################################################################################

def remote_publish_book(request, message, bookid, version):
    from . import tasks

    tasks.publish_book(bookid=bookid, version=version, clientid=request.clientID, sputnikid=request.sputnikID)

    return {'result': True}

def remote_word_count(request, message, bookid, version):
    from django.utils.html import strip_tags
    from booktype.utils.wordcount import wordcount,charcount,charspacecount

    book = models.Book.objects.get(id=bookid)
    book_version = book.getVersion(version)

    ## get chapters
    chapters = models.BookToc.objects.filter(book=book, version=book_version)
    current_chapter = message["current_chapter_id"]

    #get chapter data    
    res = {}
    all_wcount = 0
    all_charcount = 0
    all_charspacecount = 0

    for chap in chapters:
        if chap.isChapter() and chap.chapter.id!=current_chapter:
            stripped_data = strip_tags(chap.chapter.content)
            all_wcount += wordcount(stripped_data)
            all_charcount += charcount(stripped_data)
            all_charspacecount += charspacecount(stripped_data)
            
    res = {"status": True, "wcount": all_wcount, "charcount": all_charcount, "charspacecount" : all_charspacecount }


    return res


