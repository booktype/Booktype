import os, sys
import re
from booki import xhtml_utils

from pprint import pformat

from lxml import etree, html
from lxml.builder import E


#doc = html.parse('copy_snippet.html')
MARKER_CLASS="espri-marker"

def test_copy():
    doc = html.parse('copy_snippet.html')
    elements = []
    for el in doc.iter('hr'):
        ID = el.get('id')
        if ID.startswith('espri-chapter-'):
            chapid = ID[14:]
            elements.append((el, chapid))

    print elements
    for s, e in zip(elements, elements[1:]):
        start_tag, sid = s
        end_tag, eid = e

        subdoc = xhtml_utils.xml_snippet(start_tag, end_tag)
        string = etree.tostring(subdoc)
        #print string
        f = open('/tmp/%s.html' % sid, 'w')
        f.write(string)
        f.close()



test_copy()

