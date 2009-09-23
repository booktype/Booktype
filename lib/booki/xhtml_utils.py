"""Various things to do with [x]html that might be useful in more than
one place."""

import lxml, lxml.html, lxml.etree
import os, sys
import re

from urlparse import urlparse, urlsplit, urljoin
from urllib2 import urlopen, HTTPError

CHAPTER_TEMPLATE = '''<html>
<head>
<title>%(title)s</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
%(text)s
</body>
</html>
'''

#IMG_DIR = '/tmp/images/'
IMG_DIR = '/home/douglas/fm-data/import-tests/staging/'

def log(*messages, **kwargs):
    for m in messages:
        try:
            print >> sys.stderr, m
        except Exception:
            print >> sys.stderr, repr(m)


class Author(object):
    def __init__(self, name, email):
        self.name = name
        self.email = email


_fetched = {}

def _read_local_url(path):
    f = open(IMG_DIR + path)
    s = f.read()
    f.close()
    return s

def _save_local_url(path, data):
    f = open(IMG_DIR + path, 'w')
    f.write(data)
    f.close()
    #os.chmod(path, 0444)

#XXX there is something a bit dodgy about this.
#Two urls could map to the same filename.  (though that is unlikely).
#
#XXX use existing images as cache.

def fetch_if_necessary(url, target):
    log(url, target)
    if url in _fetched:
        if _fetched[url] == target:
            return target
        log('Not trying to fetch "%s" -> "%s" because stored as "%s"' %(url, target, _fetched[url]))
        return url
    try:
        f = urlopen(url)
        data = f.read()
        f.close()
    except HTTPError, e:
        #if it is missing, assume it will be missing every time after.
        _fetched[url] = None
        log(e)
        return url
    _save_local_url(target, data)
    _fetched[url] = target
    return target




class BaseChapter(object):
    image_cache = ImageCache()

    def as_html(self):
        """Serialise the tree as html if possible, otherwise wrap the
        original text."""
        if hasattr(self, 'tree'):
            return lxml.etree.tostring(self.tree, method='html')

        return CHAPTER_TEMPLATE % {
            'title': '%s: %s' % (self.book, self.name),
            'text': self.text
        }

    def as_xhtml(self):
        """Convert to xhtml and serialise."""
        try:
            root = self.tree.getroot()
        except AttributeError:
            root = self.tree

        nsmap = {None: XHTML}
        xroot = lxml.etree.Element(XHTMLNS + "html", nsmap=nsmap)

        def descend(el, xel):
            xel.text = el.text
            for k, v in el.items():
                xel.set(k, v)
            for child in el.iterchildren():
                xchild = xel.makeelement(XHTMLNS + child.tag)
                xel.append(xchild)
                descend(child, xchild)
            xel.tail = el.tail

        #xroot.text = root.text
        #xroot.tail = root.tail

        descend(root, xroot)

        return lxml.etree.tostring(xroot)


    def load_tree(self, force=False):
        if not hasattr(self, 'tree') or force:
            html = self.as_html()
            self.tree = lxml.html.document_fromstring(html)
            #from lxml.html import html5parser
            #self.tree = html5parser.fromstring(html)

    def as_text(self):
        """Get the twiki-style guts of the chapter, either from the
        modified tree, or from the original text attribute."""
        if not hasattr(self, 'tree'):
            return self.text
        text = lxml.etree.tostring(self.tree.find('body'), method='xml')
        text = re.sub(r'^\s*<body.*?>\s*', '', text)
        text = re.sub(r'\s*</body>\s*$', '', text)
        return text

    def localise_links(self):
        images = []
        def localise(oldlink):
            fragments = urlsplit(oldlink)
            if '.' not in fragments.path:
                log('ignoring %s' % oldlink)
                return oldlink
            base, ext = fragments.path.rsplit('.', 1)
            if (not fragments.scheme.startswith('http') or
                fragments.netloc != self.server or
                ext not in ('png', 'gif', 'jpg', 'jpeg', 'svg', 'css', 'js') or
                '/pub/' not in base
                ):
                log('ignoring %s' % oldlink)
                return oldlink

            server = fragments.netloc.split('.', 1)[0]
            base = base.split('/pub/', 1)[1] #remove /floss/pub/ or /pub/
            target = ''.join(x for x in server + base if x.isalnum())
            target = '%s.%s' % (target, ext)
            newlink = self.image_cache.fetch_if_necessary(oldlink, target)
            if newlink and newlink != oldlink:
                log('got %s as %s' % (oldlink, newlink))
                images.append(newlink)
            return newlink

        self.load_tree()
        self.tree.rewrite_links(localise, base_href=('http://%s/bin/view/%s/%s' % (self.server, self.book, self.name)))
        text = lxml.etree.tostring(self.tree.find('body'), method='xml')
        self.text = self.as_text()
        return images

    cleaner = lxml.html.clean.Cleaner(scripts=True,
                                      javascript=True,
                                      comments=False,
                                      style=True,
                                      links=True,
                                      meta=True,
                                      page_structure=False,
                                      processing_instructions=True,
                                      embedded=True,
                                      frames=True,
                                      forms=True,
                                      annoying_tags=True,
                                      #allow_tags=OK_TAGS,
                                      remove_unknown_tags=True,
                                      safe_attrs_only=True,
                                      add_nofollow=False
                                      )

    def remove_bad_tags(self):
        log(self.as_html())
        for e in self.tree.iter():
            if not e.tag in OK_TAGS:
                log('found bad tag %s' % e.tag)
        self.cleaner(self.tree)


class ImportedChapter(BaseChapter):
    def __init__(self, lang, book, chapter_name, text, author, email, date, server=None):
        self.lang = lang
        self.book = book
        self.name = chapter_name
        self.text = text
        self.author = Author(author, email)
        self.date = date
        if server is None:
            server = '%s.flossmanuals.net' % lang
        self.server = server



CHAPTER_URL = "http://%s/bin/view/%s/%s?skin=text"

class EpubChapter(BaseChapter):
    def __init__(self, server, book, chapter_name, url=None, cache_dir=None):
        self.server = server
        self.book = book
        self.name = chapter_name
        self.url = url or CHAPTER_URL % (server, book, chapter_name)
        if cache_dir:
            self.image_cache = ImageCache(cache_dir)

    def fetch(self):
        """Fetch content as found at self.url"""

        f = urlopen(self.url)
        self.text = f.read()
        f.close()


