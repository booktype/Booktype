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

import time
import re
import decimal
import logging

from booki.editor.models import Chapter

logger = logging.getLogger('booktype')


def remote_ping(request, message):
    """
    Sends ping to the server. Just so we know client is still alive. It also removes old locks. This is not the place to do it at all,
    but once we have normal scheduled calls, will put it there.
    :Args:
      - request (:class:`django.http.HttpRequest`): Client Request object
      - message (dict): Message object
    """

    import sputnik

    sputnik.addMessageToChannel(request, "/booktype/", {})

    # kill old chapters which are no longer under edit
    keys = sputnik.rkeys("booktype:*:*:editlocks:*")

    for key in keys:
        last_ping = sputnik.get(key)

        try:
            last_ping = decimal.Decimal(last_ping)
        except Exception as e:
            logger.exception(e)

        if last_ping and decimal.Decimal("%f" % time.time()) - last_ping > Chapter.EDIT_PING_SECONDS_MAX_DELTA:
            sputnik.rdelete(key)
            m = re.match("booktype:(\d+):(\d+).(\d+):editlocks:(\d+):(\w+)", key)

            if m:
                bookid, version, chapter_id, username = (m.group(1), "{0}.{1}".format(m.group(2), m.group(3)),
                                                         m.group(4), m.group(5))

                sputnik.addMessageToChannel(request, "/booktype/book/%s/%s/" % (bookid, version),
                                            {"command": "chapter_state",
                                             "chapterID": chapter_id,
                                             "state": "normal",
                                             "username": username},
                                            myself=True)


# FIXME not implemented
def remote_disconnect(request, message):
    pass


def remote_subscribe(request, message):
    """
    Subscribes client to specific channels.

    Input:
     - chanels

    :Args:
      - request (:class:`django.http.HttpRequest`): Client Request object
      - message (dict): Message object
    """

    import sputnik

    for chnl in message["channels"]:
        if not sputnik.hasChannel(chnl):
            sputnik.createChannel(chnl)

        sputnik.addClientToChannel(chnl, request.sputnikID)


def remote_connect(request, message):
    """
    Initializes sputnik connection for this client. Creates clientID for this connection.

    Input:
     - chanels

    :Args:
      - request (:class:`django.http.HttpRequest`): Client Request object
      - message (dict): Message object

    :Returns:
      Returns unique Client ID for this connection
    """

    import sputnik

    ret = {}

    # does this work ?
    try:
        clientID = sputnik.incr("sputnik:client_id")
    except Exception as err:
        logger.warn("Not able to get cliend_id from sputnik. Msg: %s" % err)
        sputnik.rcon.connect()
        clientID = sputnik.incr("sputnik:client_id")

    ret["clientID"] = clientID
    request.sputnikID = "%s:%s" % (request.session.session_key, clientID)

    if not clientID:
        return

    # subscribe to this channels
    for chnl in message["channels"]:
        if not sputnik.hasChannel(chnl):
            sputnik.createChannel(chnl)

        sputnik.addClientToChannel(chnl, request.sputnikID)

    # set our username
    if request.user and request.user.username.strip() != '' and request.sputnikID and request.sputnikID.find(' ') == -1:
        sputnik.set("ses:%s:username" % request.sputnikID, request.user.username)

    # set our last access
    if request.sputnikID and request.sputnikID.strip() != '' and request.sputnikID and request.sputnikID.find(' ') == -1:
        sputnik.set("ses:%s:last_access" % request.sputnikID, time.time())

    return ret
