# This file is part of Booktype.
# Copyright (c) 2012
# Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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
import re
import json
import time
import datetime
import logging

from lxml import html, etree
from django.db.models import Q
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.utils.timezone import datetime as django_datetime
from django.utils.translation import ugettext, ugettext_lazy as _lazy
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, SuspiciousOperation

import sputnik
from booki.editor import models
from booki.utils.log import logBookHistory, logChapterHistory
from booktype.utils import security, config
from booktype.utils.misc import booktype_slugify, get_available_themes, get_default_book_status
from booktype.apps.core.models import Role, BookRole
from booktype.apps.themes.models import BookTheme

from .utils import send_notification, clean_chapter_html
from .models import ChatMessage

try:
    from PIL import Image
except ImportError:
    import Image


logger = logging.getLogger('sputnik.edit.channel')


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

            state = "normal"
            current_editor = chap.chapter.get_current_editor_username()
            if current_editor:
                state = "edit"

            results.append((
                chap.chapter.id,
                chap.chapter.title,
                chap.chapter.url_title,
                chap.typeof,
                chap.chapter.status.id,
                chap.chapter.lock_type,
                chap.chapter.lock_username,
                parent_id,
                chap.id,
                state,
                current_editor
            ))
        else:
            results.append((
                chap.id,
                chap.name,
                chap.name,
                chap.typeof,
                None,       # fake status
                0,          # fake unlocked
                None,       # fake lock username
                parent_id,
                chap.id,
                "normal",   # fake state
                None        # fake current editor
            ))
    return results


def get_toc_dict_for_book(version):
    """
    Function returns list of TOC elements. Elements of list are dictionaries.

    @rtype: C{list}
    @return: Returns list of TOC elements
    """

    results = []
    for chap in version.get_toc():
        parent_id = chap.parent.id if chap.parent else "root"

        # is it a section or chapter?
        if chap.chapter:

            state = "normal"
            current_editor = chap.chapter.get_current_editor_username()
            if current_editor:
                state = "edit"

            chapter = chap.chapter
            checked_statuses = list(chapter.checked_statuses.values_list('pk', flat=True))

            results.append({
                'chapterID': chapter.id,
                'title': chapter.title,
                'urlTitle': chapter.url_title,
                'isSection': (chap.typeof != models.BookToc.CHAPTER_TYPE),
                'status': chapter.status.id,
                'checked_statuses': checked_statuses,
                'assigned': chapter.assigned,
                'lockType': chapter.lock_type,
                'lockUsername': chapter.lock_username,
                'parentID': parent_id,
                'tocID': chap.id,
                'state': state,
                'editBy': current_editor,
                'hasComments': chapter.has_comments,
                'hasMarker': chapter.has_marker
            })
        else:
            results.append({
                'chapterID': chap.id,
                'title': chap.name,
                'urlTitle': booktype_slugify(chap.name),
                'isSection': True,
                'status': None,        # fake status
                'lockType': 0,         # fake unlocked
                'lockUsername': None,  # fake lock username
                'parentID': parent_id,
                'tocID': chap.id,
                'state': 'normal',     # fake state
                'editBy': None,         # fake current editor,
                'hasComments': False,
                'hasMarker': False
            })
    return results


def get_hold_chapters(book_version):
    """
    Function returns list of hold chapters. Elements of list are tuples with
    structure - (chapter_id, chapter_title, chapter_url_title, 1,
                 chapter_status_id, chapter_lock_type).

    @type book_version: C{booki.editor.models.BookVersion}
    @param book_version: Book version object
    @rtype: C{list}
    @return: Returns list with hold chapters
    """
    hold_chapters = book_version.get_hold_chapters()

    def _to_tuple(chapter):
        """
        Simply convert chapter instance to tuple.

        Args:
          chapter: booki.editor.models.Chapter instance

        Returns:
          Tuple with chapter's attributes
        """

        state = "normal"
        current_editor = chapter.get_current_editor_username()
        if current_editor:
            state = "edit"

        return (chapter.id,
                chapter.title,
                chapter.url_title,
                1,
                chapter.status.id,
                chapter.lock_type,
                chapter.lock_username,
                "root",     # no parents in hold
                None,       # hold chapter not in toc
                state,
                current_editor)

    return [_to_tuple(ch) for ch in hold_chapters]


def get_attachments(book_version, size=(100, 100), aspect_ratio=False):
    """
    Function returns list of attachments for L{book_version}. Elements of
    list are dictionaries and are sorted by attachment name. Each dictionary has keys:
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

    def _get_dimension(att):
        try:
            im = Image.open(att.attachment.name)
            return im.size
        except:
            pass

        return None

    attachments = [{"id": att.id,
                    "dimension": _get_dimension(att),
                    "status": att.status.id,
                    "name": os.path.split(att.attachment.name)[1],
                    "preview": att.thumbnail(size=size, aspect_ratio=aspect_ratio),
                    "created": str(att.created.strftime("%d.%m.%Y %H:%M:%S")),
                    "size": att.attachment.size}
                   for att in book_version.get_attachments().order_by("attachment") if att.attachment]

    return attachments


def get_book(request, bookid, versionid):
    try:
        book = models.Book.objects.get(id=int(bookid))
    except models.Book.DoesNotExist:
        raise ObjectDoesNotExist
    except models.Book.MultipleObjectsReturned:
        raise ObjectDoesNotExist

    book_security = security.get_security_for_book(request.user, book)
    has_permission = book_security.can_edit()

    if not has_permission:
        raise PermissionDenied

    book_version = book.get_version(versionid)

    if not book_version:
        raise ObjectDoesNotExist

    return book, book_version, book_security


def get_book_statuses(book):
    """
    Function returns list of Book statuses.

    :Arguments:
        book: Book instance

    Returns list of book statuses elements
    """

    qs = models.BookStatus.objects.filter(book=book).order_by("-weight")
    return [(st.id, _lazy(st.name), st.color) for st in qs]


def get_book_statuses_dict(book):
    """
    Returns list of dict of book statuses elements

    :Arguments:
        book: Book instance
    """
    from django.db.models import Count
    BookStatus = models.BookStatus

    default_status_name = get_default_book_status()
    all_statuses = (BookStatus.objects
                    .filter(book=book)
                    .annotate(num_chapters=Count('chapter'))
                    .annotate(num_attachments=Count('attachment'))
                    .order_by('-weight'))

    status_list = []
    for status in all_statuses:
        status_list.append({
            'id': status.id,
            'name': _lazy(status.name),
            'color': status.color,
            'num_chapters': status.num_chapters,
            'num_attachments': status.num_attachments,
            'is_default_status': status.name == default_status_name
        })

    return status_list


def remote_init_editor(request, message, bookid, version):
    """
    Called when Booki editor is being initialized.

    "user_add" message is send to all users currently on this channel and notification is send
    to all online users on the chat.

    Returns:
     - licenses - list of tuples (abbrevation, name)
     - chapters - result of getTOCForBook function
     - metadata - list of dictionaries {'name': ..., 'value': ...}
     - hold - result of getHoldChapters function
     - users - list of active users
     - statuses - list of tuples (status_id, status_name)
     - attachments - result of getAttachments function
     - onlineUsers - list of online users
     - chatMessages - list of chat messages

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

    # get chapters
    chapters = get_toc_dict_for_book(book_version)
    hold_chapters = get_hold_chapters(book_version)

    # get users
    def _get_username(a):
        if a == request.sputnikID:
            return "<b>%s</b>" % a
        return a

    try:
        users = [_get_username(m) for m in list(sputnik.smembers("sputnik:channel:%s:channel" % message["channel"]))]
    except:
        users = []

    # get workflow statuses
    statuses = get_book_statuses(book)

    # get attachments
    try:
        attachments = get_attachments(book_version)
    except:
        attachments = []

    # get metadata
    metadata = [{'name': v.name, 'value': v.get_value()} for v in models.Info.objects.filter(book=book)]

    # notify others
    sputnik.addMessageToChannel(
        request, "/chat/%s/" % bookid, {
            "command": "user_joined",
            "email": request.user.email,
            "user_joined": request.user.username
        }, myself=False)

    # get licenses
    licenses = [(elem.abbrevation, elem.name) for elem in models.License.objects.all().order_by("name")]

    # get online users
    try:
        _online_users = sputnik.smembers("sputnik:channel:%s:users" % message["channel"])
    except:
        _online_users = []

    if request.user.username not in _online_users:
        send_notification(request, bookid, version, "notification_user_joined_the_editor", request.user.username)
        try:
            sputnik.sadd("sputnik:channel:%s:users" % message["channel"], request.user.username)
            _online_users.append(request.user.username)
        except:
            pass

        # set notifications to other clients
        try:
            profile = request.user.profile
        except AttributeError:
            profile = None

        moodMessage = ''
        if profile:
            moodMessage = profile.mood

        sputnik.addMessageToChannel(
            request, "/booktype/book/{}/{}/".format(bookid, version), {
                "command": "user_add",
                "username": request.user.username,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
                "mood": moodMessage
            })

    # get online users and their mood messages
    def _get_user(_user):
        try:
            _u = User.objects.get(username=_user)
            return {
                'username': _user,
                'email': _u.email,
                'first_name': _u.first_name,
                'last_name': _u.last_name,
                'mood': _u.profile.mood
            }
        except:
            return None

    online_users = filter(bool, [x for x in [_get_user(x) for x in _online_users] if x])

    available_themes = get_available_themes()
    theme_active = available_themes[0]

    try:
        theme = BookTheme.objects.get(book=book)
        # override default one if it's available
        if theme.active in available_themes:
            theme_active = theme.active
        else:
            theme.active = theme_active
            theme.save()

    except BookTheme.DoesNotExist:
        theme = BookTheme(book=book, active=theme_active)
        theme.save()

    chat_messages = []

    for msg in ChatMessage.objects.filter(thread__book=book):
        sender = msg.sender
        chat_messages.append({
            'datetime': str(msg.datetime.strftime("%d/%m/%Y, %I:%M:%S %p")),
            'text': msg.text,
            'sender_id': sender.id,
            'sender_username': sender.username,
            'email': sender.email,
        })

    # provide information about current user
    current_user = {
        'username': book_security.user.username,
        'first_name': book_security.user.first_name,
        'last_name': book_security.user.last_name,
        'email': book_security.user.email,
        'is_superuser': book_security.is_superuser(),
        'is_staff': book_security.is_staff(),
        'is_admin': book_security.is_admin(),
        'is_book_owner': book_security.is_book_owner(),
        'is_book_admin': book_security.is_book_admin(),
        'permissions': ['{0}.{1}'.format(perm.app_name, perm.name) for perm in book_security.permissions],
    }

    return {
            "licenses": licenses,
            "chapters": chapters,
            "metadata": metadata,
            "hold": hold_chapters,
            "users": users,
            "statuses": statuses,
            "attachments": attachments,
            "theme": theme_active,
            # Check for errors in the future
            "theme_custom": json.loads(theme.custom),
            "onlineUsers": list(online_users),
            "current_user": current_user,
            "chatMessages": chat_messages
        }


def remote_attachments_list(request, message, bookid, version):
    """
    Calls function L{getAttachments} and returns info about attachments
    for the specific version of the book.

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

    # define default options for thumbnails
    size = (100, 100)
    aspect_ratio = False

    # overwrite default options for thumbnails
    if 'options' in message:
        try:
            size = (message['options']['width'], message['options']['height'])
            aspect_ratio = message['options']['aspect_ratio']
        except KeyError:
            pass

    try:
        attachments = get_attachments(book_version, size, aspect_ratio)
    except:
        attachments = []

    return {"attachments": attachments}


def remote_attachment_rename(request, message, bookid, version):
    """
    Change specific attachment's filename.

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

    if not book_security.has_perm('edit.rename_attachment'):
        raise PermissionDenied

    for att_id in message['attachments']:
        att = models.Attachment.objects.get(pk=att_id, version=book_version)

        logBookHistory(
            book=book,
            version=book_version,
            args={'filename': os.path.split(att.attachment.name)[1]},
            user=request.user,
            kind='attachment_rename'
        )

        _filename = booktype_slugify(message['filename'].strip())

        if not _filename:
            return {"result": False}

        new_filename = '{}.{}'.format(_filename, att.attachment.path.rsplit('.', 1)[-1])
        new_filepath = os.path.join(
            att.attachment.path.rsplit('/', 1)[0],
            new_filename
        )
        old_filepath = att.attachment.path
        old_filename = old_filepath.rsplit('/', 1)[-1]

        if new_filepath == old_filepath:
            return {"result": True}

        if os.path.exists(new_filepath):
            return {"result": False, 'message': _lazy('File with this name already exists.')}

        # delete thumbnails
        att.delete_thumbnail()
        att.delete_thumbnail(size=(150, 150))

        # rename file
        os.rename(
            old_filepath,
            new_filepath
        )

        # save
        att.attachment.name = new_filepath
        att.save()

        # walk through all chapters and change filename
        for chapter in book_version.get_toc():
            should_update_content = False

            try:
                cont = chapter.chapter.content
            except AttributeError:
                continue

            utf8_parser = html.HTMLParser(encoding='utf-8')
            root = html.document_fromstring(cont, parser=utf8_parser)

            for element in root.iter('img'):
                src = element.get('src', None)

                if not src:
                    continue

                src_prefix, src_filename = src.rsplit('/', 1)

                if src_filename != old_filename:
                    continue

                element.set('src', '/'.join((src_prefix, new_filename)))
                should_update_content = True

            if should_update_content:
                cont = etree.tostring(root, method='html', encoding='utf-8')[12:-14]
                chapter.chapter.content = cont
                chapter.chapter.save()

        # update all clients html
        sputnik.addMessageToChannel(
            request, "/booktype/book/%s/%s/" % (bookid, version), {
                "command": "attachment_rename",
                "oldSrc": 'static/{}'.format(old_filename),
                "newSrc": 'static/{}'.format(new_filename)
            },
            myself=True
        )

        send_notification(request, bookid, version, "attachment_was_renamed")

    return {"result": True}


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

    if not book_security.has_perm('edit.remove_attachment'):
        raise PermissionDenied

    for att_id in message['attachments']:
        att = models.Attachment.objects.get(pk=att_id, version=book_version)

        logBookHistory(
            book=book,
            version=book_version,
            args={'filename': os.path.split(att.attachment.name)[1]},
            user=request.user,
            kind='attachment_delete'
        )
        att_name = att.get_name()
        att.delete()
        send_notification(request, bookid, version, "notification_attachment_was_deleted", att_name)

    return {"result": True}


def remote_chapter_state(request, message, bookid, version):
    """
    Sets new state for the specific chapter. Sends "chapter_state" with new state to all users on the channel.

    Input:
      - chapterID
      - state

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @type version: C{string}
    @param version: Book version
    """

    _, book_version, _ = get_book(request, bookid, version)

    try:
        chapter = models.Chapter.objects.get(id=int(message["chapterID"]), version=book_version)
    except models.Chapter.DoesNotExist:
        return dict(result=False)

    # request for edit unlock
    if message["state"] == "normal":
        # if chapter under edit by another user
        editor_username = chapter.get_current_editor_username()
        if editor_username and editor_username != request.user.username:
            raise PermissionDenied

        sputnik.rdelete("booktype:%s:%s:editlocks:%s:%s" % (bookid, version, message["chapterID"],
                                                            request.user.username))

    chapterItem = {
        "hasComments": chapter.has_comments,
        "hasMarker": chapter.has_marker,
        "statusID": chapter.status.id,
        "checked_statuses": list(chapter.checked_statuses.values_list('pk', flat=True))
    }

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_state",
            "chapterID": message["chapterID"],
            "state": message["state"],
            "username": request.user.username,
            "chapterItem": chapterItem
        }, myself=True)

    return {"result": True}


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

    book, book_version, book_security = get_book(request, bookid, version)

    try:
        chapter = models.Chapter.objects.get(id=int(message["chapterID"]), version=book_version)
        status = models.BookStatus.objects.get(id=int(message["statusID"]))
    except (models.Chapter.DoesNotExist, models.BookStatus.DoesNotExist):
        return dict(result=False)

    # check permissions
    if not book_security.has_perm('edit.change_chapter_status'):
        raise PermissionDenied

    # if chapter is locked -> check access
    if chapter.is_locked():
        # check access
        if not book_security.has_perm('edit.edit_locked_chapter'):
            raise PermissionDenied
        elif not book_security.is_admin() and (chapter.lock.type == models.ChapterLock.LOCK_EVERYONE
                                               and chapter.lock.user != request.user):
            raise PermissionDenied

    chapter.status = status
    chapter.save()

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "change_status",
            "chapterID": message["chapterID"],
            "statusID": int(message["statusID"]),
            "username": request.user.username
        })

    sputnik.addMessageToChannel(
        request, "/chat/%s/" % bookid, {
            "command": "message_info",
            "from": request.user.username,
            "email": request.user.email,
            "message_id": "user_changed_chapter_status",
            "message_args": [
                request.user.username,
                chapter.title,
                _lazy(status.name)
            ]
        },
        myself=True)

    send_notification(
        request, bookid, version,
        "notification_chapter_status_was_changed",
        chapter.title, _lazy(status.name))

    return {'result': True}


def remote_status_checked(request, message, bookid, version):
    """
    Saves checked or unchecked status into chapter checked_statuses relation
    field.

    FIXME: should we notify all the users in the channel?
    """
    book, book_version, book_security = get_book(request, bookid, version)
    checked_state = message.get('checkedState', False)  # true or false?

    # NOTE: should this be tight to permissions?

    try:
        chapter = models.Chapter.objects.get(id=int(message["chapterID"]), version=book_version)
        status = models.BookStatus.objects.get(id=int(message["statusID"]))
    except (models.Chapter.DoesNotExist, models.BookStatus.DoesNotExist):
        return dict(result=False)

    if checked_state:
        chapter.checked_statuses.add(status)
    else:
        chapter.checked_statuses.remove(status)

    # let's get the updated list of checked statuses
    checked_statuses = list(chapter.checked_statuses.values_list('pk', flat=True))

    return dict(result=True, checked_statuses=checked_statuses)


def remote_assign_chapter(request, message, bookid, version):
    """
    Assign user to a chapter. If userID is null it will remove the assigning

    FIXME:
        - should we notify all the users in the channel?
    """
    book, book_version, book_security = get_book(request, bookid, version)
    user_assign = message.get('username', '')

    # NOTE: should this be tight to permissions?

    try:
        chapter = models.Chapter.objects.get(id=int(message["chapterID"]), version=book_version)
    except models.Chapter.DoesNotExist:
        return dict(result=False)

    chapter.assigned = user_assign
    chapter.save()

    return dict(result=True, assigned=chapter.assigned)


def remote_chapter_save(request, message, bookid, version):
    """
    Saves new chapter content.

    Writes log to Chapter and Book history. Sends notification to chat. Removes lock.
    Sends "chapter_status" messahe to the channel. Fires the chapter_modified signal.

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
    # or maybe even better put it in the Model

    book, book_version, book_security = get_book(request, bookid, version)

    try:
        # check if you can access book this chapter belongs to
        chapter = models.Chapter.objects.get(id=int(message["chapterID"]), version=book_version)
    except models.Chapter.DoesNotExist:
        return dict(result=False)

    # if chapter under edit by another user -> decline
    editor_username = chapter.get_current_editor_username()
    if editor_username and editor_username != request.user.username:
        raise PermissionDenied

    # if chapter is locked -> check access
    if chapter.is_locked():
        if not book_security.has_perm('edit.edit_locked_chapter'):
            raise PermissionDenied
        elif not book_security.is_admin() and (chapter.lock.type == models.ChapterLock.LOCK_EVERYONE
                                               and chapter.lock.user != request.user):
            raise PermissionDenied

    content = message['content']

    if not message.get("minor", False):
        history = logChapterHistory(chapter=chapter,
                                    content=content,
                                    user=request.user,
                                    comment=message.get("comment", ""),
                                    revision=chapter.revision + 1)

        if history:
            logBookHistory(book=chapter.book,
                           version=book_version,
                           chapter=chapter,
                           chapter_history=history,
                           user=request.user,
                           args={"comment": message.get("comment", ""),
                                 "author": message.get("author", ""),
                                 "authorcomment": message.get("authorcomment", "")},
                           kind='chapter_save')

        chapter.revision += 1

        msg = {
            "message_id": "user_saved_chapter_to_revision",
            "message_args": [request.user.username, chapter.title, chapter.revision]}

    else:
        msg = {
            "message_id": "user_saved_chapter",
            "message_args": [request.user.username, chapter.title]}

    chapter.content = content
    chapter.save()

    # send chat message to channel
    msg.update({
        "command": "message_info", "from": request.user.username, "email": request.user.email})
    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, msg, myself=True)

    # TODO: not sure if this ever gets evaluated as true.
    # Check it later and remove if not used
    if not message.get('continue'):
        sputnik.addMessageToChannel(
            request, "/booktype/book/%s/%s/" % (bookid, version), {
                "command": "chapter_status",
                "chapterID": message["chapterID"],
                "status": "normal",
                "username": request.user.username
            })

        sputnik.rdelete("type:%s:edit:%s:locks:%s:%s" % (bookid, message["chapterID"], request.user.username))

    # fire the signal
    import booki.editor.signals
    booki.editor.signals.chapter_modified.send(sender=book_version, chapter=chapter, user=request.user)

    return {}


def remote_chapter_delete(request, message, bookid, version):
    """
    Delete chapter.

    Creates Book history record. Sends notification to chat. Sends "chapter_status"
    message to the channel. Sends "chapter_rename" message to the channel.

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

    if not book_security.has_perm('edit.delete_chapter'):
        raise PermissionDenied

    try:
        # get toc item related with chapter to be deleted
        chap = models.Chapter.objects.get(id__exact=int(message["chapterID"]), version=book_version)
    except models.Chapter.DoesNotExist:
        return dict(result=False)

    # if chapter under edit -> decline delete operation
    if chap.get_current_editor_username():
        raise PermissionDenied

    # if chapter is locked -> check access
    if chap.is_locked():
        # check access
        if not book_security.has_perm('edit.edit_locked_chapter'):
            raise PermissionDenied
        elif not book_security.is_admin() and (chap.lock.type == models.ChapterLock.LOCK_EVERYONE
                                               and chap.lock.user != request.user):
            raise PermissionDenied

    chap.delete()

    # MUST DELETE FROM TOC ALSO

    sputnik.addMessageToChannel(
        request, "/chat/%s/" % bookid, {
            "command": "message_info",
            "from": request.user.username,
            "email": request.user.email,
            "message_id": "user_delete_chapter",
            "message_args": [request.user.username, chap.title]
        },
        myself=True
    )

    logBookHistory(
        book=book,
        version=book_version,
        args={'chapter': chap.title},
        user=request.user,
        kind='chapter_delete'
    )

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_delete",
            "chapterID": message["chapterID"]
        },
        myself=True
    )

    send_notification(request, bookid, version, "notification_chapter_was_deleted", chap.title)

    return {"result": True}


def remote_section_delete(request, message, bookid, version):
    """
    Delete chapter.

    Creates Book history record. Sends notification to chat. Sends "chapter_status"
    message to the channel. Sends "chapter_rename" message to the channel.

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

    if not book_security.has_perm('edit.delete_section'):
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
                        book=book,
                        version=book_version,
                        args={'chapter': toc_item.chapter.title},
                        user=request.user,
                        kind='chapter_delete'
                    )
                    toc_item.chapter.delete()
                else:
                    # log section delete in book history
                    logBookHistory(
                        book=book,
                        version=book_version,
                        args={'section': toc_item.name},
                        user=request.user,
                        kind='section_delete'
                    )
                    toc_item.delete()
    else:
        # in case user doesn't want to remove chapters, change the parent
        for toc_item in sec.booktoc_set.all():
            toc_item.parent = None
            toc_item.save()

    # log main section delete in book history
    logBookHistory(
        book=book,
        version=book_version,
        args={'section': sec.name},
        user=request.user,
        kind='section_delete'
    )
    sec.delete()

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "section_delete",
            "chapterID": message["chapterID"],
            "deleteChildren": message["deleteChildren"]
        },
        myself=True
    )
    if delete_children == u'on':
        send_notification(request, bookid, version, "notification_section_with_chapters_inside_was_deleted", sec.name)
    else:
        send_notification(request, bookid, version, "notification_section_was_deleted", sec.name)

    return {"result": True}


def remote_chapter_rename(request, message, bookid, version):
    """
    Rename chapter name.

    Creates Book history record. Sends notification to chat. Sends "chapter_status" message to the channel.
    Sends "chapter_rename" message to the channel.

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

    if not book_security.has_perm('edit.rename_chapter'):
        raise PermissionDenied

    try:
        # get toc item related to chapter
        toc_item = models.BookToc.objects.get(id__exact=int(message["tocID"]), version=book_version)
    except models.BookToc.DoesNotExist:
        return dict(result=False)

    # check security
    chapter = toc_item.chapter

    # if chapter under edit by another user
    editor_username = chapter.get_current_editor_username()
    if editor_username and editor_username != request.user.username:
        raise PermissionDenied

    # if chapter is locked -> check access
    if chapter.is_locked():
        # check access
        if not book_security.has_perm('edit.edit_locked_chapter'):
            raise PermissionDenied
        elif not book_security.is_admin() and (chapter.lock.type == models.ChapterLock.LOCK_EVERYONE
                                               and chapter.lock.user != request.user):
            raise PermissionDenied

    old_title = chapter.title
    chapter.title = message["chapter"]
    chapter.save()

    logBookHistory(
        book=chapter.book,
        version=book_version,
        chapter=chapter,
        user=request.user,
        args={"old": old_title, "new": message["chapter"]},
        kind="chapter_rename"
    )

    sputnik.addMessageToChannel(
        request, "/chat/%s/" % bookid, {
            "command": "message_info",
            "from": request.user.username,
            "email": request.user.email,
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

    send_notification(request, bookid, version, "notification_chapter_was_renamed", old_title, chapter.title)

    return dict(result=True)


def remote_section_rename(request, message, bookid, version):
    """
    Rename section name.

    Creates Book history record. Sends notification to chat. Sends "chapter_status"
    message to the channel. Sends "chapter_rename" message to the channel.

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

    if not book_security.has_perm('edit.rename_section'):
        raise PermissionDenied

    # check security
    sectionID = message["chapterID"]

    toc_item = models.BookToc.objects.get(id__exact=int(sectionID), version=book_version)
    old_title = toc_item.name
    toc_item.name = message["chapter"]
    toc_item.save()

    logBookHistory(
        book=book,
        version=book_version,
        chapter=None,
        user=request.user,
        args={"old": old_title, "new": message["chapter"]},
        kind="section_rename"
    )

    sputnik.addMessageToChannel(
        request, "/chat/%s/" % bookid, {
            "command": "message_info",
            "from": request.user.username,
            "email": request.user.email,
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

    send_notification(request, bookid, version, "notification_section_was_renamed", old_title, toc_item.name)

    return dict(result=True)


def remote_chapters_changed(request, message, bookid, version):
    """
    Reorders the TOC.

    Creates Book history record. Sends "chapters_changed" message to the channel.

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

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('edit.reorder_toc'):
        raise PermissionDenied

    lst = [(chap['item_id'], chap['parent_id']) for chap in message["chapters"]]
    lstHold = []

    weight = len(lst)

    logBookHistory(
        book=book,
        version=book_version,
        user=request.user,
        kind="chapter_reorder"
    )

    for chap in lst:
        try:
            toc_item = models.BookToc.objects.get(id__exact=int(chap[0]), version=book_version)
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
            m = models.BookToc.objects.get(id__exact=message["chapter_id"][1:], version=book_version)
            m.delete()
        else:
            m = models.BookToc.objects.get(chapter__id__exact=int(message["chapter_id"]), version=book_version)
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

    send_notification(request, bookid, version, "notification_toc_order_was_changed")

    # TODO
    # this should be changed, to check for errors

    return {"result": True}


def remote_chapter_hold(request, message, bookid, version):

    book, book_version, book_security = get_book(request, bookid, version)
    chapter_id = message["chapterID"]

    try:
        toc_item = models.BookToc.objects.get(chapter__id__exact=chapter_id, version=book_version, typeof=1)
    except models.BookToc.DoesNotExist:
        return dict(result=False)

    # if chapter under edit -> decline
    if toc_item.chapter.get_current_editor_username() or not book_security.has_perm('edit.manage_chapter_hold'):
        raise PermissionDenied

    # if chapter is locked -> check access
    if toc_item.chapter.is_locked():
        # check access
        if not book_security.has_perm('edit.edit_locked_chapter'):
            raise PermissionDenied
        elif not book_security.is_admin() and (toc_item.chapter.lock.type == models.ChapterLock.LOCK_EVERYONE
                                               and toc_item.chapter.lock.user != request.user):
            raise PermissionDenied

    toc_id = toc_item.id
    toc_item.delete()

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_hold",
            "chapterID": chapter_id,
            "tocID": toc_id
        },
        myself=True
    )

    send_notification(request, bookid, version, "notification_chapter_put_on_hold", toc_item.chapter.title)

    return dict(result=True)


def remote_chapter_unhold(request, message, bookid, version):

    book, book_version, book_security = get_book(request, bookid, version)
    chapter_id = message["chapterID"]

    try:
        chptr = models.Chapter.objects.get(id__exact=chapter_id, version=book_version)
    except models.Chapter.DoesNotExist:
        return dict(result=False)

    # if chapter under edit -> decline
    if chptr.get_current_editor_username() or not book_security.has_perm('edit.manage_chapter_hold'):
        raise PermissionDenied

    # if chapter is locked -> check access
    if chptr.is_locked():
        # check access
        if not book_security.has_perm('edit.edit_locked_chapter'):
            raise PermissionDenied
        elif not book_security.is_admin() and (chptr.lock.type == models.ChapterLock.LOCK_EVERYONE
                                               and chptr.lock.user != request.user):
            raise PermissionDenied

    # chapter can be only in one toc in single moment
    if not models.BookToc.objects.filter(chapter=chptr).exists():
        toc_item = models.BookToc(book=book, version=book_version, name=chptr.title, chapter=chptr,
                                  weight=-1, typeof=1)
        toc_item.save()

        sputnik.addMessageToChannel(
            request, "/booktype/book/%s/%s/" % (bookid, version), {
                "command": "chapter_unhold",
                "chapterID": chapter_id,
                'tocID': toc_item.id
            },
            myself=True
        )

    send_notification(request, bookid, version, "notification_chapter_unheld", chptr.title)

    return {"result": True}


def remote_chapter_lock(request, message, bookid, version):
    """
    Sputnik request handler for locking chapter.

    Args:
      reuest: Client Request object
      message: Message object
      bookid: Unique Book id
      version: Book version

    Returns:
      Dict. Example {result=True}
    """

    book, book_version, book_security = get_book(request, bookid, version)
    chapter_id = message["chapterID"]
    lock_type = message["lockType"]

    # validate lock type value
    if lock_type not in (models.ChapterLock.LOCK_SIMPLE, models.ChapterLock.LOCK_EVERYONE):
        raise SuspiciousOperation

    # check access
    if not book_security.has_perm('edit.lock_chapter'):
        raise PermissionDenied

    try:
        # get chapter
        chapter = models.Chapter.objects.get(id=int(chapter_id), version=book_version)

        # if chapter under edit -> decline
        if chapter.get_current_editor_username():
            raise PermissionDenied

        # create lock for provided chapter
        models.ChapterLock.objects.create(chapter=chapter, user=request.user, type=lock_type)

    except (models.Chapter.DoesNotExist, IntegrityError):
        return dict(result=False)

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_lock_changed",
            "chapterID": chapter_id,
            "lockType": chapter.lock_type,
            "lockUsername": request.user.username
        },
        myself=True
    )

    send_notification(request, bookid, version, "notification_chapter_was_locked", chapter.title)

    return dict(result=True)


def remote_chapter_unlock(request, message, bookid, version):
    """
    Sputnik request handler for unlocking chapter.

    Args:
      reuest: Client Request object
      message: Message object
      bookid: Unique Book id
      version: Book version

    Returns:
      Dict. Example {result=True}
    """

    book, book_version, book_security = get_book(request, bookid, version)
    chapter_id = message["chapterID"]

    # get chapter
    try:
        chapter = models.Chapter.objects.get(id=int(chapter_id), version=book_version)
    except models.Chapter.DoesNotExist:
        return dict(result=False)

    # if chapter under edit -> decline
    if chapter.get_current_editor_username():
        raise PermissionDenied

    # check access
    if not book_security.has_perm('edit.lock_chapter'):
        raise PermissionDenied
    elif not book_security.is_admin() and (chapter.lock.type == models.ChapterLock.LOCK_EVERYONE
                                           and chapter.lock.user != request.user):
        raise PermissionDenied

    # remove lock
    chapter.lock.delete()
    chapter.save()

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_lock_changed",
            "chapterID": message["chapterID"],
            "lockType": chapter.lock_type
        },
        myself=True
    )

    send_notification(request, bookid, version, "notification_chapter_was_unlocked", chapter.title)

    return dict(result=True)


def remote_export_chapter_html(request, message, bookid, version):
    """
    Sputnik request handler for exporting chapter's html content.

    Args:
      reuest: Client Request object
      message: Message object
      bookid: Unique Book id
      version: Book version

    Returns:
      Dict. Example {result=True}
    """

    book, book_version, book_security = get_book(request, bookid, version)
    chapter_id = message["chapterID"]

    # get chapter
    try:
        chapter = models.Chapter.objects.get(id=int(chapter_id), version=book_version)
    except models.Chapter.DoesNotExist:
        return dict(result=False)

    # check access
    if not book_security.has_perm('edit.export_chapter_content'):
        raise PermissionDenied

    try:
        content = {'content': clean_chapter_html(chapter.content), 'error': False}
    except:
        content = {'content': '', 'error': True}

    return content


def remote_split_chapter(request, message, bookid, version):
    res = {"result": False, "access": False}

    # check if user has permissions for splitting this chapter.
    try:
        book, book_version, book_security = get_book(request, bookid, version)
        current_chapter = models.Chapter.objects.get(id=int(message["chapterID"]), version=book_version)
    except (models.Chapter.DoesNotExist, PermissionDenied):
        res["reason"] = ugettext("You have no permissions for splitting the chapter.")
        return res

    # check if user has permission for creating chapter
    if not book_security.has_perm('edit.create_chapter'):
        res["reason"] = ugettext("You have no permissions for splitting the chapter.")
        return res

    # if chapter under edit by another user -> decline
    editor_username = current_chapter.get_current_editor_username()
    if editor_username and editor_username != request.user.username:
        res["reason"] = ugettext("Chapter is under edit.")
        return res

    # if chapter is locked -> check access
    if current_chapter.is_locked():
        # check access
        if not book_security.has_perm('edit.edit_locked_chapter'):
            res["reason"] = ugettext("You have no permissions for splitting locked chapter.")
            return res
        elif not book_security.is_admin() and (current_chapter.lock.type == models.ChapterLock.LOCK_EVERYONE
                                               and current_chapter.lock.user != request.user):
            res["reason"] = ugettext("You have no permissions for splitting locked chapter.")
            return res

    # set access after all permissions were checked
    res['access'] = True

    url_title = booktype_slugify(message["title"])

    if len(url_title) == 0:
        res["reason"] = ugettext("You have selected invalid title name.")
        return res

    if models.Chapter.objects.filter(book=book, version=book_version, url_title=url_title).exists():
        res["reason"] = ugettext("Chapter with this title already exists.")
        return res

    try:
        # create new chapter
        status = models.BookStatus.objects.filter(book=book).order_by("-weight")[0]
        content = u'<h1>%s</h1>%s' % (message["title"], message["content"])
        new_chapter = models.Chapter(book=book,
                                     version=book_version,
                                     url_title=url_title,
                                     title=message["title"],
                                     status=status,
                                     content=content,
                                     created=django_datetime.now(),
                                     modified=django_datetime.now())
        new_chapter.save()

        do_increase = False

        # update chapters weight and create new toc item
        for item in book_version.get_toc():
            if do_increase:
                item.weight -= 1
                item.save()

            if item.is_chapter() and item.chapter.pk == current_chapter.pk:
                do_increase = True
                toc_item = models.BookToc(version=book_version,
                                          book=book,
                                          parent=item.parent,
                                          name=message["title"],
                                          chapter=new_chapter,
                                          weight=item.weight - 1,
                                          typeof=1)
                toc_item.save()

        # create history for newly created chapter
        history = logChapterHistory(
            chapter=new_chapter,
            content=content,
            user=request.user,
            comment=message.get("comment", ""),
            revision=new_chapter.revision
        )

        if history:
            logBookHistory(
                book=book,
                version=book_version,
                chapter=new_chapter,
                chapter_history=history,
                user=request.user,
                kind='chapter_create'
            )

    except Exception as e:
        logger.error('Error during chapter splitting: {0}'.format(e))
        transaction.rollback()
        return res

    # send notifications for editor
    sputnik.addMessageToChannel(
        request, "/chat/%s/" % bookid, {
            "command": "message_info",
            "from": request.user.username,
            "email": request.user.email,
            "message_id": "user_new_chapter",
            "message_args": [request.user.username, new_chapter.title]
        },
        myself=True
    )

    toc_id = None
    try:
        toc_id = toc_item.id
    except Exception:
        pass

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_create",
            "chapter": (new_chapter.id,
                        new_chapter.title,
                        new_chapter.url_title,
                        1,
                        status.id,
                        new_chapter.lock_type,
                        new_chapter.lock_username,
                        "root",
                        toc_id,
                        "normal",
                        None)
        },
        myself=False
    )

    send_notification(request, bookid, version, "notification_chapter_was_created", new_chapter.title)

    res['status'] = True
    res['result'] = True
    res['chapters'] = get_toc_for_book(book_version)
    res['hold'] = get_hold_chapters(book_version)

    return res


def remote_get_chapter(request, message, bookid, version):
    """
    This is called when you fire up WYSWYG editor or Chapter viewer. It sends back basic chapter information.

    If edit_lock flag is send then it will Sends message "chapter_state" to the channel and create edit_lock
    for this chapter.

    Input:
     - chapterID
     - edit_lock (True or False)
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

    res = {"result": True, "access": False}

    # check if user has permissions for editing this chapter.
    # if user has no permissions or chapter locked at the moment
    # function return access=False and reason message.
    try:
        book, book_version, book_security = get_book(request, bookid, version)
        chapter = models.Chapter.objects.get(id=int(message["chapterID"]), version=book_version)
    except (models.Chapter.DoesNotExist, PermissionDenied):
        # book_security.can_edit() is not implemented yet
        res["reason"] = ugettext("You have no permissions for editing this chapter.")
        return res

    # TODO clarify about read only mode
    # check if chapter is locked or under edit
    if message.get("edit_lock", False):
        editor_username = chapter.get_current_editor_username()

        if editor_username and editor_username != request.user.username:
            res["reason"] = ugettext("Chapter currently being edited.")
            return res

        if chapter.is_locked():
            if not book_security.has_perm('edit.edit_locked_chapter'):
                res["reason"] = ugettext("You have no permissions for editing chapters under lock.")
                return res
            elif not book_security.is_admin() and (chapter.lock.type == models.ChapterLock.LOCK_EVERYONE
                                                   and chapter.lock.user != request.user):
                res["reason"] = ugettext("Chapter currently is locked from everyone.")
                return res

    res["access"] = True
    res["title"] = chapter.title
    res["content"] = chapter.content
    res["current_revision"] = chapter.revision

    if message.get("revisions", False):
        revision_qs = models.ChapterHistory.objects.filter(chapter=chapter).order_by("revision")
        res["revisions"] = [x.revision for x in revision_qs]

    if message.get("revision", chapter.revision) != chapter.revision:
        ch = models.ChapterHistory.objects.get(chapter=chapter, revision=message.get("revision"))
        res["content"] = ch.content

    # if this chapter for edit or read
    if message.get("edit_lock", False):

        # set the initial timer edit locking
        sputnik.set(
            "booktype:%s:%s:editlocks:%s:%s" % (
                bookid, version, message["chapterID"], request.user.username),
            time.time())

        sputnik.addMessageToChannel(
            request, "/booktype/book/%s/%s/" % (bookid, version), {
                "command": "chapter_state",
                "chapterID": message["chapterID"],
                "state": "edit",
                "username": request.user.username
            }, myself=False)

    return res


def remote_create_chapter(request, message, bookid, version):
    """
    Creates new chapters. New chapter is always added at the end of the TOC.
    Creates empty chapter content only with chapter title as heading.

    Record for Chapter and Book history is created. Message "chapter_create"
    is send to the channel. Notification is send to the chat.

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

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('edit.create_chapter'):
        raise PermissionDenied

    url_title = booktype_slugify(message["chapter"])
    if len(url_title) == 0:
        return {"result": False, "created": False, "silly_url": True}

    # for now, just limit it to 100 characters max
    url_title = url_title[:100]

    # here I should probably set it to default project status
    s = models.BookStatus.objects.filter(book=book).order_by("-weight")[0]
    ch = models.Chapter.objects.filter(
        book=book, version=book_version, url_title=url_title)

    if len(list(ch)) > 0:
        return {"created": False, "chapter_exists": True}

    content = u'<h1>%s</h1><p><br/></p>' % message["chapter"]

    chapter = models.Chapter(
        book=book,
        version=book_version,
        url_title=url_title,
        title=message["chapter"],
        status=s,
        content=content,
        created=datetime.datetime.now(),
        modified=datetime.datetime.now()
    )
    chapter.save()

    weight = len(book_version.get_toc()) + 1
    for itm in models.BookToc.objects.filter(
        version=book_version, book=book
    ).order_by("-weight"):

        itm.weight = weight
        itm.save()

        weight -= 1

    toc_item = models.BookToc(
        version=book_version,
        book=book,
        name=message["chapter"],
        chapter=chapter,
        weight=1,
        typeof=1
    )
    toc_item.save()

    history = logChapterHistory(
        chapter=chapter,
        content=content,
        user=request.user,
        comment=message.get("comment", ""),
        revision=chapter.revision
    )

    if history:
        logBookHistory(
            book=book,
            version=book_version,
            chapter=chapter,
            chapter_history=history,
            user=request.user,
            kind='chapter_create'
        )

    checked_statuses = list(chapter.checked_statuses.values_list('pk', flat=True))

    # TODO: turn this into dict to make it more readable
    result = (
        chapter.id,
        chapter.title,
        chapter.url_title,
        1,                      # typeof (chapter)
        chapter.status.id,      # status
        chapter.lock_type,
        chapter.lock_username,
        "root",                 # parent id (first level)
        toc_item.id,            # tocID
        "normal",               # fake state
        None,                   # fake current editor,
        checked_statuses
    )

    sputnik.addMessageToChannel(
        request, "/chat/%s/" % bookid, {
            "command": "message_info",
            "from": request.user.username,
            "email": request.user.email,
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
        myself=True
    )

    send_notification(request, bookid, version, "notification_chapter_was_created", chapter.title)

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

    att = models.Attachment(
        book=target_book,
        version=target_book.version,
        status=target_book.status,
        created=datetime.datetime.now()
    )

    att.attachment.save(
        os.path.basename(attachment.attachment.name),
        attachment.attachment,
        save=False
    )
    att.save()
    return att


def remote_create_section(request, message, bookid, version):
    """
    Creates new section. Sections is added at the end of the TOC.

    Creates Book history entry. Sends "chapter_create" message to the channel.
    Sends notification to chat.

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

    if not book_security.has_perm('edit.create_section'):
        raise PermissionDenied

    ch = models.BookToc.objects.filter(
        book=book,
        version=book_version,
        name=message['chapter'],
        typeof=0
    )

    if len(list(ch)) > 0:
        return {"created": False, "section_exists": True}

    c = models.BookToc(
        book=book,
        version=book_version,
        name=message["chapter"],
        chapter=None,
        weight=0,
        typeof=0
    )

    result = True
    c.save()

    logBookHistory(
        book=book,
        version=book_version,
        user=request.user,
        args={"title": message["chapter"]},
        kind='section_create'
    )

    result = (
        c.id,
        c.name,
        c.name,
        c.typeof,
        None,       # fake status
        0,          # fake unlocked
        None,       # fake lock username
        "root",
        c.id,
        "normal",   # fake state
        None        # fake current editor
    )

    sputnik.addMessageToChannel(
        request, "/chat/%s/" % bookid, {
            "command": "message_info",
            "from": request.user.username,
            "email": request.user.email,
            "message_id": "user_new_section",
            "message_args": [request.user.username, message["chapter"]]
        },
        myself=True
    )

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_create",
            "chapter": result,
            "typeof": c.typeof
        },
        myself=True
    )

    send_notification(request, bookid, version, "notification_section_was_created", c.name)

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

    # TODO this function should be reusable
    def _get_dimension(cover):
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
            'dimension': _get_dimension(cover),
            'approved': cover.approved})

    covers.reverse()

    return {"covers": covers, "can_update": book_security.is_admin()}


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

    if not book_security.has_perm('edit.edit_cover'):
        raise PermissionDenied

    cover = models.BookCover.objects.get(book=book, cid=message.get('cid', ''))
    cover.approved = message.get('cover_status', False)
    cover.save()

    logBookHistory(
        book=book,
        version=book_version,
        args={
            'filename': cover.filename, 'title': cover.title, 'cid': cover.pk
        },
        user=request.user,
        kind='cover_update'
    )

    return {"result": True}


def remote_cover_delete(request, message, bookid, version):
    """
    Delete cover image.


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

    if not book_security.has_perm('edit.delete_cover'):
        raise PermissionDenied

    cover = models.BookCover.objects.get(book=book, cid=message.get('cid', ''))
    logBookHistory(
        book=book,
        version=book_version,
        args={'filename': cover.filename, 'title': cover.title, 'cid': cover.pk},
        user=request.user,
        kind='cover_delete'
    )
    cover.delete()

    send_notification(request, bookid, version, "notification_cover_was_deleted", cover.title)

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

    if not book_security.has_perm('edit.edit_cover'):
        raise PermissionDenied

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

    send_notification(request, bookid, version, "notification_cover_was_updated", cover.title)

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


@transaction.atomic
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

    return {"result": True, "cover": cover, "licenses": licenses}


def remote_publish_book(request, message, bookid, version):
    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('export.export_book'):
        raise PermissionDenied

    if not (set(config.get_configuration('PUBLISH_OPTIONS')) >= set(message['formats'])):
        return {'result': False,
                'reason': ugettext('One of the selected formats was disabled. Try to reload page.')}

    from . import tasks
    tasks.publish_book.apply_async((1, ), dict(bookid=bookid,
                                               version=version,
                                               username=request.user.username,
                                               clientid=request.clientID,
                                               sputnikid=request.sputnikID,
                                               formats=message["formats"]))

    return {'result': True}


def remote_word_count(request, message, bookid, version):
    from unidecode import unidecode
    from booktype.utils.wordcount import wordcount, charcount, charspacecount

    book = models.Book.objects.get(id=bookid)
    book_version = book.get_version(version)

    # get chapters
    chapters = models.BookToc.objects.filter(book=book, version=book_version)
    current_chapter = message['current_chapter_id']
    current_chapter_content = unidecode(message['current_chapter_content'])

    # count chapters data
    all_wcount = 0
    all_charcount = 0
    all_charspacecount = 0

    for chap in chapters:
        if chap.is_chapter() and chap.chapter.id != int(current_chapter):
            content = unidecode(chap.chapter.content)
            cleaned = clean_chapter_html(content, text_only=True)
            all_wcount += wordcount(cleaned)
            all_charcount += charcount(cleaned)
            all_charspacecount += charspacecount(cleaned)

    # time to count content of the current chapter
    chapter_content = clean_chapter_html(current_chapter_content, text_only=True)
    current_chapter = {
        'wcount': wordcount(chapter_content),
        'charcount': charcount(chapter_content),
        'charspacecount': charspacecount(chapter_content)
    }

    return {
        'result': True,
        'status': True,
        'wcount': all_wcount + current_chapter['wcount'],
        'charcount': all_charcount + current_chapter['charcount'],
        'charspacecount': all_charspacecount + current_chapter['charspacecount'],
        'current_chapter': current_chapter
    }


def remote_book_status_rename(request, message, bookid, version):
    """
    Renames a book status

    Sends notification to chat.


    Input:
      - status_name
      - status_id

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
    @return: Returns list of all statuses and id of the renamed one
    """

    book, book_version, book_security = get_book(request, bookid, version)
    status_id = None

    if not book_security.has_perm('edit.manage_status'):
        raise PermissionDenied

    from django.utils.html import strip_tags

    try:
        bs = models.BookStatus.objects.get(book=book, id=message["status_id"])
        bs.name = strip_tags(message["status_name"].strip())
        bs.save()
    except models.BookStatus.DoesNotExist:
        pass

    all_statuses = get_book_statuses(book)

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "book_status_renamed",
            "statuses": all_statuses
        },
        myself=False
    )

    return {
        "status": True,
        "status_id": status_id,
        "statuses": all_statuses
    }


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

    if not book_security.has_perm('edit.manage_status'):
        raise PermissionDenied

    weight = 100

    for status_id in [x[11:] for x in message["order"]]:
        up = models.BookStatus.objects.get(book=book, id=status_id)
        up.weight = weight
        up.save()

        weight -= 1

    all_statuses = get_book_statuses(book)

    sputnik.addMessageToChannel(
        request,
        "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_status_changed",
            "statuses": all_statuses
        }, myself=False)

    return {"result": True, "statuses": all_statuses}


def remote_book_status_remove(request, message, bookid, version):
    """
    Removes book status. In case status is being used by chapters or attachment
    it will reassign chapters and attachments to default status.

    Note: default status cannot be removed

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

    if not book_security.has_perm('edit.manage_status'):
        raise PermissionDenied

    result = True
    msg = None

    up = models.BookStatus.objects.get(book=book, id=message["status_id"])
    assigned_chapters = models.Chapter.objects.filter(status=up, book=book)
    assigned_attachments = models.Attachment.objects.filter(status=up, version__book=book)

    default_status_name = get_default_book_status()

    if book.status == up:
        msg = _lazy("Unable to delete. Status used in current book")

    if default_status_name == up.name:
        msg = _lazy("Default status cannot be deleted")

    if msg is not None:
        return {"result": False, "message": msg}

    # ressign any chapter or attachments to default status
    if assigned_chapters.count() > 0 or assigned_attachments.count() > 0:
        try:
            default_status = models.BookStatus.objects.get(book=book, name=default_status_name)
        except models.BookStatus.DoesNotExist:
            return {
                "result": False,
                "message": _lazy("Unable to reassign registries. Default status is missing.")
            }

        for chap in assigned_chapters:
            chap.status = default_status
            chap.save()

        for attach in assigned_attachments:
            attach.status = default_status
            attach.save()

    # TODO: sync other clients when statuses changed
    up.delete()

    all_statuses = get_book_statuses(book)

    sputnik.addMessageToChannel(
        request,
        "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_status_changed",
            "statuses": all_statuses
        },
        myself=False)

    return {
            "result": result,
            "statuses": all_statuses
        }


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

    if not book_security.has_perm('edit.manage_status'):
        raise PermissionDenied

    from django.utils.html import strip_tags

    bs = models.BookStatus(
        book=book,
        name=strip_tags(message["status_name"].strip()),
        weight=0
    )
    bs.save()

    status_id = bs.id

    all_statuses = get_book_statuses(book)

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "chapter_status_changed",
            "statuses": all_statuses
        },
        myself=False)

    return {
        "result": True,
        "status_id": status_id,
        "statuses": all_statuses
    }


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

    users = [(u.user.username, '%s (%s)' % (u.user.username, u.user.first_name)) for u in models.BookiPermission.objects.filter(book=book, permission=message["role"]).order_by("user__username")]

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

    res = {"result": True, "terminate": False}

    if request.user.username:
        _, book_version, _ = get_book(request, bookid, version)

        try:
            chapter = models.Chapter.objects.get(id=int(message["chapterID"]), version=book_version)
        except models.Chapter.DoesNotExist:
            return dict(result=False)

        # if chapter under edit by another user -> decline
        if chapter.get_current_editor_username() != request.user.username:
            raise SuspiciousOperation

        # update timer for edit locking
        edit_lock_key = "booktype:%s:%s:editlocks:%s:%s" % (bookid, version, message["chapterID"], request.user.username)
        sputnik.set(edit_lock_key, time.time())

        # terminate editing if needed
        kill_edit_lock_key = "booktype:%s:%s:killeditlocks:%s:%s" % (bookid, version, message["chapterID"],
                                                                     request.user.username)

        if '%s' % sputnik.get(kill_edit_lock_key) == '1':
            sputnik.rdelete(kill_edit_lock_key)
            res["terminate"] = True

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

    from booki.editor.common import parseJSON

    book, book_version, book_security = get_book(request, bookid, version)

    page = int(message.get("page", 1))

    book_history = models.BookHistory.objects.filter(book=book).order_by("-modified")[(page - 1) * 50:(page - 1) * 50 + 50]

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
                            "kind": temp.get(entry.kind, '')})
        elif entry.kind == 2 and entry.chapter:
            history.append({"chapter": entry.chapter.title,
                            "chapter_url": entry.chapter.url_title,
                            "chapter_history": entry.chapter_history.id,
                            "modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"),
                            "description": entry.args,
                            "user": entry.user.username,
                            "kind": temp.get(entry.kind, '')})
        elif entry.kind in [11, 12]:
            history.append({"modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"),
                            "version": parseJSON(entry.args),
                            "user": entry.user.username,
                            "kind": temp.get(entry.kind, '')})
        elif entry.kind in [13, 14, 16, 17, 18]:
            history.append({"modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"),
                            "args": parseJSON(entry.args),
                            "user": entry.user.username,
                            "kind": temp.get(entry.kind, '')})
        elif entry.kind in [15]:
            history.append({"chapter": entry.chapter.title,
                            "chapter_url": entry.chapter.url_title,
                            "description": entry.args,
                            "modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"),
                            "user": entry.user.username,
                            "kind": temp.get(entry.kind, '')})
        elif entry.kind in [19]:
            history.append({"args": parseJSON(entry.args),
                            "modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"),
                            "user": entry.user.username,
                            "kind": temp.get(entry.kind, '')})
        else:
            history.append({"modified": entry.modified.strftime("%d.%m.%Y %H:%M:%S"),
                            "description": entry.args,
                            "user": entry.user.username,
                            "kind": temp.get(entry.kind, '')})

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

    book, book_version, book_security = get_book(request, bookid, version)

    chapter_history = models.ChapterHistory.objects.filter(
        chapter__book=book, chapter__id=message["chapter"]).order_by("-revision")

    history = []

    for entry in chapter_history:
        history.append({
            "chapter": entry.chapter.title,
            "chapter_url": entry.chapter.url_title,
            "modified": entry.modified.strftime("%b %d, %Y %H:%M:%S"),
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

    chapter = models.Chapter.objects.get(version=book_version,
                                         id=message["chapter"])

    revision = models.ChapterHistory.objects.get(revision=message["revision"],
                                                 chapter__id=message["chapter"],
                                                 chapter__version=book_version.id)

    # TODO
    # does chapter history really needs to keep content or it can only keep reference to chapter

    history = logChapterHistory(chapter=chapter,
                                content=revision.content,
                                user=request.user,
                                comment="Reverted to revision %s." % message["revision"],
                                revision=chapter.revision + 1)

    if history:
        logBookHistory(book=book,
                       version=book_version,
                       chapter=chapter,
                       chapter_history=history,
                       user=request.user,
                       args={},
                       kind='chapter_save')

    chapter.revision += 1
    chapter.content = revision.content

    chapter.save()

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid,
                                {"command": "message_info",
                                 "from": request.user.username,
                                 "email": request.user.email,
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
    notes = message.get('notes')
    book_notes_obj = None

    if not book_security.has_perm('edit.note_edit'):
        raise PermissionDenied

    if len(book_notes) == 0:
        book_notes_obj = models.BookNotes(book=book, notes=notes)
    else:
        book_notes_obj = book_notes[0]

    book_notes_obj.notes = notes
    book_notes_obj.save()

    sputnik.addMessageToChannel(
        request, "/chat/%s/" % bookid, {
            "command": "message_info",
            "from": request.user.username,
            "email": request.user.email,
            "message_id": "user_saved_notes",
            "message_args": [request.user.username, book.title]
        },
        myself=True
    )

    send_notification(request, bookid, version, "notification_notes_were_changed")

    return {"result": True}


def remote_chapter_kill_editlock(request, message, bookid, version):
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

    book, book_version, book_security = get_book(request, bookid, version)

    if book_security.is_admin():
        for key in sputnik.rkeys("booktype:%s:%s:editlocks:%s:*" % (bookid, version, message["chapterID"])):
            m = re.match("booktype:(\d+):(\d+).(\d+):editlocks:(\d+):(\w+)", key)
            if m:
                username = m.group(5)
                sputnik.set("booktype:%s:%s:killeditlocks:%s:%s" % (bookid, version, message["chapterID"], username), 1)

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
                                   book=book,  # this should be removed
                                   url_title=chap.url_title,
                                   title=chap.title,
                                   status=chap.status,
                                   revision=chap.revision,
                                   created=datetime.datetime.now(),
                                   content=chap.content)
            nchap.save()

        ntoc = models.BookToc(version=new_version,
                              book=book,  # this should be removed
                              name=toc.name,
                              chapter=nchap,
                              weight=toc.weight,
                              typeof=toc.typeof)
        ntoc.save()

    # hold chapters

    for chap in book_ver.get_hold_chapters():
        c = models.Chapter(version=new_version,
                           book=book,  # this should be removed
                           url_title=chap.url_title,
                           title=chap.title,
                           status=chap.status,
                           revision=chap.revision,
                           created=datetime.datetime.now(),
                           content=chap.content)
        c.save()

    for att in book_ver.get_attachments():
        a = models.Attachment(version=new_version,
                              book=book,
                              status=att.status,
                              created=datetime.datetime.now())
        a.attachment.save(att.get_name(), att.attachment, save=False)
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

    new_version = create_new_version(book, book_version, message, book_version.major + 1, 0)

    logBookHistory(book=book,
                   version=new_version,
                   chapter=None,
                   chapter_history=None,
                   user=request.user,
                   args={"version": new_version.get_version()},
                   kind='major_version')

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

    new_version = create_new_version(book, book_version, message, book_version.major, book_version.minor + 1)

    logBookHistory(book=book,
                   version=new_version,
                   chapter=None,
                   chapter_history=None,
                   user=request.user,
                   args={"version": new_version.get_version()},
                   kind='minor_version')

    return {"result": True, "version": new_version.get_version()}


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
    @Type version: C{string}
    @param version: Book version
    @rtype: C{dict}
    @return: Returns text with diff between two chapters
    """

    from .views import unified_diff

    book, book_version, book_security = get_book(request, bookid, version)
    chapter_id = message["chapter"]
    content = message.get("content")

    content1 = models.ChapterHistory.objects.get(
        chapter__book=book, chapter__id=chapter_id, revision=message["revision1"]).content

    content2 = models.ChapterHistory.objects.get(
        chapter__book=book, chapter__id=chapter_id, revision=message["revision2"]).content

    # check with unsaved content
    if (content1 == content2) or content:
        content2 = content

    diff = unified_diff(content1, content2)

    return {"result": True, "output": diff}


def remote_assign_to_role(request, message, bookid, version):
    """
    Remote to assign user to an specific role. It checks if the role
    already exists for the current book, otherwise, it creates the role
    and assign the user as a member

    Arguments:
        - roleid
        - userid
    """

    try:
        user = User.objects.get(id=message['userid'])
    except User.DoesNotExist:
        return {'result': False}

    book, _version, book_security = get_book(request, bookid, version)
    if not book_security.has_perm('core.manage_roles'):
        raise PermissionDenied

    roleid = message.get('roleid')
    if roleid is None:
        return {'result': False}

    # check if roles exist, otherwise continue with next loop
    try:
        role = Role.objects.get(id=roleid)
    except Exception as err:
        logger.error("Unable to assign role to user %s", err)
        return {'result': False}

    book_role, _ = BookRole.objects.get_or_create(
        role=role, book=book)
    book_role.members.add(user)

    return {'result': True, 'role_id': book_role.id}


def remote_remove_user_from_role(request, message, bookid, version):
    """
    Removes a given user from an specific role.

    Arguments:
        - role
        - user
    """

    _book, _version, book_security = get_book(request, bookid, version)
    if not book_security.has_perm('core.manage_roles'):
        raise PermissionDenied

    try:
        user = User.objects.get(id=message['userid'])
        role = BookRole.objects.get(id=message['roleid'])
    except Exception as err:
        logger.error("Unable to remove role to user %s", err)
        return {'result': False}

    role.members.remove(user)
    return {'result': True}


def remote_set_theme(request, message, bookid, version):
    book, book_version, book_security = get_book(request, bookid, version)

    try:
        theme = BookTheme.objects.get(book=book)
        theme.active = message['theme']
        theme.save()
    except Exception:
        return {'result': False}

    sputnik.addMessageToChannel(
        request, "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "theme_changed",
            "theme": message['theme']
        },
        myself=False
    )


    send_notification(request, bookid, version, "notification_theme_was_changed", message['theme'])

    return {'result': True}


def remote_save_custom_theme(request, message, bookid, version):
    book, book_version, book_security = get_book(request, bookid, version)

    try:
        theme = BookTheme.objects.get(book=book)
        theme.custom = json.dumps(message['custom'])
        theme.save()
    except Exception:
        return {'result': False}

    return {'result': True}


def remote_get_export_list(request, message, bookid, version):
    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('export.export_view'):
        raise PermissionDenied

    from booktype.apps.export.models import BookExport, ExportFile, ExportComment

    exports = []

    for export in BookExport.objects.filter(version=book_version).order_by('-created'):
        comments = []

        for comment in ExportComment.objects.filter(export=export).order_by('created'):
            comments.append({
                'username': comment.user.username,
                'email': comment.user.email,
                'created': str(comment.created.strftime("%d.%m.%Y %H:%M:%S")),
                'content': comment.content
            })

        files = {}

        for fexport in ExportFile.objects.filter(export=export):

            files[fexport.typeof] = {
                'filename': fexport.filename,
                'status': fexport.status,
                'description': fexport.description,
                'filesize': fexport.filesize,
                'pages': fexport.pages
            }

        if export.published is None:
            _published = ''
        else:
            _published = str(export.published.strftime("%d.%m.%Y %H:%M:%S"))

        exports.append({
            'name': export.name,
            'username': export.user.username,
            'task_id': export.task_id,
            'created': str(export.created.strftime("%d.%m.%Y %H:%M:%S")),
            'published': _published,
            'status': export.status,
            'files': files,
            'comments': comments
        })

    return {'result': True, 'exports': exports}


def remote_post_export_comment(request, message, bookid, version):
    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('export.export_comment'):
        raise PermissionDenied

    from booktype.apps.export.models import BookExport, ExportComment

    book_export = BookExport.objects.get(task_id=message['task_id'])

    comment = ExportComment(
        export=book_export,
        user=request.user,
        created=datetime.datetime.now(),
        content=message['content'])
    comment.save()

    sputnik.addMessageToChannel(
        request,
        "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "new_export_comment",
            "task_id": message["task_id"],
            "username": request.user.username,
            "email": request.user.email,
            "created": str(comment.created.strftime("%d.%m.%Y %H:%M:%S")),
            "content": message['content']
        }, myself=False
    )

    return {
        'result': True,
        'comment': {
            'username': request.user.username,
            'email': request.user.email,
            'created': str(comment.created.strftime("%d.%m.%Y %H:%M:%S")),
            'content': comment.content
        }
    }


def remote_remove_export(request, message, bookid, version):
    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('export.export_delete'):
        raise PermissionDenied

    from booktype.apps.export.models import BookExport

    book_export = BookExport.objects.get(task_id=message['task_id'])

    book_export.delete()
    sputnik.addMessageToChannel(
        request,
        "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "remove_export",
            "task_id": message["task_id"]
        },
        myself=False
    )

    return {'result': True}


def remote_rename_export_name(request, message, bookid, version):
    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('export.export_book'):
        raise PermissionDenied

    from booktype.apps.export.models import BookExport

    book_export = BookExport.objects.get(task_id=message['task_id'])
    book_export.name = message['name']
    book_export.save()

    sputnik.addMessageToChannel(
        request,
        "/booktype/book/%s/%s/" % (bookid, version), {
            "command": "rename_export_name",
            "task_id": message["task_id"],
            "name": message['name']
        }, myself=False
    )

    return {'result': True}


def remote_export_settings_get(request, message, bookid, version):
    from booktype.apps.export.utils import get_settings

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('export.export_settings'):
        raise PermissionDenied

    export_format = message.get('format', '')

    covers = {}

    for cover in models.BookCover.objects.filter(approved=True, book=book).order_by("title"):
        extension = os.path.splitext(cover.attachment.name)[-1].lower()
        key = '{}/cover{}'.format(cover.cid, extension)

        cover_name = cover.title
        if len(cover_name.strip()) == 0:
            cover_name = cover.filename

        covers[key] = cover_name

    settings_options = get_settings(book, export_format)

    return {
        'result': True,
        'settings': settings_options,
        'covers': covers
    }


def remote_export_settings_set(request, message, bookid, version):
    from booktype.apps.export.utils import set_settings

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('export.export_settings'):
        raise PermissionDenied

    data = message.get('data', '[]')

    set_settings(book, message.get('format', ''), data)

    return {'result': True}


def remote_load_book_settings(request, message, bookid, version):
    """Just returns some basic settings of the book_version"""

    book, book_version, book_security = get_book(request, bookid, version)

    return {'track_changes': book_version.track_changes}


def remote_remove_metafield(request, message, bookid, version):
    """Removes an additional metadata field"""

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('edit.manage_metadata'):
        raise PermissionDenied

    try:
        meta_name = message.get('toDelete')
        models.Info.objects.filter(book=book, name=meta_name).delete()
    except Exception as e:
        return {'result': False, 'message': e}

    return {'result': True}


def remote_add_comment(request, message, bookid, version):
    """Creates a new comment for a give chapter"""

    import uuid
    from .models import Comment

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('edit.add_comment'):
        return {'result': False}

    chapter = models.Chapter.objects.get(pk=message["chapter_id"], version=book_version)
    com = Comment(
        chapter=chapter,
        is_imported=False,
        user=request.user,
        text=message["text"],
        content=message["content"],
        comment_id=str(uuid.uuid4()),
        date=datetime.datetime.now(),
    )
    com.save()

    comment = {
        'cid': com.comment_id,
        'author': com.get_author,
        'date': com.date.strftime('%s'),
        'text': com.text,
        'content': com.content
    }

    return {'result': True, 'new_comment': comment}


def remote_reply_comment(request, message, bookid, version):
    """Simple reply to an existent comment in a chapter"""

    import uuid
    from .models import Comment

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('edit.add_comment'):
        return {'result': False}

    chapter = models.Chapter.objects.get(pk=message["chapter_id"], version=book_version)
    comment = Comment.objects.get(chapter=chapter, comment_id=message["comment_id"])

    # save the comment reply
    com = Comment(
        text='',
        parent=comment,
        chapter=chapter,
        user=request.user,
        comment_id=str(uuid.uuid4()),
        date=datetime.datetime.now(),
        is_imported=False,
        content=message['content']
    )
    com.save()

    return {'result': True}


def remote_get_comments(request, message, bookid, version):
    """Retrieve the list of comments for a given chapter"""
    from .models import Comment

    book, book_version, book_security = get_book(request, bookid, version)

    chapter = models.Chapter.objects.get(pk=message["chapter_id"], version=book_version)

    comments = []
    status = 0

    if message.get('resolved', False):
        status = 1

    for comment in Comment.objects.filter(chapter=chapter, status=status, state=0, parent=None):
        replies = []

        for reply in Comment.objects.filter(chapter=chapter, parent=comment):
            replies.append({
                'cid': reply.comment_id,
                'author': reply.get_author,
                'date': reply.date.strftime('%s'),
                'text': '',
                'content': reply.content
            })

        comm = {
            'cid': comment.comment_id,
            'author': comment.get_author,
            'date': comment.date.strftime('%s'),
            'text': comment.text,
            'content': comment.content,
            'replies': replies
        }

        comments.append(comm)

    permissions = {
        'add_comment': book_security.has_perm('edit.add_comment'),
        'delete_comment': book_security.has_perm('edit.delete_comment'),
        'resolve_comment': book_security.has_perm('edit.resolve_comment'),
        'is_superuser': request.user.is_superuser
    }

    return {
        'result': True,
        'comments': comments,
        'permissions': permissions
    }


def remote_save_bulk_comments(request, message, bookid, version):
    """Saves multiple comments and replies provided in JSON array mode"""
    import uuid
    from datetime import datetime
    from .models import Comment

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('edit.add_comment'):
        return {'result': False}

    chapter = models.Chapter.objects.get(pk=message['chapter_id'], version=book_version)

    for comment in message.get('local_comments', []):
        # NOTE: creating user should change in future if we plan to have real time editing interface,
        # for now we just use the one logged in as author of the comment
        db_comment = Comment(
            chapter=chapter,
            is_imported=False,
            user=request.user,
            text=comment['text'],
            content=comment['content'],
            comment_id=comment['cid'],
            date=datetime.fromtimestamp(int(comment['date']))
        )
        try:
            db_comment.save()
        except Exception as err:
            logger.error('Unable to save parent comment %s' % err)
            continue

        for reply in comment.get('replies', []):
            reply = Comment(
                text='', parent=db_comment,
                comment_id=str(uuid.uuid4()),
                chapter=chapter, user=request.user,
                is_imported=False, content=reply['content'],
                date=datetime.fromtimestamp(int(reply['date']))
            )
            reply.save()

    return {'result': True}


def remote_resolve_comment(request, message, bookid, version):
    """Marks a comment as resolved"""

    from .models import Comment

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('edit.resolve_comment'):
        return {'result': False}

    chapter = models.Chapter.objects.get(pk=message['chapter_id'], version=book_version)

    comment = Comment.objects.get(chapter=chapter, comment_id=message['comment_id'])
    comment.status = 1
    comment.save()

    return {'result': True}


def remote_delete_comment(request, message, bookid, version):
    """Marks a comments as deleted"""

    from .models import Comment

    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('edit.delete_comment'):
        return {'result': False}

    chapter = models.Chapter.objects.get(pk=message['chapter_id'], version=book_version)

    comment = Comment.objects.get(chapter=chapter, comment_id=message['comment_id'])
    comment.state = 1
    comment.save()

    return {'result': True}


def remote_section_settings_get(request, message, bookid, version):
    """Returns the settings of a given section in json format"""

    SECTION_TYPE = 0
    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('edit.modify_section_settings'):
        return {'result': False}

    try:
        section = models.BookToc.objects.get(
            pk=message['section_id'],
            typeof=SECTION_TYPE,
            version=book_version
        )

        settings = json.loads(section.settings)
    except models.BookToc.DoesNotExist:
        return {'result': False}
    except:
        settings = {}

    return {
        'result': True,
        'settings': settings
    }


def remote_section_settings_set(request, message, bookid, version):
    """Saves the settings of a given section"""

    SECTION_TYPE = 0
    book, book_version, book_security = get_book(request, bookid, version)

    if not book_security.has_perm('edit.modify_section_settings'):
        return {'result': False}

    try:
        section = models.BookToc.objects.get(
            pk=message['section_id'],
            typeof=SECTION_TYPE,
            version=book_version
        )

        data = message.get('settings', {})
        section.settings = json.dumps(data)
        section.save()

        return {'result': True}
    except:
        return {'result': False}


def remote_check_markers(request, message, bookid, version):
    """Returns a list with the chapters that has markers in content"""

    book, book_version, book_security = get_book(request, bookid, version)
    marked_chapters = []

    for idx, item in enumerate(book_version.get_toc()):
        if item.is_chapter() and item.chapter.has_marker:
            marked_chapters.append({
                'title': item.chapter.title,
                'url_title': item.chapter.url_title,
                'id': item.chapter.pk
            })

    return {
        'result': True,
        'marked_chapters': marked_chapters
    }
