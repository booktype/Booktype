import time
import re
import decimal

def remote_ping(request, message):
    import sputnik

    sputnik.addMessageToChannel(request, "/booki/", {})

    _now = time.time()

    try:
        locks = sputnik.rcon.keys("booki:*:locks:*") 
    except:
        return

    for key in locks:
        lastAccess = sputnik.rcon.get(key)

        if type(lastAccess) in [type(' '), type(u' ')]:
            try:
                lastAccess = decimal.Decimal(lastAccess)
            except:
                continue

        if lastAccess and decimal.Decimal("%f" % _now) - lastAccess > 30:
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
    import sputnik

    ret = {}

    # does this work ?
    try:
        clientID = sputnik.rcon.incr("sputnik:client_id")
    except:
        sputnik.rcon.connect()
        clientID = sputnik.rcon.incr("sputnik:client_id")
        
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
        sputnik.rcon.set("ses:%s:username" % request.sputnikID, request.user.username)

    # set our last access
    if request.sputnikID and request.sputnikID.strip() != '' and request.sputnikID and request.sputnikID.find(' ') == -1:
        sputnik.rcon.set("ses:%s:last_access" % request.sputnikID, time.time())

    return ret
    
