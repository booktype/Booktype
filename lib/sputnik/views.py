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

    n = 0

    while True:
        v = None

        try:
            if clientID and clientID.find(' ') == -1:
                v = sputnik.rpop("ses:%s:%s:messages" % (request.session.session_key, clientID))
        except:
            if n > 20:
                break

            import logging
            logging.getLogger("booki").debug("Sputnik - Coult not get the latest message from the queue session: %s clientID:%s" %(request.session.session_key, clientID))

        n += 1

        if not v: break
        try:
            results.append(simplejson.loads(v))
        except:
            import logging
            logging.getLogger("booki").debug(v)


    import time, decimal
    try:
        if request.sputnikID and request.sputnikID.find(' ') == -1:
            sputnik.rcon.set("ses:%s:last_access" % request.sputnikID, time.time())
    except:
        import logging
        logging.getLogger("booki").debug("Sputnik - CAN NOT SET TIMESTAMP.")

    # this should not be here!
    # timeout old edit locks

    locks = {}

    _now = time.time() 
    try:
        for k in sputnik.rcon.keys("ses:*:last_access"):
            tm = sputnik.rcon.get(k)

            if type(tm) in [type(' '), type(u' ')]:
                try:
                    tm = decimal.Decimal(tm)
                except:
                    continue

        # timeout after 2 minute
            if  tm and decimal.Decimal("%f" % _now) - tm > 60*2:
                sputnik.removeClient(request, k[4:-12])
    except:
        import logging
        logging.getLogger("booki").debug("Sputnik - can not get all the last accesses")

    ret = {"result": True, "messages": results}

    return HttpResponse(simplejson.dumps(ret), mimetype="text/json")

