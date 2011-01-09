from django.db import models

import booki.editor.signals
import booki.account.signals

import urllib2
import urllib


def sendMessage(user, password, message):
    # this is hard coded for now. should 
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm='flossmanuals API',
                              uri='http://status.flossmanuals.net/',
                              user='adam',
                              passwd='bookibooki')
    opener = urllib2.build_opener(auth_handler)
    
    urllib2.install_opener(opener)
    
    data = {"status": message}
    urllib2.urlopen('http://status.flossmanuals.net/api/statuses/update.xml', urllib.urlencode(data))



def event_account_created(sender, **kwargs):
    """Register user on status.net website"""

    import urllib, urllib2

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor() )
    page = opener.open("http://status.flossmanuals.net/main/register")
    
    pageData = page.read()
    page.close()

    from lxml import html

    tokenValue = None

    try:
        tree = html.document_fromstring(pageData)
    except Exception as inst:
        return

    for elem in tree.iter():
        if elem.get('name') == 'token':
            tokenValue = elem.get('value')

    if tokenValue:
        args = {'nickname': sender.username,
                'password': 'bookibooki',
                'confirm': 'bookibooki',
 #               'password': kwargs.get('password', 'password'),
#                'confirm':  kwargs.get('password', 'password'),
                'email':    sender.email,
                'fullname': sender.first_name,
                'homepage': 'http://www.booki.cc/',
                'bio': ' ',
                'location': 'Croatia',
                'license':  'true',
                'rememberme': 'true',
                'submit':  'Register',
                'token':   tokenValue
                }

        data = urllib.urlencode(args)

        f = opener.open('http://status.flossmanuals.net/main/register', data)
        data =  f.read()
        print data
        f.close()


def event_chapter_modified(sender, **kwargs):
    from booki import settings

    sendMessage('a', 'a', 'Saved new changes to chapter "%s". %s/%s/%s/' % (kwargs['chapter'].title, settings.BOOKI_URL, sender.book.url_title, kwargs['chapter'].url_title))


booki.account.signals.account_created.connect(event_account_created)

booki.editor.signals.chapter_modified.connect(event_chapter_modified)




