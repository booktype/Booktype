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

FORCE = False

import traceback
import os, sys

from rcs.core import thoeny_filter, Version

def recursive_history_generator(path, rfilter=None):
    """The generator that yields available RCS histories form the
    given directory.  rfilter should return true if the revision is
    acceptable (based on metadata)"""
    versions = []
    os.chdir(path)
    for root, dirs, files in os.walk('.'):
        for f in files:
            if acceptable_file(f):
                try:
                    vs = extract(os.path.join(root, f), rfilter)
                    yield vs
                except Exception, e:
                    if not FORCE:
                        raise
                    traceback.print_exc()
                    print >> sys.stderr, "Continuing, but ignoring %r..." % f


def sorted_history(path, rfilter=None):
    """All file changes in chronological order"""
    versions = []
    for vs in recursive_history_generator(path, rfilter):
        versions.extend(vs)
    _versions = [(int(v.date), v) for v in versions]
    _versions.sort()
    for d, v in _versions:
        v.to_git()


def file_by_file_history(path, rfilter=None):
    """Complete each files history before beginning on the next.  (revisions in the order they fall out of """
    for vs in recursive_history_generator(path, rfilter):
        for v in reversed(vs):
            v.to_git()

def book_as_branch_history(path, rfilter=None):
    """Complete each files history before beginning on the next"""
    branch = None
    for vs in recursive_history_generator(path, rfilter):
        if not vs:
            continue
        d = os.path.dirname(vs[0].name)
        if d != branch:
            #new book, new branch
            branch = d
            print "reset %s" % branch

        for v in reversed(vs):
            print v
            v.to_git(branch, strip_dir=True)


SORT_MODES = {
    'sorted' : sorted_history,
    'by-file' : file_by_file_history,
    'branches' : book_as_branch_history,
    }



# TODO: try slow import (via working dir)
# try one branch at a time import



if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-t", "--no-thoeny", action="store_true",
                      help="ignore TWiki housekeeping commits", default=False)
    parser.add_option("-m", "--sort-mode", metavar="MODE",
                      help="use sort mode, MODE %s." % (SORT_MODES.keys(),),
                      default='sorted')
    parser.add_option("-r", "--use-rcs", action="store_true",
                      help="Use rcs subprocesses (slow, canonical).", default=False)
    parser.add_option("-f", "--force", action="store_true",
                      help="Don't give up on parsing errors.", default=False)
    parser.add_option("-w", "--working-tree", action="store_true",
                      help="Use working tree for commits.", default=False)
    options, dirs = parser.parse_args()

    if options.use_rcs:
        from rcs.subprocess_parse import extract, acceptable_file
    else:
        from rcs.parse import extract, acceptable_file

    FORCE = options.force

    if options.no_thoeny:
        rfilter = thoeny_filter
    else:
        rfilter=None

    if options.working_tree:
        Version.to_git = Version.to_git_slow


    sorter = {
        'sorted' : sorted_history,
        'by-file' : file_by_file_history,
        'branches' : book_as_branch_history,
        }[options.sort_mode]

    for d in dirs:
        sorter(d, rfilter)

