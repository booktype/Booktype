#!/usr/bin/python
#

import os, sys
import re
from booki import xhtml_utils

from pprint import pformat

TEST_TEXT = """<h1>Cropping an Image
</h1>
<p><strong>Software name : </strong>GIMP
  <br /><strong>Software version :</strong> 2.2
</p>
<p>Sometimes you might have an image <b style="bad">that<b> needs a little bit 'cut off' or <blink>trimming</blink>. 
</p>
<p>So, lets assume you have an image open in front of you &amp;c. Mine looks like this:
</p>
<p><img title="start" alt="start" src="/floss/pub/Gimp/cropping/start.png" height="398" width="492" />
  <br />
</p>
<h2 onclick="somesuch()">Decide on your crop area&nbsp;

</h2>
<script>//do nasty
</script>
"""


def _get_chapter():
    chapter = 'Chapter'
    book = 'Book'
    server = 'Example.com'
    c = xhtml_utils.EpubChapter(server, book, chapter)
    c.text = TEST_TEXT    
    return c


def parse_test():
    c = _get_chapter()
    c.load_tree()
    images = c.localise_links()                
    c.remove_bad_tags()
    print c.as_xhtml()

if __name__ == '__main__':
    parse_test()

