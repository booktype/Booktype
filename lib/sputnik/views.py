from django.http import Http404, HttpResponse, HttpResponseRedirect

import simplejson
import re
import redis
import sputnik

def dispatcher(request, **sputnik_dict):
    inp =  request.POST

    results = []

    clientID = None
    messages = simplejson.loads(inp["messages"])

    if inp.has_key("clientID") and inp["clientID"]:
        clientID = inp["clientID"]

    for message in messages:
        ret = None
        for mpr in sputnik_dict['map']:
            mtch = re.match(mpr[0], message["channel"])

            if mtch:
                a =  mtch.groupdict()
                _m = __import__(mpr[1])

                for nam in mpr[1].split('.')[1:]:
                    _m = getattr(_m, nam)

                if _m:
                    # should do hasattr first and then getattr
                    fnc = getattr(_m, "remote_%s" % message['command'])

                    if not hasattr(request, "sputnikID"):
                        request.sputnikID = "%s:%s" % (request.session.session_key, clientID)
                        request.clientID  = clientID

                    if fnc:
                        ret = fnc(request, message, **a)
                        if not ret:
                            ret = {}

                        ret["uid"] = message.get("uid")
                        break
                    else:
                        import logging
                        logging.getLogger("booki").error("Could not find function '%s' for Sputnik channel '%d'!" % (message['command'], message['channel']))

        if ret:
            results.append(ret)
        else:
            import logging
            logging.getLogger("booki").error("Sputnik - %s." % simplejson.dumps(message))


    while True:
        v = sputnik.rcon.pop("ses:%s:%s:messages" % (request.session.session_key, clientID), tail = False)
        if not v: break

        results.append(simplejson.loads(v))


    import time, decimal
    try:
        sputnik.rcon.set("ses:%s:last_access" % request.sputnikID, time.time())
    except:
        pass

    # this should not be here!
    # timeout old edit locks

    locks = {}

    _now = time.time() 
    for k in sputnik.rcon.keys("ses:*:last_access"):
        tm = sputnik.rcon.get(k)

        # timeout after 2 minute
        if  decimal.Decimal("%f" % _now) - tm > 60*2:
            sputnik.removeClient(request, k[4:-12])

    ret = {"result": True, "messages": results}

    return HttpResponse(simplejson.dumps(ret), mimetype="text/json")

