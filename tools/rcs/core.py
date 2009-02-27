import sys, os


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

    def to_git(self, write=sys.stdout.write):
        write("commit %s\n" % self.gitref)
        write("committer %s <%s@flossmanuals.net> %s +0000\n" %
              (self.author, self.author, self.date))
        self._data_blob("TWiki import: %s revision %s" % (self.name, self.revision))
        write('M 644 inline %s\n' % (self.name))
        self._data_blob(self.contents)
        write("\n")

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
