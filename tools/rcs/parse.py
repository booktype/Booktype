#!/usr/bin/python
'''Parse RCS files and return all the interesting commits.

Deliberately fragile.'''
# see `man rcsfile 5`
# and doc/RCSFILE in the CVS source tree

import os, sys, time

from rcs.core import Version, twiki_clean, ParseError

class RcsParseVersion(Version):
    """For data from rcs_parse module"""
    def __init__(self, name, d, contents):
        name = name[:-2]  #drop the ',v'
        revision = '.'.join(str(x) for x in d['rev'])
        author = d['author']
        Version.__init__(self, name, revision, d['date'], author)
        self.contents = contents

    def set_date(self, date):
        try:
            #stupid year format is sometimes 2 digit, sometimes 4 digit.
            t = time.strptime(date, "%Y.%m.%d.%H.%M.%S")
        except ValueError:
            t = time.strptime(date, "%y.%m.%d.%H.%M.%S")
        self.date = time.strftime("%s", t)
        


def parse_string(f, start=None):
    """Read an RCS string section, keeping it as a list of lines.  It
    begins and starts with '@', with '@'s in the middle escaped by
    doubling."""
    if start is None:
        start = f.next()
    if not start.startswith('@'):
        raise ParseError("start is %r : no @" % start)
    lines = []
    line = start[1:]
    while True:
        if '@' in line:
            # need to check that inline '@'s appear in doubles
            # eg douglas@@paradise.net.nz
            expecting = False
            for i, c in enumerate(line):
                if c == '@':
                    expecting = not expecting
                elif expecting:
                    # we wanted a second '@' but only got one. String ends here!
                    # This line is probably just '@\n', but might not be.
                    if i > 1:
                        lines.append(line[:i - 1])
                    if line[i:] != '\n':
                        print >> sys.stdout, "dodgily packed line %r (i: %s)" % (line, i)
                    break
            line = line.replace('@@', '@')
            if expecting:
                break
        lines.append(line)
        line = f.next()
    return lines


def parse_delta(f, line=None):
    ''' A typical delta looks like:
1.11
date	2008.09.16.08.16.08;	author AnneGentle;	state Exp;
branches;
next	1.10;
'''
    if line is None:
        line = f.next()

    data = {'rev': tuple(int(x) for x in line.split('.'))}
    while 'next' not in data:
        line = f.next().strip()
        bits = [x.split(None, 1) for x in line.split(';')]
        for b in bits:
            if len(b) == 2:
                data[b[0]] = b[1]
            elif b:
                data[b[0]] = None
    if data['next']:
        data['next'] = tuple(int(x) for x in data['next'].split('.'))
    return data


def parse_deltatext(f, line=None):
    ''' A typical commit looks like:
1.11
log
@none
@
text
@d1 1
a1 1
%META:TOPICINFO{author="AnneGentle" date="1221552967" format="1.1" version="1.11"}%
d19 1
a19 1
  <br /><img title="sdicon" alt="sdicon" src="/floss/pub/OLPC_simple/TuteBackingUp/.resized_400x52_sdicon.png" height="52" width="400" />
d26 1
a26 1
  <br /> <img title="sdcard" alt="sdcard" src="/floss/pub/OLPC_simple/TuteBackingUp/.resized_400x300_sdcard.png" height="300" width="400" /></li>
d46 1
a46 1
  <br /><img title="terminal_ls" alt="terminal_ls" src="/floss/pub/OLPC_simple/TuteBackingUp/.resized_400x200_terminal_ls.jpg" height="200" width="400" />
@
'''
    if line == None:
        line = f.next()
    rev_no = tuple(int(x) for x in line.split('.'))
    log = f.next()
    comment = parse_string(f)
    text = f.next()
    for got, wanted in ((log, 'log\n'), (text, 'text\n')):
        if got != wanted:
            print >> sys.stderr, "got %r, expected %r" % (got, wanted)

    #So now the rest of it is the string.
    text = parse_string(f)
    return {'rev': rev_no, 'text': text, 'comment': comment}


def parse_intro(f):
    """Get the head, then skip the rest of the intro"""
    line = f.next()
    hrev = line.split(None)[1].rstrip(';')
    head = tuple(int(x) for x in hrev.split('.'))

    bits = []
    while True:
        line = f.next().strip()
        if not line:
            break
    return head

def parse_desc(f, line=None):
    '''Typical desc section:
desc
@none
@
'''
    if line is None:
        line = f.next()
    if line.strip() != 'desc':
        raise ParseError("Trying to parse desc, wanted 'desc', got '%s" %line.strip())
    text = parse_string(f)
    #if text != ['none\n']:
    #    print >> sys.stderr, "got unexpected desc text of:\n%s" % text
    return {'desc': text}



def apply_delta(lines, delta):
    """Change document lines in place, using the RCS style diff in
    delta.

    delta format:

    <'a' or 'd'><line number> <line count>

    example:
d1 1                           #delete 1st line
a1 2                           #add following two lines at beginning
 data to be added
 here too
d24 3                          #delete lines 24-27
    """
    # A couple of tricky points:
    # As hunks are applied, the offset of later modifications changes, which
    # is tracked in 'mod'.
    # Additions happen *after* the named offset.

    delta = iter(delta)
    mod = 0
    for line in delta:
        mode = line[0]
        offset, count = (int(x) for x in line[1:].split())
        offset = offset - 1 + mod # for zero based indexing
        if mode == 'd':
            del lines[offset : offset + count ]
            mod -= count
        elif mode == 'a':
            lines[offset + 1 : offset + 1] = [delta.next() for i in range(count)]
            mod += count


def parse_rcs_file(filename):
    """Extract all revisions from the named RCS file, and the head pointer.
    """
    if not filename.endswith(',v'):
        print >> sys.stderr, "WARNING:'%s' is not a good name for an RCS file" % filename

    f = open(filename)
    deltas = {}
    try:
        head = parse_intro(f)
        for line in f:
            if not line.strip():
                continue
            if line.startswith('desc'):
                break
            d = parse_delta(f, line)
            deltas[d['rev']] = d

        parse_desc(f, line)

        for line in f:
            if not line.strip():
                continue
            d = parse_deltatext(f, line)
            deltas[d['rev']]['text'] = d['text']
    except Exception, e:
        # because not all exceptions can know.
        print >> sys.stderr, 'File: %r' %filename
        raise

    return head, deltas



def rcs_revision_generator(filename):
    """generate all revisions of the file, in reverse order."""
    # This uses the RCS linked list, though it would work just as well
    # to sort the revisions.
    head, deltas = parse_rcs_file(filename)
    lines = deltas[head]['text']
    next = deltas[head]['next']
    yield deltas[head], ''.join(lines)
    while next:
        d = deltas[next]
        apply_delta(lines, d['text'])
        yield d, ''.join(lines)
        next = d['next']


def twiki_revision_generator(filename):
    """generate all revisions of the file, in reverse order, clearing
    out stupid metadata and fake revisions."""
    head, deltas = parse_rcs_file(filename)
    lines = deltas[head]['text']
    next = deltas[head]['next']

    yield deltas[head], ''.join(twiki_clean(lines)[0])
    while next:
        d = deltas[next]
        apply_delta(lines, d['text'])
        yield d, ''.join(twiki_clean(lines)[0])
        next = d['next']



def extract(filename, rfilter=None):
    """Find unique revisions of the file, and the relevant metadata.
    Most attached metadata is not relevant, and is binned.  In many
    cases the file is unchanged except for this useless metadata, so
    the revision is a false one.  We purge those.
    """
    versions = []
    for d, string in twiki_revision_generator(filename):
        revision = RcsParseVersion(filename, d, string)
        if rfilter is not None and not rfilter(revision):
            continue
        
        if not versions:
            versions.append(revision)
        elif revision.contents == versions[-1].contents:
            #because the revisions are being generated in reverse order
            versions[-1] = revision
        else:
            versions.append(revision)

    return versions

def acceptable_file(fn):
    return fn.endswith(',v')


if __name__ == '__main__':
    TEST =  '/home/douglas/twiki-data/Sugar/BackingUp.txt,v'
    from subprocess import PIPE, Popen

    for delta, revision in rcs_revision_generator(TEST):
        r = '.'.join(str(x) for x in delta['rev'])
        f = open('/tmp/python-%s.txt' % r, 'w')
        f.write(revision)
        f.close()

        f = open('/tmp/co-%s.txt' % r, 'w')
        callee = Popen(["co", "-p", "-r" + r,
                        "-q",
                        TEST
                       ],
                      stdout=f)
        f.close()
