from django.db import models

import booki.editor.signals
import booki.account.signals

import urllib2
import urllib

from django.conf import settings

try:
    STATUS_URL = settings.STATUS_URL
except AttributeError:
    STATUS_URL = 'http://status.flossmanuals.net/'




def createStatusAccount(username, password, email, firstname):
    import urllib, urllib2

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor() )
    page = opener.open("%smain/register" % STATUS_URL)
    
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
        args = {'nickname': username,
                'password': password,
                'confirm': password,
                'email':    email,
                'fullname': firstname,
                'homepage': 'http://www.booki.cc/',
                'bio': ' ',
                'location': 'Croatia',
                'license':  'true',
                'rememberme': 'true',
                'submit':  'Register',
                'token':   tokenValue
                }

        data = urllib.urlencode(args)

        f = opener.open('%smain/register' % STATUS_URL, data)
        data =  f.read()
        f.close()


def searchMessages(query):
    import urllib, urllib2, simplejson

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor() )
    page = opener.open("%sapi/search.json?q=%s" % (STATUS_URL, query))

    pageData = page.read()
    page.close()

    data = simplejson.loads(pageData)

    return data


def sendMessage(user, password, message):
    # this is hard coded for now. should 
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm = 'flossmanuals API',
                              uri = STATUS_URL,
                              user = user,
                              passwd = password)
    opener = urllib2.build_opener(auth_handler)
    
    urllib2.install_opener(opener)
    
    data = {"status": message}
    urllib2.urlopen('%sapi/statuses/update.xml' % STATUS_URL, urllib.urlencode(data))



def event_account_created(sender, **kwargs):
    """Register user on status.net website"""

    try:
        createStatusAccount(sender.username, 'bookibooki', sender.email, sender.first_name)
    except:
        pass


def event_chapter_modified(sender, **kwargs):
    #sendMessage('a', 'a', 'Saved new changes to chapter "%s". %s/%s/%s/' % (kwargs['chapter'].title, settings.BOOKI_URL, sender.book.url_title, kwargs['chapter'].url_title))


def event_book_created(sender, **kwargs):
    try:
        sendMessage(sender.username, 'bookibooki', 'I just created a new book "%s"! #%s' % (kwargs['book'].title, kwargs['book'].url_title))
    except:
        pass


def event_account_status_changed(sender, **kwargs):
    try:
        sendMessage(sender.username, 'bookibooki', kwargs['message'])
    except: # 
        pass
    

booki.account.signals.account_created.connect(event_account_created)
booki.account.signals.account_status_changed.connect(event_account_status_changed)

#booki.editor.signals.chapter_modified.connect(event_chapter_modified)
booki.editor.signals.book_created.connect(event_book_created)





