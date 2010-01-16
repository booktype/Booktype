import time
import simplejson
import sputnik

# must fix this rcon issue somehow. 
# this is stupid but will work for now

def hasChannel(channelName):
    return sputnik.rcon.sismember("sputnik:channels", channelName)

def createChannel(channelName):
    if not hasChannel(channelName):
        sputnik.rcon.sadd("sputnik:channels", channelName)

    return True

def removeChannel(channelName):
    return sputnik.rcon.srem("sputnik:channels", channelName)

def addClientToChannel(channelName, client):
    sputnik.rcon.sadd("ses:%s:channels" % client, channelName)

    sputnik.rcon.sadd("sputnik:channel:%s:channel" % channelName, client)

def removeClientFromChannel(request, channelName, client):
    sputnik.rcon.srem("sputnik:channel:%s:channel" % channelName, client)

    # get our username
    userName = sputnik.rcon.get("ses:%s:username" % client)

    # get all usernames
    users = sputnik.rcon.smembers("sputnik:channel:%s:users" % channelName)

    # get all clients
    allClients = []
    for cl in sputnik.rcon.smembers("sputnik:channel:%s:channel" % channelName):
        allClients.append(sputnik.rcon.get("ses:%s:username" % cl))

    for usr in users:
        if usr not in allClients:
            sputnik.rcon.srem("sputnik:channel:%s:users" % channelName, usr)
            addMessageToChannel(request, channelName, {"command": "user_remove", "username": usr}, myself = True)


def addMessageToChannel(request, channelName, message, myself = False ):
    clnts = sputnik.rcon.smembers("sputnik:channel:%s:channel" % channelName)

    message["channel"] = channelName
    message["clientID"] = request.clientID

    for c in clnts:
        if not myself and c == request.sputnikID:
            continue

        rcon.push( "ses:%s:messages" % c, simplejson.dumps(message), tail = True)

def removeClient(request, clientName):
    for chnl in sputnik.rcon.smembers("ses:%s:channels" % clientName):
        removeClientFromChannel(request, chnl, clientName)
        sputnik.rcon.srem("ses:%s:channels" % clientName, chnl)

    sputnik.rcon.delete("ses:%s:username" % clientName)
    sputnik.rcon.delete("ses:%s:last_access" % clientName)

    # TODO
    # also, i should delete all messages
