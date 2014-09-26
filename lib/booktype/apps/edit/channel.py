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

import os
import sputnik
from lxml import etree, html

from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from booki.utils.log import logBookHistory, logChapterHistory

from booki.editor import models
from booki.utils import security
from booktype.utils.misc import booktype_slugify


# this couple of functions should go to models.BookVersion
def get_toc_for_book(version):
    """
    Function returns list of TOC elements. Elements of list are tuples.
     - If chapter - (chapter_id, chapter_title, chapter_url_title, type_of, chapter_status_ud)
     - If section - (s + section_id, section_name, section_name, type_of)

    @rtype: C{list}
    @return: Returns list of TOC elements
    """

    results = []
    for chap in version.get_toc():
        parent_id = chap.parent.id if chap.parent else "root"
        
        # is it a section or chapter?
        if chap.chapter:
            results.append((
                chap.chapter.id,
                chap.chapter.title,
                chap.chapter.url_title,
                chap.typeof,
                chap.chapter.status.id,
                parent_id,
                chap.id
            ))
        else:
            results.append((
                chap.id,
                chap.name,
                chap.name,
                chap.typeof,
                None, # fake status
                parent_id,
                chap.id
            ))
    return results


def get_hold_chapters(book_version):
    """
    Function returns list of hold chapters. Elements of list are tuples with structure - (chapter_id, chapter_title, chapter_url_title, 1, chapter_status_id).

    @type book_version: C{booki.editor.models.BookVersion}
    @param book_version: Book version object
    @rtype: C{list}
    @return: Returns list with hold chapters
    """

    return [(ch.id, ch.title, ch.url_title, 1, ch.status.id) for ch in book_version.get_hold_chapters()]


def get_attachments(book_version):
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
                    "preview":   att.thumbnail(),
                    "created":   str(att.created.strftime("%d.%m.%Y %H:%M:%S")),
                    "size":      att.attachment.size}
                   for att in book_version.get_attachments().order_by("attachment") if att.attachment]

    return attachments


def get_book(request, bookid, versionid):
    try:
        book = models.Book.objects.get(id=int(bookid))
    except models.Book.DoesNotExist:
        raise ObjectDoesNotExist
    except models.Book.MultipleObjectsReturned:
        raise ObjectDoesNotExist

    book_security = security.getUserSecurityForBook(request.user, book)
    hasPermission = security.canEditBook(book, book_security)

    if not hasPermission:
        raise PermissionDenied

    book_version = book.get_version(versionid)

    if not book_version:
        raise ObjectDoesNotExist

    return book, book_version, book_security


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

    book, book_version, book_security = get_book(request, bookid, version)

    ## get chapters
    chapters = get_toc_for_book(book_version)
    holdChapters = get_hold_chapters(book_version)

    ## get users
    def _get_username(a):
        if a == request.sputnikID:
            return "<b>%s</b>" % a
        return a

    try:
        users = [_get_username(m) for m in list(sputnik.smembers("sputnik:channel:%s:channel" % message["channel"]))]
    except:
        users = []

    ## get workflow statuses
    statuses = [(status.id, status.name) for status in models.BookStatus.objects.filter(book=book).order_by("-weight")]

    ## get attachments
    try:
        attachments = get_attachments(book_version)
    except:
        attachments = []

    ## get metadata
    metadata = [{'name': v.name, 'value': v.get_value()} for v in models.Info.objects.filter(book=book)]

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
                                     "first_name": request.user.first_name,
                                     "last_name": request.user.last_name,
                                     "email": request.user.email,
                                     "mood": moodMessage}
                                    )

    ## get online users and their mood messages

    from django.contrib.auth.models import User

    def _getUser(_user):
        try:
            _u = User.objects.get(username=_user)
            return {
                    'username':_user,
                    'email': _u.email,
                    'first_name': _u.first_name,
                    'last_name': _u.last_name,
                    'mood':_u.get_profile().mood
                   }
        except:
            return None

    onlineUsers = filter(bool, [x for x in [_getUser(x) for x in _onlineUsers] if x])

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
            "is_admin":  book_security.isAdmin(),
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

    book, book_version, book_security = get_book(request, bookid, version)

    try:
        attachments = get_attachments(book_version)
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

    book, book_version, book_security = get_book(request, bookid, version)

    if book_security.isAdmin():
        for att_id in message['attachments']:
            att = models.Attachment.objects.get(pk=att_id, version=book_version)

            from booki.utils import log
            import os.path

            log.logBookHistory(book = book,
                               version = book_version,
                               args = {'filename': os.path.split(att.attachment.name)[1]},
                               user = request.user,
                               kind = 'attachment_delete')

            att.delete()

    return {"result": True}

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

    book, book_version = get_book(request, bookid, version)

    chapter = models.Chapter.objects.get(id=int(message["chapterID"]), version=book_version)
    status  = models.BookStatus.objects.get(id=int(message["statusID"]))

    chapter.status = status

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

    return {'result': True}


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

    book, book_version, book_security = get_book(request, bookid, version)

    chapter = models.Chapter.objects.get(id=int(message["chapterID"]), version=book_version)

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

    chapter.save()

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info",
                                                                "from": request.user.username,
                                                                "message_id": "user_saved_chapter",
                                                                "message_args": [request.user.username, chapter.title]},
                                myself=True)

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

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.isAdmin():
        raise PermissionDenied

    # get toc item related with chapter to be deleted
    chap = models.Chapter.objects.get(id__exact=int(message["chapterID"]), version=book_version)
    chap.delete()

    # MUST DELETE FROM TOC ALSO

    sputnik.addMessageToChannel(
        request, "/chat/%s/" %  bookid, {
            "command": "message_info",
            "from": request.user.username,
            "message_id": "user_delete_chapter",
            "message_args": [request.user.username, chap.title]
        },
        myself=True
    )

    logBookHistory(
        book = book,
        version = book_version,
        args = {'chapter': chap.title},
        user = request.user,
        kind = 'chapter_delete'
    )

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_delete",
            "chapterID": message["chapterID"]
        },
        myself = True
    )

    return {"result": True}


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

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.isAdmin():
        raise PermissionDenied

    section_id = message["chapterID"]
    delete_children = message["deleteChildren"]
    sec = models.BookToc.objects.get(pk=section_id, version=book_version)

    if delete_children == u'on':
        if sec.has_children():
            for toc_item in sec.booktoc_set.all():
                if toc_item.is_chapter():
                    # log chapter delete in book history
                    logBookHistory(
                        book = book,
                        version = book_version,
                        args = {'chapter': toc_item.chapter.title},
                        user = request.user,
                        kind = 'chapter_delete'
                    )
                    toc_item.chapter.delete()
                else:
                    # log section delete in book history
                    logBookHistory(
                        book = book,
                        version = book_version,
                        args = {'section': toc_item.name},
                        user = request.user,
                        kind = 'section_delete'
                    )
                    toc_item.delete()
    else:
        # in case user doesn't want to remove chapters, change the parent 
        for toc_item in sec.booktoc_set.all():
            toc_item.parent = None
            toc_item.save()

    # log main section delete in book history
    logBookHistory(
        book = book,
        version = book_version,
        args = {'section': sec.name},
        user = request.user,
        kind = 'section_delete'
    )
    sec.delete()

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "section_delete",
            "chapterID": message["chapterID"],
            "deleteChildren": message["deleteChildren"]
        },
        myself = True
    )

    return {"result": True}


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

    book, book_version, book_security = get_book(request, bookid, version)

    # get toc item related to chapter
    toc_item = models.BookToc.objects.get(id__exact=int(message["tocID"]), version=book_version)

    # check security
    chapter = toc_item.chapter

    old_title = chapter.title
    chapter.title = message["chapter"]
    chapter.save()

    logBookHistory(
        book = chapter.book,
        version = book_version,
        chapter = chapter,
        user = request.user,
        args = {"old": old_title, "new": message["chapter"]},
        kind = "chapter_rename"
    )

    sputnik.addMessageToChannel(
        request, "/chat/%s/" %  bookid, {
            "command": "message_info",
            "from": request.user.username,
            "message_id": "user_renamed_chapter",
            "message_args": [request.user.username, old_title, message["chapter"]]
        },
        myself=True
    )

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_rename",
            "tocID": message["tocID"],
            "chapter": message["chapter"]
        }, 
        myself=True
    )

    return dict(result=True)


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

    book, book_version, book_security = get_book(request, bookid, version)

    # check security
    sectionID = message["chapterID"]

    toc_item = models.BookToc.objects.get(id__exact=int(sectionID), version=book_version)
    old_title = toc_item.name
    toc_item.name = message["chapter"]
    toc_item.save()

    logBookHistory(
        book = book,
        version = book_version,
        chapter = None,
        user = request.user,
        args = {"old": old_title, "new": message["chapter"]},
        kind = "section_rename"
    )

    sputnik.addMessageToChannel(
        request, "/chat/%s/" %  bookid, {
            "command": "message_info",
            "from": request.user.username,
            "message_id": "user_renamed_section",
            "message_args": [request.user.username, old_title, message["chapter"]]
        },
        myself=True
    )

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "section_rename",
            "chapterID": message["chapterID"],
            "chapter": message["chapter"]
        }, 
        myself=True
    )

    return dict(result=True)


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

    lst = [(chap['item_id'], chap['parent_id']) for chap in message["chapters"]]
    lstHold = []

    book, book_version, book_security = get_book(request, bookid, version)

    weight = len(lst)

    logBookHistory(
       book = book,
       version = book_version,
       user = request.user,
       kind = "chapter_reorder"
    )

    for chap in lst:
        try:
            toc_item =  models.BookToc.objects.get(id__exact=int(chap[0]), version=book_version)
            toc_item.weight = weight
            
            # check if toc item has parent
            parent = None
            if chap[1] != 'root':
                try:
                    parent = models.BookToc.objects.get(
                        id__exact=int(chap[1]), 
                        version=book_version
                    )
                except Exception, e:
                    pass

            toc_item.parent = parent
            toc_item.save()
        except Exception, e:
            print e

        weight -= 1

    if message["kind"] == "remove":
        if type(message["chapter_id"]) == type(u' ') and message["chapter_id"][0] == 's':
            m =  models.BookToc.objects.get(id__exact=message["chapter_id"][1:], version=book_version)
            m.delete()
        else:
            m =  models.BookToc.objects.get(chapter__id__exact=int(message["chapter_id"]), version=book_version)
            m.delete()

#        addMessageToChannel(request, "/chat/%s/%s/" % (projectid, bookid), {"command": "message_info", "from": request.user.username, "message": 'User %s has rearranged chapters.' % request.user.username})

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapters_changed",
            "ids": lst,
            "hold_ids": lstHold,
            "kind": message["kind"],
            "chapter_id": message["chapter_id"]
        }
    )

    # TODO
    # this should be changed, to check for errors

    return {"result": True}


def remote_chapter_hold(request, message, bookid, version):

    book, book_version, book_security = get_book(request, bookid, version)
    chapterID = message["chapterID"]

    toc_item = models.BookToc.objects.get(chapter__id__exact=chapterID, version=book_version)
    toc_id = toc_item.id
    toc_item.delete()

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_hold",
            "chapterID": message["chapterID"],
            "tocID": toc_id
        }, 
        myself=True
    )

    return dict(result=True)


def remote_chapter_unhold(request, message, bookid, version):
    
    book, book_version, book_security = get_book(request, bookid, version)
    chapterID = message["chapterID"]

    chptr = models.Chapter.objects.get(id__exact=chapterID, version=book_version)
    toc_item = models.BookToc(
        book = book,
        version = book_version,
        name = chptr.title,
        chapter = chptr,
        weight = -1,
        typeof = 1
    )
    toc_item.save()

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_unhold",
            "chapterID": message["chapterID"],
            'tocID': toc_item.id
        }, 
        myself=True
    )

    return {"result": True}


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

    res = {"result": True}

    book, book_version, book_security = get_book(request, bookid, version)

    # check if you can access book this chapter belongs to
    chapter = models.Chapter.objects.get(id=int(message["chapterID"]), version=book_version)

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

    book, book_version, book_security = get_book(request, bookid, version)
    url_title = booktype_slugify(message["chapter"])

    if len(url_title) == 0:
        return {"result": False, "created": False, "silly_url": True}

    # for now, just limit it to max 100 characters
    url_title = url_title[:100]

    # here i should probably set it to default project status
    s = models.BookStatus.objects.filter(book=book).order_by("-weight")[0]
    ch = models.Chapter.objects.filter(book=book, version=book_version, url_title=url_title)

    if len(list(ch)) > 0:
        return {"created": False, "chapter_exists": True}

    content = u'<h1>%s</h1><p><br/></p>' % message["chapter"]

    chapter = models.Chapter(
        book = book,
        version = book_version,
        url_title = url_title,
        title = message["chapter"],
        status = s,
        content = content,
        created = datetime.datetime.now(),
        modified = datetime.datetime.now()
    )
    chapter.save()

    weight = len(book_version.get_toc()) + 1
    for itm in models.BookToc.objects.filter(version = book_version, book = book).order_by("-weight"):
        itm.weight = weight
        itm.save()

        weight -= 1
        
    toc_item = models.BookToc(
        version = book_version,
        book = book,
        name = message["chapter"],
        chapter = chapter,
        weight = 1,
        typeof = 1
    )
    toc_item.save()

    history = logChapterHistory(
        chapter = chapter,
        content = content,
        user = request.user,
        comment = message.get("comment", ""),
        revision = chapter.revision
    )

    if history:
        logBookHistory(
            book = book,
            version = book_version,
            chapter = chapter,
            chapter_history = history,
            user = request.user,
            kind = 'chapter_create'
        )

    result = (
        chapter.id, 
        chapter.title, 
        chapter.url_title, 
        1, # typeof (chapter)
        s.id, # status
        'root', # parent id (first level)
        toc_item.id # tocID
    )

    sputnik.addMessageToChannel(
        request, "/chat/%s/" % bookid, {
            "command": "message_info",
            "from": request.user.username,
            "message_id": "user_new_chapter",
            "message_args": [request.user.username, message["chapter"]]
        },
        myself=True
    )

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_create", 
            "chapter": result
        }, 
        myself = True
    )

    return {"result": True, "created": True, "chapter_id": chapter.id}


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

    book, book_version, book_security = get_book(request, bookid, version)

    try:
        source_book = models.Book.objects.get(url_title=message["book"])
    except models.Book.DoesNotExist:
        return {"result": False, "created": False}
    except models.Book.MultipleObjectsReturned:
        return {"result": False, "created": False}

    source_book_version = source_book.version
    source_url_title = message["chapter"]

    try:
        source_chapter = models.Chapter.objects.get(book=source_book, version=source_book_version, url_title=source_url_title)
    except models.Chapter.DoesNotExist:
        return {"result": False, "created": False}
    except models.Chapter.MultipleObjectsReturned:
        return {"result": False, "created": False}

    title = message.get("renameTitle", "")
    if title.strip():
        url_title = booktype_slugify(title)
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

    chapter.save()
    # this should be solved in better way
    # should have createChapter in booki.utils.book module

    toc_items = len(book_version.get_toc())+1

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

    tc.save()

    history = logChapterHistory(chapter = chapter,
                                content = chapter.content,
                                user = request.user,
                                comment = message.get("comment", ""),
                                revision = chapter.revision)
    logBookHistory(book = book,
                   version = book_version,
                   chapter = chapter,
                   chapter_history = history,
                   user = request.user,
                   kind = 'chapter_clone')

    attachments = source_book_version.get_attachments()
    attachmentnames = dict([(att.get_name(), att) for att in attachments])

    target_attachments = book_version.get_attachments()
    target_attachmentnames = dict([(att.get_name(), att)
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
                    name2copy[name] = new_att.get_name()
                if att and name in name2copy:
                    e.set('src', "static/"+name2copy[name])

    chapter.content = etree.tostring(tree, encoding='UTF-8', method='html')
    chapter.save()

    result = (chapter.id, chapter.title, chapter.url_title, 1, s.id)

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info",
                                                                "from": request.user.username,
                                                                "message_id": "user_cloned_chapter",
                                                                "message_args": [request.user.username, chapter.title, source_book.title]},
                                myself=True)

    sputnik.addMessageToChannel(request, "/booki/book/%s/%s/" % (bookid, version),  {"command": "chapter_create", "chapter": result}, myself = True)

    return {"result": True, "created": True}


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

    book, book_version, book_security = get_book(request, bookid, version)
    ch = models.BookToc.objects.filter(
       book=book,
       version=book_version,
       name=message['chapter'],
       typeof=0
    )

    if len(list(ch)) > 0:
        return {"created": False, "section_exists": True}

    c = models.BookToc(
        book = book,
        version = book_version,
        name = message["chapter"],
        chapter = None,
        weight = 0,
        typeof = 0
    )

    result = True
    c.save()

    logBookHistory(
       book = book,
       version = book_version,
       user = request.user,
       args = {"title": message["chapter"]},
       kind = 'section_create'
    )

    result = (
        c.id,
        c.name,
        c.name,
        c.typeof,
        None, # fake status
        "root",
        c.id
    )

    sputnik.addMessageToChannel(
        request, "/chat/%s/" % bookid, {
            "command": "message_info",
            "from": request.user.username,
            "message_id": "user_new_section",
            "message_args": [request.user.username, message["chapter"]]
        },
        myself=True
    )

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" %  (bookid, version), {
            "command": "chapter_create",
            "chapter": result,
            "typeof": c.typeof
        },
        myself = True
    )

    return {"result": True, "created": True, "chapter_id": 's{}'.format(c.id)}


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

    try:
        from PIL import Image
    except ImportError:
        import Image

    def _getDimension(cover):
        try:
            im = Image.open(cover.attachment.name)
            return im.size
        except:
            pass

        return None

    book, book_version, book_security = get_book(request, bookid, version)

    covers = []

    for cover in models.BookCover.objects.filter(book=book).order_by("title"):
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

        covers.append({
            'cid': cover.cid,
            'placement': cover.cover_type,
            'format': frm,
            'title': title,
            'notes': cover.notes,
            'filename': os.path.split(cover.attachment.name)[1],
            'preview': '../_cover/{0}/cover{1}'.format(cover.cid, os.path.split(cover.attachment.name)[1]),
            'size': cover.attachment.size,
            'dimension': _getDimension(cover),
            'approved': cover.approved})

    covers.reverse()

    return {"covers": covers, "can_update": book_security.isAdmin()}


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

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.isAdmin():
        raise PermissionDenied

    cover = models.BookCover.objects.get(book=book, cid=message.get('cid', ''))
    cover.approved = message.get('cover_status', False)
    cover.save()

    from booki.utils import log

    log.logBookHistory(book = book,
                       version = book_version,
                       args = {'filename': cover.filename, 'title': cover.title, 'cid': cover.pk},
                       user = request.user,
                       kind = 'cover_update'
                       )

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

    book, book_version, book_security = get_book(request, bookid, version)
    cover = models.BookCover.objects.get(book=book, cid=message.get('cid', ''))
    logBookHistory(
        book=book,
        version=book_version,
        args={'filename': cover.filename, 'title': cover.title, 'cid': cover.pk},
        user=request.user,
        kind='cover_delete'
    )
    cover.delete()

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

    book, book_version, book_security = get_book(request, bookid, version)

    cover = models.BookCover.objects.get(book=book, cid=message.get('cid', ''))
    cover.title = message.get('title', '').strip()[:250]

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

    logBookHistory(
        book=book,
        version=book_version,
        args={'filename': cover.filename, 'title': cover.title, 'cid': cover.pk},
        user=request.user,
        kind='cover_update'
    )

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

    licenses = [(elem.abbrevation, elem.name) for elem in models.License.objects.all().order_by("name")]

    return {"result": True, "licenses": licenses}


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

    book, book_version, book_security = get_book(request, bookid, version)

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

    licenses = [(elem.abbrevation, elem.name) for elem in models.License.objects.all().order_by("name")]

    transaction.commit()

    return {"result": True, "cover": cover, "licenses": licenses}


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

    book, book_version, book_security = get_book(request, bookid, version)

    licenses = [(lic.abbrevation, lic.name)  for lic in models.License.objects.all().order_by("name") if lic]
    languages = [(lic.abbrevation, lic.name) for lic in models.Language.objects.all().order_by("name") if lic] + [('unknown', 'Unknown')]

    current_license = getattr(book.license, "abbrevation","")
    current_language = getattr(book.language, "abbrevation", "unknown")

    # get rtl
    try:
        rtl = models.Info.objects.get(book=book, name='{http://booki.cc/}dir', kind=0).get_value()
    except (models.Info.DoesNotExist, models.Info.MultipleObjectsReturned):
        rtl = "LTR"

    return {"result": True,
            "licenses": licenses,
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

    book, book_version, book_security = get_book(request, bookid, version)

    lic = models.License.objects.filter(abbrevation=message["license"])[0]
    book.license = lic
    book.save()


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

    book, book_version, book_security = get_book(request, bookid, version)

    from django.contrib.auth.models import User

    # not so cool idea
    excl = [a.user.username for a in models.AttributionExclude.objects.filter(book = book)]
    users = [(u['user__username'], u['user__first_name']) for u in models.ChapterHistory.objects.filter(chapter__version__book=book).values("user", "user__username", "user__first_name").distinct()  if u['user__username'] not in excl]
    users_exclude = [(u.user.username, u.user.first_name) for u in models.AttributionExclude.objects.filter(book = book).order_by("user__username")]


    return {"result": True,
            "users": users,
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

    book, book_version, book_security = get_book(request, bookid, version)

    from django.contrib.auth.models import User

    # delete all elements
    models.AttributionExclude.objects.filter(book=book).delete()

    for userName in message["excluded_users"]:
        u = User.objects.get(username = userName)
        a = models.AttributionExclude(book = book, user = u)
        a.save()

    transaction.commit()

    return {"result": True}


def remote_publish_book(request, message, bookid, version):
    from . import tasks

    tasks.publish_book(bookid=bookid, version=version, clientid=request.clientID, sputnikid=request.sputnikID)

    return {'result': True}


def remote_word_count(request, message, bookid, version):
    from django.utils.html import strip_tags
    from booktype.utils.wordcount import wordcount,charcount,charspacecount

    book = models.Book.objects.get(id=bookid)
    book_version = book.get_version(version)

    ## get chapters
    chapters = models.BookToc.objects.filter(book=book, version=book_version)
    current_chapter = message["current_chapter_id"]

    #get chapter data
    res = {}
    all_wcount = 0
    all_charcount = 0
    all_charspacecount = 0

    for chap in chapters:
        if chap.is_chapter() and chap.chapter.id!=current_chapter:
            stripped_data = strip_tags(chap.chapter.content)
            all_wcount += wordcount(stripped_data)
            all_charcount += charcount(stripped_data)
            all_charspacecount += charspacecount(stripped_data)

    res = {"result": True, "status": True, "wcount": all_wcount, "charcount": all_charcount, "charspacecount" : all_charspacecount }

    return res

######################################################################################################

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

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.isAdmin():
        raise PermissionDenied

    book.permission = message["permission"]
    book.save()

    return {"result": True}


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

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.isAdmin():
        raise PermissionDenied

    weight = 100

    for status_id in [x[11:] for x in message["order"]]:
        up = models.BookStatus.objects.get(book = book, id = status_id)
        up.weight = weight
        up.save()

        weight -= 1


    allStatuses = [(status.id, status.name) for status in models.BookStatus.objects.filter(book=book).order_by("-weight")]

    sputnik.addMessageToChannel(request,
                                "/booki/book/%s/%s/" % (bookid, version),
                                {"command": "chapter_status_changed",
                                 "statuses": allStatuses},
                                myself = False
                                )

    return {"result": True,
            "statuses": allStatuses }


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

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.isAdmin():
        raise PermissionDenied

    result = True

    up = models.BookStatus.objects.get(book = book, id = message["status_id"])
    # this is a quick fix
    # check - no chapter has this status + no attachment has this status and no book has this status
    if len(list(models.Chapter.objects.filter(status = up, book = book))) == 0 and \
            len(list(models.Attachment.objects.filter(status = up, version__book = book))) == 0 and \
            book.status != up:
        up.delete()
    else:
        result = False

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

    book, book_version, book_security = get_book(request, bookid, version)

    status_id = None

    if not book_security.isAdmin():
        raise PermissionDenied

    from django.utils.html import strip_tags

    bs = models.BookStatus(book = book,
                           name = strip_tags(message["status_name"].strip()),
                           weight = 0)
    bs.save()

    status_id = bs.id

    allStatuses = [(status.id, status.name) for status in models.BookStatus.objects.filter(book=book).order_by("-weight")]

    sputnik.addMessageToChannel(request,
                                "/booki/book/%s/%s/" % (bookid, version),
                                {"command": "chapter_status_changed",
                                 "statuses": allStatuses},
                                myself = False
                                )

    return {"result": True,
            "status_id": status_id,
            "statuses": allStatuses
            }


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

    book, book_version, book_security = get_book(request, bookid, version)

    try:
        for up in models.BookiPermission.objects.filter(book = book,
                                                     user__username = message["username"],
                                                     permission = message["role"]):
            up.delete()
    except models.BookiPermission.DoesNotExist:
        pass

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

    book, book_version, book_security = get_book(request, bookid, version)

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

    return {"result": result}


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

    book, book_version, book_security = get_book(request, bookid, version)

    users = [(u.user.username, '%s (%s)' % (u.user.username, u.user.first_name)) for u in models.BookiPermission.objects.filter(book = book, permission = message["role"]).order_by("user__username")]

    if int(message["role"]) == 1:
        users.append((book.owner.username, '%s (%s) [owner]' % (book.owner.username, book.owner.first_name)))

    return {"result": True, "users": users}


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

    book, book_version, book_security = get_book(request, bookid, version)

    from django.contrib.auth.models import User

#    users = ['%s' % (u.username, ) for u in User.objects.filter(Q(username__contains=message["possible_user"]) | Q(first_name__contains=message["possible_user"]))[:20]]
    users = ['%s (%s)' % (u.username, u.first_name) for u in User.objects.filter(Q(username__contains=message["possible_user"]) | Q(first_name__contains=message["possible_user"]))[:20]]


    return {"result": True, "possible_users": users}


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

    book, book_version, book_security = get_book(request, bookid, version)

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

    return {"result": True}


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

    from django.contrib.auth.models import User
    res = {"result": True}
    def vidi(a):
        return sputnik.rdecode(a)

    usernames = [m for m in list(sputnik.smembers("sputnik:channel:%s:users" % message["channel"]))]
    values = User.objects.filter(username__in=usernames).values('username', 'email', 'first_name', 'last_name')
    res["users"] = list(values)

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

    res = {"result": True}

    import time

    # rcon.delete(key)
    # set the initial timer for editor

    if request.user.username and request.user.username != '':
        sputnik.set("booki:%s:locks:%s:%s" % (bookid, message["chapterID"], request.user.username), time.time())

        if '%s' % sputnik.get("booki:%s:killlocks:%s:%s" % (bookid, message["chapterID"], request.user.username)) == '1':
            sputnik.rdelete("booki:%s:killlocks:%s:%s" % (bookid, message["chapterID"], request.user.username))
            res = {"kill": "please"}

    return res


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

    book, book_version, book_security = get_book(request, bookid, version)

    page = int(message.get("page", 1))

    book_history = models.BookHistory.objects.filter(book=book).order_by("-modified")[(page-1)*50:(page-1)*50+50]

    temp = {
        0: 'unknown',
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
        19: 'chapter_delete'
    }


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

    book, book_version, book_security = get_book(request, bookid, version)

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


    book, book_version, book_security = get_book(request, bookid, version)

    chapter = models.Chapter.objects.get(version=book_version, url_title=message["chapter"])

    revision = models.ChapterHistory.objects.get(revision=message["revision"], chapter__url_title=message["chapter"], chapter__version=book_version.id)

    # TODO
    # does chapter history really needs to keep content or it can only keep reference to chapter

    history = logChapterHistory(chapter = chapter,
                      content = revision.content,
                      user = request.user,
                      comment = "Reverted to revision %s." % message["revision"],
                      revision = chapter.revision+1)

    if history:
        logBookHistory(book = book,
                       version = book_version,
                       chapter = chapter,
                       chapter_history = history,
                       user = request.user,
                       args = {},
                       kind = 'chapter_save')

    chapter.revision += 1
    chapter.content = revision.content;

    chapter.save()

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid,
                                {"command": "message_info",
                                 "from": request.user.username,
                                 "message_id": "user_reverted_chapter",
                                 "message_args": [request.user.username, chapter.title, message["revision"]]},
                                myself=True)

    return {"result": True}


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

    book, book_version, book_security = get_book(request, bookid, version)

    revision = models.ChapterHistory.objects.get(chapter__book=book, chapter__url_title=message["chapter"], revision=message["revision"])

    return {"result": True,
            "chapter": revision.chapter.title,
            "chapter_url": revision.chapter.url_title,
            "modified": revision.modified.strftime("%d.%m.%Y %H:%M:%S"),
            "user": revision.user.username,
            "revision": revision.revision,
            "version": '%d.%d' % (revision.chapter.version.major, revision.chapter.version.minor),
            "content": revision.content,
            "comment": revision.comment}


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

    book, book_version, book_security = get_book(request, bookid, version)

    book_notes = models.BookNotes.objects.filter(book=book)

    notes = []
    for entry in book_notes:
        notes.append({"notes": entry.notes})

    return {"result": True, "notes": notes}


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

    book, book_version, book_security = get_book(request, bookid, version)

    book_notes = models.BookNotes.objects.filter(book=book)
    notes = message.get("notes")
    book_notes_obj = None

    if len(book_notes) == 0:
        book_notes_obj = models.BookNotes( book = book , notes = notes)
    else:
        book_notes_obj = book_notes[0]
    book_notes_obj.notes = notes


    book_notes_obj.save()

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_info",
                                                                "from": request.user.username,
                                                                "message_id": "user_saved_notes",
                                                                "message_args": [request.user.username, book.title]},
                                myself=True)

    return {"result": True}


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

    book, book_version, book_security = get_book(request, bookid, version)

    if book_security.isAdmin():
        for key in sputnik.rkeys("booki:%s:locks:%s:*" % (bookid, message["chapterID"])):
            m = re.match("booki:(\d+):locks:(\d+):(\w+)", key)
            if m:
                sputnik.set("booki:%s:killlocks:%s:%s" % (bookid, message["chapterID"], m.group(3)), 1)

    return {"result": True}


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

    book, book_version, book_security = get_book(request, bookid, version)

    book_versions = [{"major": v.major,
                      "minor": v.minor,
                      "name": v.name,
                      "description": v.description,
                      "created": str(v.created.strftime('%a, %d %b %Y %H:%M:%S GMT'))}
                     for v in models.BookVersion.objects.filter(book=book).order_by("-created")]

    return {"result": True, "versions": book_versions}


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

    for toc in book_ver.get_toc():
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

    for chap in book_ver.get_hold_chapters():
        c = models.Chapter(version=new_version,
                           book=book, # this should be removed
                           url_title=chap.url_title,
                           title=chap.title,
                           status=chap.status,
                           revision=chap.revision,
                           created=datetime.datetime.now(),
                           content=chap.content)
        c.save()

    for att in book_ver.get_attachments():
        a = models.Attachment(version = new_version,
                              book=book,
                              status=att.status,
                              created=datetime.datetime.now())
        a.attachment.save(att.get_name(), att.attachment, save = False)
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

    book, book_version, book_security = get_book(request, bookid, version)

    new_version = create_new_version(book, book_version, message, book_version.major+1, 0)

    logBookHistory(book = book,
                   version = new_version,
                   chapter = None,
                   chapter_history = None,
                   user = request.user,
                   args = {"version": new_version.get_version()},
                   kind = 'major_version')

    return {"result": True, "version": new_version.get_version()}


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

    book, book_version, book_security = get_book(request, bookid, version)

    new_version = create_new_version(book, book_version, message, book_version.major, book_version.minor+1)

    logBookHistory(book = book,
                   version = new_version,
                   chapter = None,
                  chapter_history = None,
                   user = request.user,
                   args = {"version": new_version.get_version()},
                   kind = 'minor_version')

    return {"result": True, "version": new_version.get_version()}


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

    book, book_version, book_security = get_book(request, bookid, version)

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

    return {"result": True, "output": '\n'.join(output)}


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

    book, book_version, book_security = get_book(request, bookid, version)

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

    return {"result": True, "output": info+'<table border="0" width="100%%"><tr><td width="50%%"><div style="border-bottom: 1px solid #c0c0c0; font-weight: bold;">Revision: '+message["revision1"]+'</div></td><td width="50%%"><div style="border-bottom: 1px solid #c0c0c0; font-weight: bold">Revision: '+message["revision2"]+'</div></td></tr>\n'.join(output)+'</table>\n'}

