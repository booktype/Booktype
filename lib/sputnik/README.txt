
Sputnik
=======

Sputnik is a Django application for two-way Ajax communication with
Web clients. This enables pushing data from the server to the clients
in response to events. In the current implementation, the clients poll
for messages from a Redis database, but long polling and WebSockets
support are in the plans.

Purpose
-------

Sputnik is meant for Django applications that need real-time two-way
communication such as notifications, presence, data updates, or collaborative
editing.

Normally, Web applications cannot push data to the browser. The
solution is to implement some server push (sometimes known as "Comet")
approach for Django.

Concepts
--------

* Server - the Sputnik application within a Django project
* Client - a document in a browser (reload makes a new client)
* Message - unit of data transmitted (JSON with uid, channel, command)
* Channel - clients receive all messages from their subscribed channels

* Command - a message that includes command name (or "message type")
* User - a logged-in user in the Django project

* Channel name - a string
* Command name - a string
* User name - a Django user name
* Client ID - a unique number that identifies the client
* UID - a unique number used by client to match replies to requests
* Sputnik ID - "%s:%s" % (request.session.session_key, clientID)

Design
------

In Sputnik, data is sent as JSON messages on the named message channels.
The clients subscribe to some channels to start receiving the messages
on those channels. The server sends messages to the channels.

The clients don't send messages directly to the channels. Instead,
they send commands to the server, and the commands can result in
messages sent to the channels.

API
---

* JavaScript
  * $.booki.subscribeToChannel(channelName, callback)
  * $.booki.connect();
  * $.booki.sendToChannel(channelName, message, callback, errback)
  * $.booki.sendToCurrentBook(message, callback, errback) - sends to a 
    book-version-specific channel
* Python
  * sputnik.addMessageToChannel(request, channelName, message, myself=False)
    * request used for request.sputnikID and request.clientID
  * Additional: user lists, locks, time since last command from client

Implementation
--------------

The data about current users, clients, channels and unfetched messages
is held in a Redis in-memory NoSQL key-value database process.

Clients poll for any unfetched messages to them via the Django app.

The Django applications on the server can add new messages to the
channels in Redis. Commands received from the client go to the
Sputnik dispatcher that routes them to the correct view based on the
channel and command names. 

Future tasks
------------

* Compare to other Comet APIs.
* Make the division clear between Booktype and Sputnik.
* Think about usage guidelines:
  * When to post a form, post an Ajax request, post a Sputnik command?
  * When to render in Django, render in JavaScript?
    * Need to render in multiple locales at a time in Django?
  * How to bind data with least plumbing code?
* Can the design be simplified?
* Implement long polling, WebSockets etc.
