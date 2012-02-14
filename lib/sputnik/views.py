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

from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseRedirect

from booki.utils.json_wrapper import simplejson
import re
import redis
import sputnik

@transaction.commit_manually
def dispatcher(request, **sputnik_dict):
    """
    Main Sputnik dispatcher. Every Sputnik request goes through this dispatcher. 

    Input arguments are passed through C{request.POST}:
      - C{request.POST['messages']} 
          List of messages client is sending to server.
      - C{request.POST['clientID']} 
          Unique client ID for this connection.

    This is just another Django view.

    @todo: Change logging and error handling.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type sputnik_dict: C{dict}
    @param sputnik_dict: Mapping of channels with specific python modules.
    @rtype: C{HttpResponse}
    @return: Return C{django.http.HttpResponse} object.
    """

    try:
        inp =  request.POST
    except IOError:
        return HttpResponse(simplejson.dumps({"result": False, "messages": []}), mimetype="text/json")

    results = []

    clientID = None
    messages = simplejson.loads(inp.get("messages", "[]"))

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

#            from booki.utils.log import printStack
#            printStack(None)


        n += 1

        if not v: break
        try:
            results.append(simplejson.loads(v))
        except:

            import logging
            logging.getLogger("booki").debug(v)

#            from booki.utils.log import printStack
#            printStack(None)


    import time, decimal
    try:
        if request.sputnikID and request.sputnikID.find(' ') == -1:
            sputnik.set("ses:%s:last_access" % request.sputnikID, time.time())
    except:

        import logging
        logging.getLogger("booki").debug("Sputnik - CAN NOT SET TIMESTAMP.")

#        from booki.utils.log import printStack
#        printStack(None)


    # this should not be here!
    # timeout old edit locks

    locks = {}

    _now = time.time() 
    try:
        for k in sputnik.rkeys("ses:*:last_access"):
            tm = sputnik.get(k)

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

#        from booki.utils.log import printStack
#        printStack(None)


    ret = {"result": True, "messages": results}

    try:
        return HttpResponse(simplejson.dumps(ret), mimetype="text/json")
    except:
        transaction.rollback()
    finally:
        transaction.commit()

