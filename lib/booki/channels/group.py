from django.db import transaction

from booki.editor import models
from booki.utils import security

def remote_init_group(request, message, groupid):
    import sputnik

    ## get online users
    try:
        _onlineUsers = sputnik.smembers("sputnik:channel:%s:users" % message["channel"])
    except:
        _onlineUsers = []

    if request.user.username not in _onlineUsers:
        try:
            sputnik.sadd("sputnik:channel:%s:users" % message["channel"], request.user.username)
        except:
            pass

    return {}

def remote_leave_group(request, message, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    group.members.remove(request.user)
    transaction.commit()

    return {"result": True}

def remote_join_group(request, message, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    group.members.add(request.user)
    transaction.commit()

    return {"result": True}
