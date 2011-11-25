from django.db import transaction

from django.conf import settings

try:
    STATUS_URL = settings.STATUS_URL
except AttributeError:
    STATUS_URL = 'http://status.flossmanuals.net/'


def remote_get_status_messages(request, message, profileid):
    import feedparser

    d = feedparser.parse('%s%s/rss' % (STATUS_URL, profileid))

#    messages = [(x['title'], ) for x in d['entries']]
    messages = [(x['content'][0]['value'], ) for x in d['entries']]

    return {"list": messages}

def remote_group_create(request, message, profileid):
    from booki.editor.models import BookiGroup
    from booki.utils.misc import bookiSlugify
    import datetime

    groupName = message.get("groupName", "")
    groupDescription = message.get("groupDescription", "")

    try:
        group = BookiGroup(name = groupName,
                           url_name = bookiSlugify(groupName),
                           description = groupDescription,
                           owner = request.user,
                           
                           created = datetime.datetime.now())
        group.save()

        group.members.add(request.user)
    except:
        transaction.rollback()
        return {"created": False}
    else:
        transaction.commit()

    return {"created": True}


def remote_init_profile(request, message, profileid):
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


def remote_mood_set(request, message, profileid):
    # should check permissions
    from django.utils.html import strip_tags

    ## maximum size is 30 characters only
    ## html tags are removed
    moodMessage = strip_tags(message.get("value",""))[:30]

    import booki.account.signals
    booki.account.signals.account_status_changed.send(sender = request.user, message = message.get('value', ''))

    # save new permissions
    profile = request.user.get_profile()
    profile.mood = moodMessage

    try:
        profile.save()
    except:
        transaction.rollback()
    else:
        transaction.commit()

        ## propagate to other users
        ## probably should only send it to /booki/ channel
        
        import sputnik

        for chnl in sputnik.smembers("sputnik:channels"):
            if sputnik.sismember("sputnik:channel:%s:users" % message['channel'], request.user.username):
                sputnik.addMessageToChannel(request, chnl, {"command": "user_status_changed", 
                                                            "from": request.user.username, 
                                                            "message": moodMessage}, 
                                            myself=True)
            
    return {}
