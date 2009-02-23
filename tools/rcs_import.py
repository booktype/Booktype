#!/usr/bin/python
"""Read TWiki RCS files, and import the data into git.

cd path/for/new/git/repo
git init --shared=all
rcs_import.py path/to/twiki/data | git-fast-import

# now the data is in git but not visible yet

git checkout

# examine it with one of these:

gitk
git log
git gui

# to start again at any point:

rm -rf .git
# and if you have the done `git checkout`:
rm -r *

"""

THEONY = True
FORCE = False

import traceback
import os, sys, time
from subprocess import call, PIPE, Popen

class RCSError(Exception):
    pass


class RCSVersion:
    data = ''
    gitref = 'HEAD'
    marker = iter(xrange(1,9999999))

    def __init__(self, name, revision, date, author):
        self.name = os.path.normpath(name)
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
        write("mark :%s\n" % self.marker.next())
        write("committer %s <%s@flossmanuals.net> %s +0000\n" %
              (self.author, self.author, self.date))
        self._data_blob("Import from TWiki: %s revision %s" % (self.name, self.revision))
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



def rcs_extract_subprocess(filename):
    """Find unique revisions of the file, and the relevant metadata.
    Most attached metadata is not relevant, and is binned.  In many
    cases the file is unchanged except for this useless metadata, so
    the revision is a false one.  We purge those.
    """
    versions = []
    for revision in revision_list(filename):
        if not THOENY and revision.author in ('PeterThoeny', 'thoeny') \
               or int(revision.date) < 1050000000:
            continue

        callee = Popen(["co", "-p", "-r" + revision.revision,
                        "-q", "-ko",
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



class RcsParseVersion(RCSVersion):
    def __init__(self, name, d, string):
        self.name = os.path.normpath(name[:-2])  #drop the ',v'
        self.revision = '.'.join(str(x) for x in d['rev'])
        try:
            t = time.strptime(d['date'], "%Y.%m.%d.%H.%M.%S")
        except ValueError:
            #stupid date format is sometimes 2 digit, sometimes 4 digit years.
            t = time.strptime(d['date'], "%y.%m.%d.%H.%M.%S")
        self.date = time.strftime("%s", t)
        self.author = d['author']
        self.data = string


def rcs_extract(filename):
    """Find unique revisions of the file, and the relevant metadata.
    Most attached metadata is not relevant, and is binned.  In many
    cases the file is unchanged except for this useless metadata, so
    the revision is a false one.  We purge those.
    """
    import rcs_parse
    versions = []
    for d, string in rcs_parse.twiki_revision_generator(filename):
        revision = RcsParseVersion(filename, d, string)
        if not THOENY and revision.author in ('PeterThoeny', 'thoeny') \
               or int(revision.date) < 1050000000:
            continue
        if not versions or revision.data != versions[-1].data:
            versions.append(revision)
    return versions


def rcs_file(fn):
    return fn.endswith(',v')

def non_rcs_file(fn):
    return not fn.endswith(',v')


def recurse_and_commit(path, sort=False):
    """Find all the RCS files to put into git.  If sort is False, the
    files are dealt with in the order that they fall out of
    RCS. Otherwise, they are sorted first by date."""
    print "reset master\n"
    versions = []
    os.chdir(path)
    for root, dirs, files in os.walk('.'):
        for f in files:
            if acceptable_file(f):
                try:
                    vs = rcs_extract(os.path.join(root, f))
                    if sort:
                        versions.extend(vs)
                    else:
                        for v in reversed(vs):
                            v.to_git()
                except Exception, e:
                    if not FORCE:
                        raise
                    traceback.print_exc()
                    print >> sys.stderr, "Continuing, but ignoring %r..." % f

    _versions = [(int(v.date), v) for v in versions]
    _versions.sort()
    if sort:
        for d, v in _versions:
            v.to_git()


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-t", "--no-thoeny", action="store_true",
                      help="ignore TWiki housekeeping commits", default=False)
    parser.add_option("-s", "--sort-by-date", action="store_true",
                      help="Sort the RCS commits by date before feeding to git.", default=False)
    parser.add_option("-r", "--use-rcs", action="store_true",
                      help="Use rcs subprocesses (slow, canonical).", default=False)
    parser.add_option("-f", "--force", action="store_true",
                      help="Don't give up on parsing errors.", default=False)
    options, dirs = parser.parse_args()
    THOENY = not options.no_thoeny
    if options.use_rcs:
        rcs_extract = rcs_extract_subprocess
        acceptable_file = non_rcs_file
    else:
        acceptable_file = rcs_file
    if options.force:
        FORCE = True

    for d in dirs:
        recurse_and_commit(d, options.sort_by_date)
