def remote_message_send(request, message, bookid):        
    import sputnik

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_received", "from": request.user.username, "message": message["message"]})
    return {}
