#!/usr/bin/python

import re, random, os, sys

WORDS = 'burmese-animal-names.txt'

MAIN_SCRIPTS = ('fr.js', 'my.js')
#  /var/www/floss/pub/TWiki/TWikiJavascripts/xinha/lang/fr.js

PLUGIN_BASE = "/var/www/floss/pub/TWiki/TWikiJavascripts/xinha/plugins/"
#PLUGIN_BASE = "/home/douglas/src/xinha/plugins/"


PRINT_LINKS = '--print-links' in sys.argv

def word_lister():
    f = open(WORDS)
    words = [ line.strip() for line in f if line.strip() ]
    f.close()
    while True:
        random.shuffle(words)        
        for x in words:
            yield x

new_word = word_lister().next


def fake_localise(template, target):
    reading = open(template)
    writing = open(target, 'w')

    item_re = re.compile(r'^\s*("[^"]+")\s*:\s*("[^"]*")\s*(,?)')
    comment_re = re.compile(r'(?<=\W)(fr)(?=\W)')

    for line in reading:
        m = item_re.match(line)
        if m:
            k, v, comma = m.groups()
            writing.write('%s: "%s"%s\n' % (k, new_word(), comma))
        else:
            writing.write(comment_re.sub("my", line))

    writing.close()
    reading.close()
    

if __name__ == '__main__':    

    fake_localise(*MAIN_SCRIPTS)
    for d in os.listdir(PLUGIN_BASE):
        f = os.path.join(PLUGIN_BASE, d, 'lang/fr.js')
        if os.path.exists(f):
            target = '%s-my.js' % d
            fake_localise(f, target)
            if PRINT_LINKS:
                print "sudo ln -s %s %s" % (os.path.abspath(target), f[:-5] + 'my.js')
            else:
                print >> sys.stderr, "Converting  %s to %s" % (f, target)
            
            
    
