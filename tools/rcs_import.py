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

from rcs.core import thoeny_filter

def recurse_and_commit(path, sort=False, rfilter=None):
    """Find all the RCS files to put into git.  If sort is False, the
    files are dealt with in the order that they fall out of RCS
    (i.e. one file at a time). Otherwise, they are sorted first by
    date."""
    print "reset master\n"
    versions = []
    os.chdir(path)
    for root, dirs, files in os.walk('.'):
        for f in files:
            if acceptable_file(f):
                try:
                    vs = extract(os.path.join(root, f), rfilter)
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


# TODO: try slow import (via working dir)
# try one branch at a time import



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

    if options.use_rcs:
        from rcs.subprocess_parse import extract, acceptable_file
    else:
        from rcs.parse import extract, acceptable_file

    FORCE = options.force

    if options.no_thoeny:
        rfilter = thoeny_filter
    else:
        rfilter=None

    for d in dirs:
        recurse_and_commit(d, options.sort_by_date, rfilter)
