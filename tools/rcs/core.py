import sys, os, subprocess


class RCSError(Exception):
    pass

class ParseError(Exception):
    pass

class Version:
    contents = ''
    gitref = 'HEAD'

    def __init__(self, name, revision, date, author):
        self.name = os.path.normpath(name)
        self.revision = revision
        self.author = author
        self.set_date(date)

    def _data_blob(self, data, write=sys.stdout.write):
        write("data %s\n" % len(data))
        write(data)
        write('\n')

    def to_git(self, branch=None, write=sys.stdout.write):
        if branch is None:
            branch = self.gitref
        write("commit %s\n" % branch)
        write("committer %s <%s@flossmanuals.net> %s +0000\n" %
              (self.author, self.author, self.date))
        self._data_blob("TWiki import: %s revision %s" % (self.name, self.revision))
        write('M 644 inline %s\n' % (self.name))
        self._data_blob(self.contents)
        write("\n")

    def to_git_slow(self, branch=None, write=sys.stdout.write):
        """Write to git via the working tree"""
        if branch is not None:
            raise NotImplementedError("can't set branches in slow import, yet")
        # put the new version there
        f = open(self.name, 'w')
        f.write(self.contents)
        f.close()
        subprocess.check_call(["git", "commit",
                               "--author=%s@flossmanuals.net" % self.author,
                               "-m", "TWiki import: %s rev. %s" % (self.name, self.revision),
                               self.name])




    def set_date(self, date):
        raise NotImplementedError("subclass me, please")


def twiki_clean(lines):
    """Remove TWiki Metadata"""
    data = []
    meta = []
    for line in lines:
        if not line.startswith('%META:'):
            data.append(line)
        else:
            meta.append(line)
    return data, meta


def thoeny_filter(revision):
    """Reject old commits and commits by known twiki authors"""
    if (revision.author in ('PeterThoeny', 'thoeny')
        or int(revision.date) < 1050000000):
        return False
    return True
