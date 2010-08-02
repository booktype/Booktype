from __future__ import with_statement 

import time
import simplejson
import redis
import base64



# should read info from settings about connections
rcon = redis.Redis()
#rcon.connect()


# implement our own methods for redis communication

def rencode(key):
    return key
    return base64.b64encode(key)

def rdecode(key):
    return key
    return base64.b64decode(key)

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
    return sismember("sputnik:channels", channelName)

def createChannel(channelName):
    if not hasChannel(channelName):
        sadd("sputnik:channels", channelName)

    return True

def removeChannel(channelName):
    return srem("sputnik:channels", channelName)

def addClientToChannel(channelName, client):
    sadd("ses:%s:channels" % client, channelName)
    sadd("sputnik:channel:%s:channel" % channelName, client)

def removeClientFromChannel(request, channelName, client):
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
    import sputnik

    for chnl in sputnik.smembers("ses:%s:channels" % clientName):
        removeClientFromChannel(request, chnl, clientName)
        srem("ses:%s:channels" % clientName, chnl)

    sputnik.rdelete("ses:%s:username" % clientName)
    sputnik.rdelete("ses:%s:last_access" % clientName)

    # TODO
    # also, i should delete all messages
