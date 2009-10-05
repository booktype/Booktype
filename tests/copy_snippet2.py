import os, sys
import re
from booki import xhtml_utils

from pprint import pformat

from lxml import etree, html
from lxml.builder import E


#doc = html.parse('copy_snippet.html')
MARKER_CLASS="espri-marker"



def copy_element(src, create):
    #print src, create
    dest = create(src.tag)
    for k, v in src.items():
        dest.set(k, v)
    dest.tail = src.tail
    return dest

def test_split():
    doc = html.parse('copy_snippet.html')
    root = doc.getroot()

    chapters = {}
    def climb(src, dest):
        #print src
        for child in src.iterchildren():
            if child.tag == 'hr' and child.get('class') == MARKER_CLASS:
                ID = child.get('id')
                if ID.startswith('espri-chapter-'):
                    new = copy_element(src, src.makeelement)
                    root = new
                    for a in src.iterancestors():
                        a2 = copy_element(a, root.makeelement)
                        a2.append(root)
                        root = a2

                    chapters[ID[14:]] = root

                    if dest is not None:
                        # should write here?
                        dest.tail = None
                        for a in dest.iterancestors():
                            a.tail = None

                    dest = new
                    continue
                else:
                    print "skipping %s" % etree.tostring(child)

            elif dest is not None:
                new = copy_element(child, dest.makeelement)
                new.text = child.text
                dest.append(new)
                climb(child, new)
            else:
                #print etree.tostring(child)
                climb(child, None)

    climb(root, None)

    print chapters

    for id, tree in chapters.items():
        string = etree.tostring(tree)
        f = open('/tmp/x%s.html' % id, 'w')
        f.write(string)
        f.close()



test_split()

