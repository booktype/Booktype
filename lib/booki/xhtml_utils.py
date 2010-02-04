"""Various things to do with [x]html that might be useful in more than
one place."""

import lxml, lxml.html, lxml.html.clean
from lxml import etree

import os, sys
import re, copy
from cStringIO import StringIO

from urlparse import urlparse, urlsplit, urljoin
from urllib2 import urlopen, HTTPError

ADJUST_HEADING_WEIGHT = False

OK_TAGS = set([
    "body", "head", "html", "title", "abbr", "acronym", "address",
    "blockquote", "br", "cite", "code", "dfn", "div", "em", "h1", "h2",
    "h3", "h4", "h5", "h6", "kbd", "p", "pre", "q", "samp", "span",
    "strong", "var", "a", "dl", "dt", "dd", "ol", "ul", "li", "object",
    "param", "b", "big", "hr", "i", "small", "sub", "sup", "tt", "del",
    "ins", "bdo", "caption", "col", "colgroup", "table", "tbody", "td",
    "tfoot", "th", "thead", "tr", "img", "area", "map", "meta", "style",
    "link", "base",
    etree.Comment,
    ])

XHTMLNS = '{http://www.w3.org/1999/xhtml}'
XHTML = 'http://www.w3.org/1999/xhtml'

XHTML11_DOCTYPE = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
'''
XML_DEC = '<?xml version="1.0" encoding="UTF-8"?>\n'

IMG_CACHE = 'cache/images/'
IMG_PREFIX = 'static/'

def log(*messages, **kwargs):
    for m in messages:
        try:
            print >> sys.stderr, m
        except Exception:
            print >> sys.stderr, repr(m)


def url_to_filename(url, prefix=''):
    #XXX slightly inefficient to do urlsplit so many times, but versatile
    fragments = urlsplit(url)
    base, ext = fragments.path.rsplit('.', 1)
    server = fragments.netloc.split('.', 1)[0] #en, fr, translate
    base = base.split('/pub/', 1)[1] #remove /floss/pub/ or /pub/
    base = re.sub(r'[^\w]+', '-',  '%s-%s' %(base, server))
    return '%s%s.%s' % (prefix, base, ext)

def convert_tags(root, elmap):
    for el in root.iterdescendants():
        if el.tag in elmap:
            el.tag = elmap[el.tag]


class ImageCache(object):
    def __init__(self, cache_dir=IMG_CACHE, prefix=IMG_PREFIX):
        self._fetched = {}
        self.cache_dir = cache_dir
        self.prefix = prefix
        if not os.path.exists(cache_dir + prefix):
            os.makedirs(cache_dir + prefix)

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

    def fetch_if_necessary(self, url, target=None, use_cache=True):
        if url in self._fetched:
            return self._fetched[url]

        if target is None:
            target = url_to_filename(url, self.prefix)

        if use_cache and os.path.exists(self.cache_dir + target):
            log("used cache for %s" % target)
            return target

        try:
            f = urlopen(url)
            data = f.read()
            f.close()
        except HTTPError, e:
            # if it is missing, assume it will be missing every time
            # after, otherwise, you can get into endless waiting
            self._fetched[url] = None
            log("Wanting '%s', got error %s" %(url, e))
            return None

        self._save_local_url(target, data)
        self._fetched[url] = target
        log("got %s as %s" % (url, target))
        return target


class BaseChapter(object):
    parser = lxml.html.HTMLParser(encoding='utf-8')
    def as_html(self):
        """Serialise the tree as html."""
        return etree.tostring(self.tree, method='html', encoding='utf-8')

    def as_xhtml(self):
        """Convert to xhtml and serialise."""
        try:
            root = self.tree.getroot()
        except AttributeError:
            root = self.tree

        nsmap = {None: XHTML}
        xroot = etree.Element(XHTMLNS + "html", nsmap=nsmap)

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

        return XML_DEC + XHTML11_DOCTYPE + etree.tostring(xroot)

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
        #for e in self.tree.iter():
        #    if not e.tag in OK_TAGS:
        #        log('found bad tag %s' % e.tag)
        self.cleaner(self.tree)

    def _loadtree(self, html):
        try:
            try:
                self.tree = lxml.html.document_fromstring(html, parser=self.parser)
            except UnicodeError, e:
                log('failed to parse tree as unicode, got %s %r' % (e, e),
                    'trying again using default parser')
                self.tree = lxml.html.document_fromstring(html)
        except etree.XMLSyntaxError, e:
            log('Could not parse html file %r, string %r... exception %s' %
                (self.name, html[:40], e))
            self.tree = lxml.html.document_fromstring('<html><body></body></html>').getroottree()


class EpubChapter(BaseChapter):
    def __init__(self, server, book, chapter_name, html, use_cache=False,
                 cache_dir=None):
        self.server = server
        self.book = book
        self.name = chapter_name
        self._loadtree(html)

    def prepare_for_epub(self):
        """Shift all headings down 2 places."""
        if ADJUST_HEADING_WEIGHT:
            # a question to resolve:
            # is it better (quicker) to have multiple, filtered iterations
            # converting in order (h4->h5, h3->h4, etc) or to do a single,
            # unfiltered pass and convert from a dict?

            hmap = dict(('h%s' % x, 'h%s' % (x + 2)) for x in range(4, 0, -1))
            hmap['h5'] = 'h6'
            convert_tags(self.root, hmap)



class TWikiChapter(BaseChapter):
    image_cache = ImageCache()

    def __init__(self, server, book, chapter_name, html, use_cache=False,
                 cache_dir=None):
        self.server = server
        self.book = book
        self.name = chapter_name
        self.use_cache = use_cache
        if cache_dir:
            self.image_cache = ImageCache(cache_dir)
        self._loadtree(html)

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
            ext = ext.lower()
            if (not fragments.scheme.startswith('http') or
                fragments.netloc != self.server or
                ext not in ('png', 'gif', 'jpg', 'jpeg', 'svg', 'css', 'js') or
                '/pub/' not in base
                ):
                log('ignoring %s' % oldlink)
                return oldlink

            newlink = self.image_cache.fetch_if_necessary(oldlink, use_cache=self.use_cache)
            if newlink is not None:
                images.append(newlink)
                return newlink
            log("can't do anything for %s -- why?" % (oldlink,))
            return oldlink

        self.tree.rewrite_links(localise, base_href=('http://%s/bin/view/%s/%s' %
                                                     (self.server, self.book, self.name)))
        return images


#XXX almost certainly broken and out of date!
class Author(object):
    def __init__(self, name, email):
        self.name = name
        self.email = email

class ImportedChapter(TWikiChapter):
    """Used for git import"""
    def __init__(self, lang, book, chapter_name, text, author, email, date, server=None,
                 use_cache=False, cache_dir=None):
        self.lang = lang
        self.book = book
        self.name = chapter_name
        self.author = Author(author, email)
        self.date = date
        if server is None:
            server = '%s.flossmanuals.net' % lang
        self.server = server
        self.use_cache = use_cache
        if cache_dir:
            self.image_cache = ImageCache(cache_dir)
        #XXX is text html-wrapped?
        self._loadtree(html)

    def as_twikitext(self):
        """Get the twiki-style guts of the chapter from the tree"""
        text = etree.tostring(self.tree.find('body'), method='html')
        text = re.sub(r'^.*?<body.*?>\s*', '', text)
        text = re.sub(r'\s*</body>.*$', '\n', text)
        return text






