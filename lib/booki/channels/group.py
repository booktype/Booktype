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
