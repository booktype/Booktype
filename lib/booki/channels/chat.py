def remote_message_send(request, message, bookid):        
    addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_received", "from": request.user.username, "message": message["message"]})
    return {}
