import time
import re
import decimal
import sputnik


def remote_ping(request, message):
    sputnik.addMessageToChannel(request, "/booki/", {})

    _now = time.time()

    for key in sputnik.rcon.keys("booki:*:locks:*"):
        lastAccess = sputnik.rcon.get(key)

        if decimal.Decimal("%f" % _now) - lastAccess > 30:
            sputnik.rcon.delete(key)

            m = re.match("booki:(\d+):locks:(\d+):(\w+)", key)
            
            if m:
                sputnik.addMessageToChannel(request, "/booki/book/%s/" % m.group(1), {"command": "chapter_status", 
                                                                                      "chapterID": m.group(2), 
                                                                                      "status": "normal", 
                                                                                      "username": m.group(3)})
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
    
