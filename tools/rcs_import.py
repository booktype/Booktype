#!/usr/bin/python
"""Read TWiki RCS files, and import the data into git"""

# This could be sped up using git-fast-import

import subprocess, os, sys, time

from subprocess import call, PIPE, Popen

class RCSError(Exception):
    pass


class RCSVersion:
    data = ''
    gitref = 'master'
    def __init__(self, name, revision, date, author):
        self.name = name
        self.revision = revision
        t = time.strptime(date, "%Y/%m/%d %H:%M:%S")        
        self.date = time.strftime("%s", t)
        self.author = author

    def _data_blob(self, data, write=sys.stdout.write):
        write("data %s\n" % len(data))
        write(data)
        write('\n')

    def to_git(self, write=sys.stdout.write):
        write("commit %s\n" % self.gitref)
        write("committer %s <%s@flossmanuals.net> %s +0000\n" %
              (self.author, self.author, self.date))
        self._data_blob("Import from TWiki")
        write('M 644 inline %s\n' % (self.name))
        self._data_blob(self.data)
        write("\n")
        

def revision_list(filename):
    """Cheap and crappy parsing of rcs log.  A typical section looks
    like this (With TWiki, comment is always 'none', so we ignore it):

----------------------------
revision 1.3
date: 2008-01-14 04:29:18+00;  author: ThomasMiddleton;  state: Exp;  lines: +2 -2
none
----------------------------
"""    
    callee = Popen(["rlog", "-N", filename], stdout=PIPE)
    #print callee, callee.stdout
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

    revisions.reverse()
    return revisions


def rcs_extract(filename):
    """Find unique revisions of the file, and the relevant metadata.
    Most attached metadata is not relevant, and is binned.  In many
    cases the file is unchanged except for this useless metadata, so
    the revision is a false one.  We purge those.
    """    
    versions = []
    for revision in revision_list(filename):
        callee = Popen(["co", "-p", "-r" + revision.revision, 
                        "-q",
                        filename
                       ],
                      stdout=PIPE)
        data = []
        for line in callee.stdout:
            if not line.startswith('%META:'):
                data.append(line)
                
        # many revisions are identical execpt for metadata. Ignore those.
        s = ''.join(data)
        if not versions or s != versions[-1].data:
            revision.data = ''.join(data)
            versions.append(revision)
    return versions


def recurse(path):
    os.chdir(path)
    for root, dirs, files in os.walk('.'):
        for f in files:
            if not f.endswith(',v'):
                versions = rcs_extract(f)
                for v in versions:
                    v.to_git()


if __name__ == '__main__':    
    recurse(sys.argv[1])
