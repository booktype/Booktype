def remote_message_send(request, message, bookid):        
    """
    Called when user is sending message to chat channel L{bookid}.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    """
    
    import sputnik

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_received", "from": request.user.username, "message": message["message"]})
    return {}
