''' Chat message sending functions '''
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

import sputnik

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from booki.editor.models import Book
from booktype.utils import security
from booktype.apps.edit.models import ChatMessage, ChatThread


def remote_message_send(request, message, bookid):
    """
    Called when user is sending message to chat channel L{bookid}.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    """

    try:
        book = Book.objects.get(id=int(bookid))
    except Book.DoesNotExist:
        raise ObjectDoesNotExist
    except Book.MultipleObjectsReturned:
        raise ObjectDoesNotExist

    book_security = security.get_security_for_book(request.user, book)
    has_permission = book_security.can_edit()

    if not has_permission:
        raise PermissionDenied

    # get chat thread
    chat_thread, _ = ChatThread.objects.get_or_create(book=book)
    # create message
    chat_message = ChatMessage()
    chat_message.thread = chat_thread
    chat_message.sender = request.user
    chat_message.text = message["message"]
    chat_message.save()

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid,
                                {"command": "message_received",
                                 "email": request.user.email,
                                 "from": request.user.username,
                                 "important": message["important"],
                                 "message": message["message"]})
    return {}
