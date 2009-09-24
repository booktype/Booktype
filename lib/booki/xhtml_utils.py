"""Various things to do with [x]html that might be useful in more than
one place."""

import lxml, lxml.html, lxml.etree, lxml.html.clean

import os, sys
import re
from cStringIO import StringIO

from urlparse import urlparse, urlsplit, urljoin
from urllib2 import urlopen, HTTPError

MEDIATYPES = {
    'html': "text/html",
    'xhtml': "application/xhtml+xml",
    'css': 'text/css',
    'json': "application/json",

    'png': 'image/png',
    'gif': 'image/gif',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'svg': 'image/svg+xml',

    'ncx': 'application/x-dtbncx+xml',
    'dtb': 'application/x-dtbook+xml',
    'xml': 'application/xml',

    'pdf': "application/pdf",
    'txt': 'text/plain',

    'epub': "application/epub+zip",
    'booki': "application/booki+zip",

    None: 'application/octet-stream',
}

OK_TAGS = set([
    "body", "head", "html", "title", "abbr", "acronym", "address",
    "blockquote", "br", "cite", "code", "dfn", "div", "em", "h1", "h2",
    "h3", "h4", "h5", "h6", "kbd", "p", "pre", "q", "samp", "span",
    "strong", "var", "a", "dl", "dt", "dd", "ol", "ul", "li", "object",
    "param", "b", "big", "hr", "i", "small", "sub", "sup", "tt", "del",
    "ins", "bdo", "caption", "col", "colgroup", "table", "tbody", "td",
    "tfoot", "th", "thead", "tr", "img", "area", "map", "meta", "style",
    "link", "base"
    ])

XHTMLNS = '{http://www.w3.org/1999/xhtml}'
XHTML = 'http://www.w3.org/1999/xhtml'

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

XHTML11_DOCTYPE = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
'''
XML_DEC = '<?xml version="1.0" encoding="UTF-8"?>\n'

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


class ImageCache(object):
    def __init__(self, cache_dir=IMG_DIR):
        self._fetched = {}
        self.cache_dir = cache_dir

    def read_local_url(self, path):
        f = open(self.cache_dir + path)
        s = f.read()
        f.close()
        return s

    def _save_local_url(self, path, data):
        f = open(self.cache_dir + path, 'w')
        f.write(data)
        f.close()
        #os.chmod(path, 0444)

    #XXX there is something a bit dodgy about this.
    #Two urls could map to the same filename.  (though that is unlikely).
    #
    #XXX use existing images as cache.

    def fetch_if_necessary(self, url, target):
        #log(url, target)
        if url in self._fetched:
            if self._fetched[url] == target:
                return target
            log('Not trying to fetch "%s" -> "%s" because stored as "%s"' %(url, target, self._fetched[url]))
            return url
        try:
            f = urlopen(url)
            data = f.read()
            f.close()
        except HTTPError, e:
            #if it is missing, assume it will be missing every time after.
            self._fetched[url] = None
            log(e)
            return url
        self._save_local_url(target, data)
        self._fetched[url] = target
        return target


class BaseChapter(object):
    image_cache = ImageCache()

    def load_tree(self, text=None, html=None):
        if html is None:
            html = CHAPTER_TEMPLATE % {
                'title': '%s: %s' % (self.book, self.name),
                'text': text
                }
        self.tree = lxml.html.document_fromstring(html)

    def as_html(self):
        """Serialise the tree as html."""
        return lxml.etree.tostring(self.tree, method='html')

    def as_twikitext(self):
        """Get the twiki-style guts of the chapter from the tree"""
        text = lxml.etree.tostring(self.tree.find('body'), method='html')
        text = re.sub(r'^.*?<body.*?>\s*', '', text)
        text = re.sub(r'\s*</body>.*$', '\n', text)
        return text

    def as_xhtml(self):
        """Convert to xhtml and serialise."""
        try:
            root = self.tree.getroot()
        except AttributeError:
            root = self.tree

        nsmap = {None: XHTML}
        xroot = lxml.etree.Element(XHTMLNS + "html", nsmap=nsmap)

        def xhtml_copy(el, xel):
            xel.text = el.text
            for k, v in el.items():
                xel.set(k, v)
            for child in el.iterchildren():
                xchild = xel.makeelement(XHTMLNS + child.tag)
                xel.append(xchild)
                xhtml_copy(child, xchild)
            xel.tail = el.tail

        xhtml_copy(root, xroot)

        return XML_DEC + XHTML11_DOCTYPE + lxml.etree.tostring(xroot)

    def localise_links(self):
        """Find image links, convert them to local links, and fetch
        the images from the net so the local links work"""
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

        self.tree.rewrite_links(localise, base_href=('http://%s/bin/view/%s/%s' % (self.server, self.book, self.name)))
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
                                      allow_tags=OK_TAGS,
                                      remove_unknown_tags=False,
                                      safe_attrs_only=True,
                                      add_nofollow=False
                                      )

    def remove_bad_tags(self):
        for e in self.tree.iter():
            if not e.tag in OK_TAGS:
                log('found bad tag %s' % e.tag)
        self.cleaner(self.tree)


class ImportedChapter(BaseChapter):
    def __init__(self, lang, book, chapter_name, text, author, email, date, server=None):
        self.lang = lang
        self.book = book
        self.name = chapter_name
        self.author = Author(author, email)
        self.date = date
        if server is None:
            server = '%s.flossmanuals.net' % lang
        self.server = server
        self.load_tree(text)


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
        text = f.read()
        f.close()
        self.load_tree(text)

