
Booki Messaging
---------------

Booki Messaging is a Django application for providing
microblogging-like messaging functions. It provides template tags for
including message entry forms, message display timelines and "follow"
buttons in the user interface of a web site. Messages can include file
attachments and users can receive email notifications about new
messages to them.

Copyright
---------

Copyright 2012 Seravo Oy <tuukka@seravo.fi>

License
-------

Booktype is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Booktype is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Booktype.  If not, see <http://www.gnu.org/licenses/>.

For more details, please see the file LICENSE.txt.

Installation
------------

1. Ensure the following settings are defined in the settings.py file
of your Django project (values are examples):

DEFAULT_NOTIFICATION_FILTER='#* ~*'
EMAIL_HOST_USER = 'booki-messaging@example.com'
BOOKI_URL='http://example.com/my_booki'
DATA_URL='%s/data' % BOOKI_URL

2. Add booki.messaging to the INSTALLED_APPS
setting in the settings.py file of your Django project.

3. Add the following entry to the URLconf of your Django project file
urls.py:

(r'^messaging/', include('booki.messaging.urls'))
 
Template tags
-------------

All UI is implemented as Django template tags in a module called
messaging_tags:

user_timeline username
group_timeline groupname
book_timeline bookname
tag_timeline tagname
user_followbutton username requestuser
book_followbutton bookname requestuser
tag_followbutton tagname requestuser
user_messagefield username
group_messagefield groupname
book_messagefield bookname
messagefield_button
user_followersbox username
user_followingbox username
user_tagbox username

Templates
---------

The template tags instantiate templates that can be customised
as wanted:

timeline.html: the *_timeline tags
user_followbutton.html: user_followbutton
book_followbutton.html: book_followbutton
tag_followbutton.html: tag_followbutton
messagefield.html: the *_messagefield tags
messagefield_button.html: messagefield_button
followersbox.html: user_followersbox
followingbox.html: user_followingbox
tags.html: user_tagbox

Additional templates:

view_tag.html: content of the view_tag page
new_message_email.txt: content of the notification email
