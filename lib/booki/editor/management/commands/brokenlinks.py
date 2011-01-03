from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import os.path
import urllib2

from booki.editor import models
from lxml import etree, html

from django.test import Client


class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"

def checkLink(chapter, urlLink):
    if urlLink.startswith("http://"):
        print '   >>> ', urlLink,

        try:
            response = urllib2.urlopen(HeadRequest(urlLink))
        except IOError, e:
            if hasattr(e, 'reason'):
                print '   [%s]' % e.reason
            elif hasattr(e, 'code'):
                print '  [%s]' % e.code
        else:
            print '   [%s]' % response.code
    else:
        c = Client()
        newUrl = os.path.normpath('/%s/_v/%s/%s/%s' % (chapter.version.book.url_title, chapter.version.getVersion(), chapter.url_title, urlLink))

        print '    >> ', newUrl,
        response = c.get(newUrl)

        print '   [%s]' % response.status_code


class Command(BaseCommand):
    def handle(self, *args, **options):

        for chapter in models.Chapter.objects.all():
            print '[%s]' % chapter.url_title,

            try:
                tree = html.document_fromstring(chapter.content)
                print ''
            except:
                print '   [ERROR]'
                continue

            for elem in tree.iter():
                src = elem.get('src')
                if src:
                    checkLink(chapter, src)

                href = elem.get('href')
                if href:
                    checkLink(chapter, href)

            #chapter.content =  etree.tostring(tree, encoding='UTF-8', method='html')
            #chapter.save()
