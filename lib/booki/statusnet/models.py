from django.db import models

import booki.editor.signals
import booki.account.signals

# Create your models here.

def event_account_created(sender, **kwargs):
    ""Register user on status.net website"""

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
                'password': kwargs.get('password', 'password'),
                'confirm':  kwargs.get('password', 'password'),
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



booki.account.signals.account_created.connect(event_account_created)





