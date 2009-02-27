'''Parse RCS files using RCS binaries in subprocesses.  This is much
slower than rcs.parse, but if their output differs this one is most
probably right.
'''

from rcs.core import Version
import traceback
import os, sys, time
from subprocess import Popen, PIPE

from rcs.core import twiki_clean, RCSError

def acceptable_file(fn):
    return not fn.endswith(',v')

class RCSVersion(Version):
    """For data from rlog process.
    self.contents is not set in __init__; it should be done later.
    """
    def set_date(self, date):
        t = time.strptime(date, "%Y/%m/%d %H:%M:%S")
        self.date = time.strftime("%s", t)
        


def revision_list(filename):
    """Cheap and crappy parsing of rcs log.  A typical section looks
    like this (With TWiki, comment is always 'none', so we ignore it):

----------------------------
revision 1.3
date: 2008-01-14 04:29:18+00;  author: ThomasMiddleton;  state: Exp;  lines: +2 -2
none
----------------------------

   The revisions are returned in *reverse* order.
"""
    callee = Popen(["rlog", "-N", filename], stdout=PIPE)
    revisions = []
    for line in callee.stdout:
        if line == '----------------------------\n':
            line = callee.stdout.next()
            if not line.startswith("revision "):
                raise RCSError("can't understand this log: got '%s', expecting revision: x.xx")
            revno = line[9:].strip()
            line = callee.stdout.next()
            bits = line.split(';')
            date = bits[0][6:]             #len('date: ')
            author = bits[1].strip()[8:]   #len('author: ')
            r = RCSVersion(filename, revno, date, author)
            revisions.append(r)

    return revisions


def extract(filename, rfilter=None):
    """Find unique revisions of the file, and the relevant metadata.
    Most attached metadata is not relevant, and is binned.  In many
    cases the file is unchanged except for this useless metadata, so
    the revision is a false one.  We purge those.
    """
    versions = []
    for revision in revision_list(filename):
        if rfilter is not None and not rfilter(revision):
            continue

        callee = Popen(["co", "-p", "-r" + revision.revision,
                        "-q", "-ko",
                        filename
                       ],
                      stdout=PIPE)

        data, meta = twiki_clean(callee.stdout)

        # many revisions are identical execpt for metadata. Ignore those.
        revision.contents = ''.join(data)
        if not versions:
            versions.append(revision)
        elif revision.contents == versions[-1].contents:
            #because the revisions are being generated in reverse order
            versions[-1] = revision
        else:
            versions.append(revision)


    return versions



