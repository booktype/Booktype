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

def remote_ping(request, message):
    """
    Sends ping to the server. Just so we know client is still alive. It also removes old locks. This is not the place to do it at all, 
    but once we have normal scheduled calls, will put it there.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    """

    import sputnik

    sputnik.addMessageToChannel(request, "/booki/", {})

    _now = time.time()

    try:
        locks = sputnik.rkeys("booki:*:locks:*") 
    except:
        return

    for key in locks:
        
        lastAccess = sputnik.get(key)

        if type(lastAccess) in [type(' '), type(u' ')]:
            try:
                lastAccess = decimal.Decimal(lastAccess)
            except:
                continue

        if lastAccess and decimal.Decimal("%f" % _now) - lastAccess > 30:
            sputnik.rdelete(key)

            m = re.match("booki:(\d+):locks:(\d+):(\w+)", key)
            
            if m:
                sputnik.addMessageToChannel(request, "/booki/book/%s/" % m.group(1), {"command": "chapter_status", 
                                                                                      "chapterID": m.group(2), 
                                                                                      "status": "normal", 
                                                                                      "username": m.group(3)},
                                            myself = True)
# FIXME not implemented
def remote_disconnect(request, message):
    pass

def remote_subscribe(request, message):
    """
    Subscribes client to specific channels.

    Input:
     - chanels

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
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

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @rtype: C{string}
    @return: Returns unique Client ID for this connection
    """

    import sputnik

    ret = {}

    # does this work ?
    try:
        clientID = sputnik.incr("sputnik:client_id")
    except:
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
    
