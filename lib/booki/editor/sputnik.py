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

    for chap in list(models.BookToc.objects.filter(book=book).order_by("-weight")):
        # is it a section or chapter
        if chap.chapter:
            results.append((chap.chapter.id, chap.chapter.title, chap.chapter.url_title, chap.typeof))
        else:
            results.append(('s%s' % chap.id, chap.name, chap.name, chap.typeof))

    return results


# booki_book


def getHoldChapters(book_id):
    from django.db import connection, transaction
    cursor = connection.cursor()
    # wgere chapter_id is NULL that is the hold Chapter
    cursor.execute("select editor_chapter.id, editor_chapter.title, editor_chapter.url_title, editor_booktoc.chapter_id from editor_chapter left outer join editor_booktoc on (editor_chapter.id=editor_booktoc.chapter_id)  where editor_chapter.book_id=%s;", (book_id, ))

    chapters = []
    for row in cursor.fetchall():
        if row[-1] == None:
            chapters.append((row[0], row[1], row[2], 1))

    return chapters


def booki_book(request, message, projectid, bookid):
    from booki.editor import models

    if message["command"] == "init_editor":
        project = models.Project.objects.get(id=projectid)
        book = models.Book.objects.get(project=project, id=bookid)

        chapters = getTOCForBook(book)
        holdChapters =  getHoldChapters(bookid)

        ## chapters who are on hold

        def vidi(a):
            if a == request.sputnikID:
                return "<b>%s</b>" % a
            return a


        users = [vidi(m) for m in list(rcon.smembers("sputnik:channel:%s" % message["channel"]))]
        
        addMessageToChannel(request, "/chat/%s/%s/" % (projectid, bookid), {"command": "user_joined", "user_joined": request.user.username}, myself = False)
                
        return {"chapters": chapters, "hold": holdChapters, "users": users}

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
        chapter = models.Chapter.objects.get(id=int(message["chapterID"]))
        chapter.title = message["chapter"];
        chapter.save()

        addMessageToChannel(request, "/booki/book/%s/%s/" % (projectid, bookid), {"command": "chapter_status", "chapterID": message["chapterID"], "status": "normal", "username": request.user.username})

        addMessageToChannel(request, "/booki/book/%s/%s/" % (projectid, bookid), {"command": "chapter_rename", "chapterID": message["chapterID"], "chapter": message["chapter"]})
 
        return {}

    if message["command"] == "chapters_changed":
        lst = [chap[5:] for chap in message["chapters"]]
        lstHold = [chap[5:] for chap in message["hold"]]

        project = models.Project.objects.get(id=projectid)
        book = models.Book.objects.get(project=project, id=bookid)

        weight = len(lst)

        for chap in lst:
            if chap[0] == 's':
                m =  models.BookToc.objects.get(id__exact=int(chap[1:]))
                m.weight = weight
                m.save()
            else:
                try:
                    m =  models.BookToc.objects.get(chapter__id__exact=int(chap))
                    m.weight = weight
                    m.save()
                except:
                    chptr = models.Chapter.objects.get(id__exact=int(chap))
                    m = models.BookToc(book = book,
                                       name = "SOMETHING",
                                       chapter = chptr,
                                       weight = weight,
                                       typeof=1)
                    m.save()

            weight -= 1

        if message["kind"] == "remove":
            if type(message["chapter_id"]) == type(' ') and message["chapter_id"][0] == 's':
                m =  models.BookToc.objects.get(id__exact=message["chapter_id"][1:])
                m.delete()
            else:
                m =  models.BookToc.objects.get(chapter__id__exact=int(message["chapter_id"]))
                m.delete()


        addMessageToChannel(request, "/booki/book/%s/%s/" % (projectid, bookid), {"command": "chapters_changed", "ids": lst, "hold_ids": lstHold, "kind": message["kind"], "chapter_id": message["chapter_id"]})
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

        result = (c.chapter.id, c.chapter.title, c.chapter.url_title, c.typeof)

        addMessageToChannel(request, "/booki/book/%s/%s/" % (projectid, bookid), {"command": "chapter_create", "chapter": result}, myself = True)

        return {}

    if message["command"] == "create_section":
        from booki.editor import models

        import datetime
        project = models.Project.objects.get(id=projectid)
        book = models.Book.objects.get(project=project, id=bookid)

        c = models.BookToc(book = book,
                           name = message["chapter"],
                           chapter = None,
                           weight = 0,
                           typeof=0)
        c.save()

        result = ("s%s" % c.id, c.name, None, c.typeof)

        addMessageToChannel(request, "/booki/book/%s/%s/" % (projectid, bookid), {"command": "chapter_create", "chapter": result, "typeof": c.typeof}, myself = True)

        return {}


    return {}

