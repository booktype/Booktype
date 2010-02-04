import time
import simplejson
import redis
import base64

rcon = redis.Redis()
rcon.connect()


# implement our own methods for redis communication

def rencode(key):
    return base64.b64encode(key)

def rdecode(key):
    return base64.b64decode(key)

def sismember(key, value):
    import sputnik

    if key and key.strip() != '':
        return sputnik.rcon.sismember(key, rencode(value))

    return False

def sadd(key, value):
    import sputnik

    if key and key.strip() != '':
        sputnik.rcon.sadd(key, rencode(value))

    return False

def rset(key, value):
    import sputnik

    if key and key.strip() != '':
        sputnik.rcon.set(key, rencode(value))

    return False

def rpop(key):
    import sputnik

    if key and key.strip() != '':
        return rdecode(sputnik.rcon.pop(key))

    return None

def srem(key, value):
    import sputnik

    if key and key.strip() != '':
        return sputnik.rcon.srem(key, rencode(value))

    return None

def get(key):
    import sputnik

    if key and key.strip() != '':
        return rdecode(sputnik.rcon.get(key))

def smembers(key):
    import sputnik

    if key and key.strip() != '':
        try:
            return [rdecode(el) for el in list(sputnik.rcon.smembers(key))]
        except:
            return []

    return []

def rkeys(key):
    import sputnik

    if key and key.strip() != '':
        return [rdecode(el) for el in list(sputnik.rcon.keys(key))]

    return []

def push(key, value):
    import sputnik

    if key and key.strip() != '':
        return sputnik.rcon.push(key, rencode(value))

    return None

def rdelete(key):
    import sputnik

    if key and key.strip() != '':
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
    userName = sputnik.rcon.get("ses:%s:username" % client)

    # get all usernames
    users = smembers("sputnik:channel:%s:users" % channelName)

    try:
        # get all clients
        allClients = []
        for cl in smembers("sputnik:channel:%s:channel" % channelName):
            allClients.append(sputnik.rcon.get("ses:%s:username" % cl))

        for usr in users:
            if usr not in allClients:
                sputnik.rcon.srem("sputnik:channel:%s:users" % channelName, usr)
                addMessageToChannel(request, channelName, {"command": "user_remove", "username": usr}, myself = True)
    except:
        pass


def addMessageToChannel(request, channelName, message, myself = False ):
    import sputnik
    # TODO
    # not iterable
    try:
        clnts = smembers("sputnik:channel:%s:channel" % channelName)
    except:
        return

    message["channel"] = channelName
    message["clientID"] = request.clientID

    for c in clnts:
        if not myself and c == request.sputnikID:
            continue

        if c.strip() != '':
            try:
                push( "ses:%s:messages" % c, simplejson.dumps(message))
            except:
                pass
                

def removeClient(request, clientName):
    import sputnik
    for chnl in smembers("ses:%s:channels" % clientName):
        removeClientFromChannel(request, chnl, clientName)
        srem("ses:%s:channels" % clientName, chnl)

    sputnik.rcon.delete("ses:%s:username" % clientName)
    sputnik.rcon.delete("ses:%s:last_access" % clientName)

    # TODO
    # also, i should delete all messages
