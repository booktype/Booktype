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

import re
import logging
import json
import time
import decimal
import importlib

from django.db import transaction
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist, SuspiciousOperation, PermissionDenied


import sputnik
from . import utils

logger = logging.getLogger("sputnik")


def set_last_access(request):
    try:
        if request.sputnikID and request.sputnikID.find(' ') == -1:
            sputnik.set("ses:%s:last_access" % request.sputnikID, time.time())
    except:
        logger.error("Can not set timestamp.")


def remove_timeout_clients(request):
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
            if tm and decimal.Decimal("%f" % _now) - tm > 60 * 2:
                sputnik.removeClient(request, k[4:-12])
    except:
        logger.debug("Can not get all the last accesses")


def collect_messages(request, clientID):
    results = []
    n = 0

    while True:
        v = None

        try:
            if clientID and clientID.find(' ') == -1:
                v = sputnik.lpop("ses:%s:%s:messages" % (request.session.session_key, clientID))
        except:
            # Limit only to 20 messages
            if n > 20:
                break

            logger.error("Could not get the latest message from the queue session: %s clientID:%s" % (request.session.session_key, clientID))

        n += 1

        if not v:
            break

        try:
            results.append(json.loads(v))
        except:
            logger.error("Error while adding values to the result.")

    return results


@transaction.atomic
def dispatcher(request, **sputnik_dict):
    """
    Main Sputnik dispatcher. Every Sputnik request goes through this dispatcher.

    Input arguments are passed through *request.POST*:
      - *request.POST['messages']*: List of messages client is sending to server.
      - *request.POST['clientID']*: Unique client ID for this connection.

    This is just another Django view.

    .. todo::

      Change logging and error handling.


    :Args:
      - request (:class:`django.http.HttpRequest`): Client Request object
      - sputnik_dict (dict): Mapping of channels with specific python modules.

    :Returns:
      Return :class:`django.http.HttpResponse` instance.
    """

    status_code = True
    results = []
    clientID = None

    if request.method != 'POST':
        status_code = False

    try:
        messages = json.loads(request.POST.get("messages", "[]"))
    except ValueError:
        status_code = False
        logger.error("Error while trying to read input data. This does not seems to be JSON data.")
    except:
        status_code = False
        logger.error("Error while trying to read input data.")

    if status_code:
        clientID = request.POST.get("clientID", None)

        if not hasattr(request, "sputnikID"):
            request.sputnikID = "%s:%s" % (request.session.session_key, clientID)
            request.clientID = clientID

        for message in messages:
            found_match = False

            for mpr in sputnik_dict['map']:
                mtch = re.match(mpr[0], message.get("channel", ""))

                if mtch:
                    a = mtch.groupdict()
                    found_match = True
                    try:
                        _m = importlib.import_module(mpr[1])
                    except ImportError:
                        logger.error("Couldn't load module '{}'.".format(mpr[1]))
                        _m = None

                    if _m:
                        # should do hasattr first and then getattr
                        fnc = getattr(_m, "remote_%s" % message.get('command', ''))

                        if fnc:
                            execute_status = True
                            ret = None

                            # Catch different kind of errors
                            # For now they all do the same thing but this might change in the future
                            try:
                                ret = fnc(request, message, **a)
                            except ObjectDoesNotExist, e:
                                execute_status = False
                                logger.error("[{}] Object you are trying to find does not exist.".format("remote_{}".format(message.get('command', ''))))
                                logger.exception(e)
                            except SuspiciousOperation, e:
                                execute_status = False
                                logger.error("[{}] Suspicious operation.".format("remote_{}".format(message.get('command', ''))))
                                logger.exception(e)
                            except PermissionDenied, e:
                                execute_status = False
                                logger.error("[{}] Permission denied.".format("remote_{}".format(message.get('command', ''))))
                                logger.exception(e)
                            except Exception, e:
                                execute_status = False
                                logger.error("[{}] Unknown exception.".format("remote_{}".format(message.get('command', ''))))
                                logger.exception(e)

                            # For different compatibility reasons return result and status now
                            if not ret:
                                ret = {"result": execute_status}

                            # result and some other things might be a problem here
                            ret["status"] = execute_status
                            ret["uid"] = message.get("uid", None)

                            results.append(ret)

                        else:
                            logger.error("Could not find function '{}' for Sputnik channel '{}'!".format(message.get('command', ''), message.get('channel', '')))

            if not found_match:
                logger.error("I can not find match for your channel [{}].".format(message.get("channel", "")))

        # Collect other messages waiting for this user
        results.extend(collect_messages(request, clientID))

        # Set timestamp for this access
        set_last_access(request)

        # This will be moved to background workers
        remove_timeout_clients(request)

    # Besides status we are still using result
    return_objects = {"status": status_code, "result": status_code, "messages": results}

    # Always return HTTP status 200
    # In the future we should change this and return different kind of statuses in case of error

    return HttpResponse(utils.serializeJson(return_objects), content_type="text/json")
