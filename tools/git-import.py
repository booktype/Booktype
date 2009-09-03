#!/usr/bin/python
import os, sys, time, re
from subprocess import check_call, Popen, PIPE


STAGING_DIR = '/home/douglas/fm-data/import-tests/staging'

DEST_DIR = '/home/douglas/fm-data/import-tests/booki-data.git'
SEPARATOR = "\n------8<-----------------\n"

WRITE = sys.stdout.write

branches = set(['master'])

def to_git(branch, chapter, text, author, email, date, version, comments,
           write=WRITE):
    if comments:
        comments = '\n' + comments
    write("commit refs/heads/%s\n" % branch)
    write("committer %s <%s@flossmanuals.net> %s\n" % (author, email, date))
    _data_blob("TWiki import: %s r%s%s" % (chapter, version, comments), write)
    if branch not in branches:
        write('merge refs/heads/master\n')
        branches.add(branch)

    write('M 644 inline %s\n' % (chapter))
    _data_blob(text, write)
    write("\n")

def _data_blob(data, write=WRITE):
    write("data %s\n" % len(data))
    write(data)
    write('\n')


def initialise(dir=DEST_DIR, clear=False):
    if clear and os.path.exists(dir):
        check_call(['rm', '-rf', dir])
    if not os.path.exists(dir):
        os.makedirs(dir)
    os.chdir(dir)
    check_call(['git', 'init', '-q', '--bare'])

def import_staged_files(dir=STAGING_DIR):
    for subdir in sorted(os.listdir(dir)):
        for filename in sorted(os.listdir(os.path.join(dir, subdir))):
            import_file(os.path.join(dir, subdir, filename))

def import_file(filename):
    #1204448128.XO_for_kids.OpeningXO.1.13
    #date, book, chapter, one, version = filename.split()
    f = open(filename)
    header, body = f.read().split(SEPARATOR)
    f.close()
    headers = parse_headers(header)
    h = headers.pop
    #date = time.strftime('%F %R:%S', time.gmtime(int(h('date'))))
    date = h('date') + ' +0100'
    to_git(h('book'), h('chapter'), body, h('author'), h('email'), date, h('version'),
           '\n'.join("%s: %s" % x for x in headers.items()), write=WRITE)
    #sys.stderr.write('.')


def parse_headers(s):
    headers = {}
    for line in s.split('\n'):
        if ':' not in line:
            #print >> sys.stderr, "skipping line '%s'" % line
            continue
        k, v = (x.strip() for x in line.split(': ', 1))
        if k == 'book2':
            continue
        if k == 'PREFERENCE':
            k, v = extract_preference(v)
        headers[k] = v
    return headers

def extract_preference(s):
    found = {}
    for m in re.finditer(r"""(["'])(.*?)\1=(['"])(.*?)\3""", s):
        k, v = m.group(2, 4)
        found[k] = v
    #print >> sys.stderr, found, s
    name = found.pop('name')
    value = found.pop('value')
    if found:
        value += ' (and:' + str(found) + ')'
    return name, value


def empty_master_commit():
    to_git('master', 'Hello', 'This is not a manual', 'Douglas Bagnall',
           'douglas@paradise.net.nz', '99999999 +1200', '', 'Not a manual',
           write=WRITE)



if __name__ == '__main__':
    initialise(clear=True)
    empty_master_commit()
    import_staged_files()
