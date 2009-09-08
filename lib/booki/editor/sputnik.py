import redis, time
import simplejson

# must fix this rcon issue somehow. 
# this is stupid but will work for now

rcon = redis.Redis()

def hasChannel(channelName):
    global rcon

    return rcon.sismember("sputnik:channels", channelName)

def createChannel(channelName):
    global rcon

    if not hasChannel(channelName):
        rcon.sadd("sputnik:channels", channelName)

    return True

def removeChannel(channelName):
    global rcon

    return rcon.srem("sputnik:channels", channelName)

def addClientToChannel(channelName, client):
    global rcon

    rcon.sadd("ses:%s:channels" % client, channelName)

    rcon.sadd("sputnik:channel:%s" % channelName, client)

def removeClientFromChannel(channelName, client):
    global rcon

    return rcon.srem("sputnik:channel:%s" % channelName, client)

def addMessageToChannel(request, channelName, message, myself = False ):
    global rcon

    clnts = rcon.smembers("sputnik:channel:%s" % channelName)

    message["channel"] = channelName
    message["clientID"] = request.clientID

    for c in clnts:
        if not myself and c == request.sputnikID:
            continue

        rcon.push( "ses:%s:messages" % c, simplejson.dumps(message), tail = True)

def removeClient(clientName):
    global rcon

    for chnl in rcon.smembers("ses:%s:channels" % clientName):
        removeClientFromChannel(chnl, clientName)
        rcon.srem("ses:%s:channels" % clientName, chnl)

    rcon.delete("ses:%s:last_access" % clientName)

    # TODO
    # also, i should delete all messages


## treba viditi shto opcenito sa onim

def booki_main(request, message):
    global rcon

    ret = {}
    if message["command"] == "ping":
        addMessageToChannel(request, "/booki/", {})

    if message["command"] == "disconnect":
        pass

    if message["command"] == "connect":
#        r = redis.Redis()

        if not rcon.exists("sputnik:client_id"):
            rcon.set("sputnik:client_id", 0)

        clientID = rcon.incr("sputnik:client_id")
        ret["clientID"] = clientID
        request.sputnikID = "%s:%s" % (request.session.session_key, clientID)

        # subscribe to this channels
        for chnl in message["channels"]:
            if not hasChannel(chnl):
                createChannel(chnl)

            addClientToChannel(chnl, request.sputnikID)

        # set our last access
        rcon.set("ses:%s:last_access" % request.sputnikID, time.time())

    return ret



def booki_chat(request, message, projectid, bookid):
    if message["command"] == "message_send":
        addMessageToChannel(request, "/chat/%s/%s/" % (projectid, bookid), {"command": "message_received", "from": request.user.username, "message": message["message"]})
        return {}

    return {}

# remove all the copy+paste code


# getChapters

def getTOCForBook(book):
    from booki.editor import models

    results = []

    for chap in list(models.BookToc.objects.filter(book=book).order_by("weight")):
        if chap.chapter:
            results.append((chap.chapter.id, chap.chapter.title, chap.chapter.url_title, chap.typeof))
        else:
            results.append((chap.chapter.id, chap.name, chap.name, chap.typeof))

    return results


# booki_book

def booki_book(request, message, projectid, bookid):
    from booki.editor import models

    if message["command"] == "init_editor":
        project = models.Project.objects.get(id=projectid)
        book = models.Book.objects.get(project=project, id=bookid)

        chapters = getTOCForBook(book)

        def vidi(a):
            if a == request.sputnikID:
                return "<b>%s</b>" % a
            return a

        users = [vidi(m) for m in list(rcon.smembers("sputnik:channel:%s" % message["channel"]))]
        
        addMessageToChannel(request, "/chat/%s/%s/" % (projectid, bookid), {"command": "user_joined", "user_joined": request.user.username}, myself = False)
                
        return {"chapters": chapters, "users": users}

    if message["command"] == "chapter_status":
        addMessageToChannel(request, "/booki/book/%s/%s/" % (projectid, bookid), {"command": "chapter_status", "chapterID": message["chapterID"], "status": message["status"], "username": request.user.username})
        return {}

    if message["command"] == "chapter_save":
        chapter = models.Chapter.objects.get(id=int(message["chapterID"]))
        chapter.content = message["content"];
        chapter.save()

        addMessageToChannel(request, "/booki/book/%s/%s/" % (projectid, bookid), {"command": "chapter_status", "chapterID": message["chapterID"], "status": "normal", "username": request.user.username})

        return {}

    if message["command"] == "chapter_rename":
        addMessageToChannel(request, "/booki/book/%s/%s/" % (projectid, bookid), {"command": "chapter_status", "chapterID": message["chapterID"], "status": "rename", "username": request.user.username})
 
        return {}

    if message["command"] == "chapters_changed":
        lst = [chap[5:] for chap in message["chapters"]]

        project = models.Project.objects.get(id=projectid)
        book = models.Book.objects.get(project=project, id=bookid)

        weight = len(lst)

        for chap in lst:
            m =  models.BookToc.objects.get(chapter__id__exact=int(chap))
            m.weight = weight
            m.save()

            weight -= 1

        results = []

        for chap in list(models.BookToc.objects.filter(book=book).order_by("weight")):
            if chap.chapter:
                results.append((chap.chapter.id, chap.chapter.title, chap.chapter.url_title, chap.typeof))
            else:
                results.append((chap.chapter.id, chap.name, chap.name, chap.typeof))

        addMessageToChannel(request, "/booki/book/%s/%s/" % (projectid, bookid), {"command": "chapters_changed", "chapters": results})
        return {}

    if message["command"] == "get_users":
        res = {}
        def vidi(a):
            if a == request.sputnikID:
                return "!%s!" % a
            return a

        res["users"] = [vidi(m) for m in list(rcon.smembers("sputnik:channel:%s" % message["channel"]))]
        return res 

    if message["command"] == "get_chapter":
        res = {}

        chapter = models.Chapter.objects.get(id=int(message["chapterID"]))
        res["title"] = chapter.title
        res["content"] = chapter.content 

        addMessageToChannel(request, "/booki/book/%s/%s/" % (projectid, bookid), {"command": "chapter_status", "chapterID": message["chapterID"], "status": "edit", "username": request.user.username})

        return res

    if message["command"] == "create_chapter":
        from booki.editor import models

        import datetime
        project = models.Project.objects.get(id=projectid)
        book = models.Book.objects.get(project=project, id=bookid)

        from django.template.defaultfilters import slugify

        url_title = slugify(message["chapter"])


        s = models.ProjectStatus.objects.all()[0]
        chapter = models.Chapter(book = book,
                                 url_title = url_title,
                                 title = message["chapter"],
                                 status = s,
                                 created = datetime.datetime.now(),
                                 modified = datetime.datetime.now())
        chapter.save()

        c = models.BookToc(book = book,
                           name = message["chapter"],
                           chapter = chapter,
                           weight = 0,
                           typeof=1)
        c.save()

        chapters = list(models.Chapter.objects.filter(book=book))

        results = []

        for chap in list(models.BookToc.objects.filter(book=book).order_by("weight")):
            if chap.chapter:
                results.append((chap.chapter.id, chap.chapter.title, chap.chapter.url_title, chap.typeof))
            else:
                results.append((chap.chapter.id, chap.name, chap.name, chap.typeof))

        addMessageToChannel(request, "/booki/book/%s/%s/" % (projectid, bookid), {"command": "chapters_list", "chapters": results}, myself = True)

        return {}

    if message["command"] == "get_chapters":
        project = models.Project.objects.get(id=projectid)
        book = models.Book.objects.get(project=project, id=bookid)

        results = getTOCForBook(book)
        
        return {"chapters": results}

    return {}

