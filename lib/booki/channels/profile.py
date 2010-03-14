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

    # save new permissions
    profile = request.user.get_profile()
    profile.mood = moodMessage
    profile.save()

    ## propagate to other users
    ## probably should only send it to /booki/ channel

    import sputnik

    for chnl in sputnik.smembers("sputnik:channels"):
        if sputnik.sismember("sputnik:channel:%s:users" % chnl, request.user.username):
            sputnik.addMessageToChannel(request, chnl, {"command": "user_status_changed", 
                                                        "from": request.user.username, 
                                                        "message": moodMessage}, 
                                        myself=True)
            
    return {}
