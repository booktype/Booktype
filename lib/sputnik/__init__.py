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


"""
What is Sputnik?
================
  Sputnik is Django app for handling AJAX calls from Web client. For now, it only does polling, but the idea is to make it also work with WebSockets.

  Sputnik is named after U{Soviet space program<http://en.wikipedia.org/wiki/Sputnik_program>}.

Sputnik keys
============
  - sputnik:channels - Redis Set of channel names.
  - sputnik:channel:<channel_name>:channel - Redis Set of clients for specific <channel_name>.
  - sputnik:channel:<channel_name>:users - Redis Set of usernames for specific <channel_name>.

  - ses:<client_id>:channels - Redis Set of channel names for specific <client_id>.
  - ses:<client_id>:username - Username for specific <client_id>.
  - ses:<client_id>:messages - Redis List of Sputnik messages for specific <client_id>.
  - ses:<client_id>:last_access - Timestamp of client last access.

Sputnik message
===============
  Sputnik message is nothing else then Python dictionary. It B{MUST} provide default keys I{uid}, I{channel} and I{command}. 
  Everything else is optional.
    

@todo: Remove obsolete code after changing redis client version. Redis did not support keys with spaces, so we had to encode keys.
@todo: Should read info about redis database from settings.
"""

from __future__ import with_statement 

import time
from booki.utils.json_wrapper import simplejson
import redis
import base64

from django.conf import settings

try:
    REDIS_HOST = settings.REDIS_HOST
    REDIS_PORT = settings.REDIS_PORT
    REDIS_DB = settings.REDIS_DB
    REDIS_PASSWORD = settings.REDIS_PASSWORD
except AttributeError:
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = None

rcon = redis.Redis(host = REDIS_HOST,
                   port = REDIS_PORT,
                   db = REDIS_DB,
                   password = REDIS_PASSWORD)
#rcon.connect()


# Implement our own methods for redis communication. This had to be done before because previous versions of redis had problems
# with spaces in keys and etc....


def rencode(key):
    return key

def rdecode(key):
    return key

def sismember(key, value):
    import sputnik

    if key and key.strip() != '':
        with sputnik.rcon.lock('com'):
            result = sputnik.rcon.sismember(key, rencode(value))
        return result

    return False

def sadd(key, value):
    import sputnik

    if key and key.strip() != '':
        with sputnik.rcon.lock('com'):
            sputnik.rcon.sadd(key, rencode(value))

    return False

def rset(key, value):
    import sputnik

    if key and key.strip() != '':
        with sputnik.rcon.lock('com'):
            sputnik.rcon.set(key, rencode(value))

    return False

def rpop(key):
    import sputnik

    if key and key.strip() != '':
        with sputnik.rcon.lock('com'):
            result = rdecode(sputnik.rcon.rpop(key))
        return result

    return None

def srem(key, value):
    import sputnik

    if key and key.strip() != '':
        with sputnik.rcon.lock('com'):
            result = sputnik.rcon.srem(key, rencode(value))

        return result

    return None

def incr(key):
    import sputnik

    if key and key.strip() != '':
        with sputnik.rcon.lock('con'):
            result = sputnik.rcon.incr(key)
        return result


def get(key):
    import sputnik

    if key and key.strip() != '':
        with sputnik.rcon.lock('con'):
            result = rdecode(sputnik.rcon.get(key))
        return result

def set(key, value):
    import sputnik

    if key and key.strip() != '':
        with sputnik.rcon.lock('con'):
            result = rdecode(sputnik.rcon.set(key, value))
        return result


def smembers(key):
    import sputnik

    result = []

    if key and key.strip() != '':
        try:
            with sputnik.rcon.lock('com'):
                result =  [rdecode(el) for el in list(sputnik.rcon.smembers(key))]
        except:
            from booki.utils.log import printStack
            printStack(None)
            return []

    return result


def rkeys(key):
    import sputnik

    if key and key.strip() != '':
        with sputnik.rcon.lock('con'):
            result = [rdecode(el) for el in list(sputnik.rcon.keys(key))]

        return result

    return []

def push(key, value):
    import sputnik

    if key and key.strip() != '':
        with sputnik.rcon.lock('con'):
            result = sputnik.rcon.rpush(key, rencode(value))

        return result

    return None

def rdelete(key):
    import sputnik

    if key and key.strip() != '':
        with sputnik.rcon.lock('con'):
            sputnik.rcon.delete(key)

 
# must fix this rcon issue somehow. 
# this is stupid but will work for now

def hasChannel(channelName):
    """
    Check if Sputnik channel exists.

    @type channelName: C{string}
    @param channelName: Channel name.
    @rtype: C{bool}
    @return: Returns True if channel exists.
    """

    return sismember("sputnik:channels", channelName)

def createChannel(channelName):
    """
    Create Sputnik channel.

    @type channelName: C{string}
    @param channelName: Channel name.
    @rtype: C{bool}
    @return: Always return True.
    """

    if not hasChannel(channelName):
        sadd("sputnik:channels", channelName)

    return True

def removeChannel(channelName):
    """
    Remove Sputnik channel.

    @type channelName: C{string}
    @param channelName: Channel name.
    @rtype: C{bool}
    @return: Return True if channel was removed or False if it was not.
    """

    return srem("sputnik:channels", channelName)

def addClientToChannel(channelName, client):
    """
    Add client to channel.

    @type channelName: C{string}
    @param channelName: Channel name.
    @type client: C{string}
    @param client: Unique Client ID.
    """

    sadd("ses:%s:channels" % client, channelName)
    sadd("sputnik:channel:%s:channel" % channelName, client)

def removeClientFromChannel(request, channelName, client):
    """
    Remove client from channel.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request.
    @type channelName: C{string}
    @param channelName: Channel name.
    @type client: C{string}
    @param client: Unique Client ID.
    """
    
    import sputnik
    srem("sputnik:channel:%s:channel" % channelName, client)

    # get our username
    userName = sputnik.get("ses:%s:username" % client)

    # get all usernames
    users = smembers("sputnik:channel:%s:users" % channelName)

    try:
        # get all clients
        allClients = []
        for cl in smembers("sputnik:channel:%s:channel" % channelName):
            allClients.append(sputnik.get("ses:%s:username" % cl))

        for usr in users:
            if usr not in allClients:
                sputnik.srem("sputnik:channel:%s:users" % channelName, usr)
                addMessageToChannel(request, channelName, {"command": "user_remove", "username": usr}, myself = True)
    except:
        from booki.utils.log import printStack
        printStack(None)


def addMessageToChannel(request, channelName, message, myself = False ):
    """
    Add message to specific channel.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request.
    @type channelName: C{string}
    @param channelName: Channel name.
    @type message: C{dict}
    @param message: Sputnik message.
    @type myself: C{bool}
    @keyword myself: Should client also recieve that message.
    """

    import sputnik

    # TODO
    # not iterable
    try:
        clnts = sputnik.smembers("sputnik:channel:%s:channel" % channelName)
    except:
        from booki.utils.log import printStack
        printStack(None)
        return

    message["channel"] = channelName
    message["clientID"] = request.clientID

    for c in clnts:
        if not myself and c == request.sputnikID:
            continue

        if c.strip() != '':
            try:
                sputnik.push( "ses:%s:messages" % c, simplejson.dumps(message))
            except:
                pass
                

def removeClient(request, clientName):
    """
    Remove client from Sputnik.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request.
    @type clientName: C{string}
    @param clientName: Unique Client ID.

    @todo: Should remove all tracks of user existence on the system.
    """

    import sputnik

    for chnl in sputnik.smembers("ses:%s:channels" % clientName):
        removeClientFromChannel(request, chnl, clientName)
        srem("ses:%s:channels" % clientName, chnl)

    sputnik.rdelete("ses:%s:username" % clientName)
    sputnik.rdelete("ses:%s:last_access" % clientName)

    # TODO
    # also, i should delete all messages
