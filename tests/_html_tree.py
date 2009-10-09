#!/usr/bin/python

import lxml, lxml.html, lxml.etree, lxml.html.clean

import os, sys
import re
from cStringIO import StringIO

HTML = """<html><head><title>A title</title><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head><body>
<h1>Optimising Images for the Web</h1>
<p>blah</p>
<p>There are a few questions you must first ask yourself.</p>
<h2>Is file size important?</h2>
</body></html>
"""

f = open('gimp-test.html')
HTML = f.read()
f.close()

XHTML = 'http://www.w3.org/1999/xhtml'

XHTMLNS = '{http://www.w3.org/1999/xhtml}'
nsmap = {None: XHTML}

tree = lxml.html.document_fromstring(HTML)
try:
    root = tree.getroot()
except AttributeError:
    root = tree

xroot = lxml.etree.Element(XHTMLNS + "html", nsmap=nsmap)

def xhtml_copy(el, xel):
    print el
    for k, v in el.items():
        xel.set(k, v)

    for child in el.iterchildren():
        xchild = xel.makeelement(XHTMLNS + child.tag)
        xel.append(xchild)
        xhtml_copy(child, xchild)

xhtml_copy(root, xroot)

