import time
import sputnik


def remote_ping(request, message):
    sputnik.addMessageToChannel(request, "/booki/", {})

def remote_disconnect(request, message):
    pass

def remote_connect(request, message):
    ret = {}

    # this is where we have problems when we get timeout
    def _getID():
        if not sputnik.rcon.exists("sputnik:client_id"):
            sputnik.rcon.set("sputnik:client_id", 0)
            
    try:
        _getID()
    except:
        sputnik.rcon.connect()
        _getID()

    clientID = sputnik.rcon.incr("sputnik:client_id")
    ret["clientID"] = clientID
    request.sputnikID = "%s:%s" % (request.session.session_key, clientID)

    # subscribe to this channels
    for chnl in message["channels"]:
        if not sputnik.hasChannel(chnl):
            sputnik.createChannel(chnl)

    sputnik.addClientToChannel(chnl, request.sputnikID)

    # set our username
    sputnik.rcon.set("ses:%s:username" % request.sputnikID, request.user.username)

    # set our last access
    sputnik.rcon.set("ses:%s:last_access" % request.sputnikID, time.time())

    return ret
    
