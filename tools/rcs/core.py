import sys, os, subprocess


class RCSError(Exception):
    pass

class ParseError(Exception):
    pass

class GitContext:
    def __init__(self, work_tree, git_dir=None, strip_directories=True):
        self.work_tree = work_tree
        if git_dir is not None:
            self.git_dir = git_dir
        else:
            self.git_dir = os.path.join(work_tree, '.git')
        self.strip_dir = strip_directories

    def command(self, *args):
        cmd = ["git", "--git-dir=" + self.git_dir, "--work-tree=" + self.work_tree,]
        cmd.extend(args)
        subprocess.check_call(cmd)


class Version:
    contents = ''
    gitref = 'HEAD'
    branches = set()

    def __init__(self, name, revision, date, author, context=None):
        self.name = os.path.normpath(name)
        self.revision = revision
        self.author = author
        self.set_date(date)
        self.branch = self.gitref
        self.git = context

    def _data_blob(self, data, write=sys.stdout.write):
        write("data %s\n" % len(data))
        write(data)
        write('\n')

    def to_git(self, branch=None, write=sys.stdout.write, strip_dir=False):
        if strip_dir:
            filename = os.path.basename(self.name)
        else:
            filename = self.name

        if branch is None:
            branch = self.branch
        write("commit %s\n" % branch)
        write("committer %s <%s@flossmanuals.net> %s +0000\n" %
              (self.author, self.author, self.date))
        self._data_blob("TWiki import: %s revision %s" % (self.name, self.revision))
        write('M 644 inline %s\n' % (filename))
        self._data_blob(self.contents)
        write("\n")

    def to_git_slow(self, branch=None, write=None, strip_dir=False):
        """Write to git via the working tree"""
        if strip_dir:
            filename = os.path.basename(self.name)
        else:
            filename = self.name

        if branch is not None and branch != self.branch:
            if branch in self.branches:
                self.git.command("checkout", branch)
            else:
                self.git.command("checkout", "-l", "-b", branch)
                self.branches.add(branch)

        # put the new version there
        f = open(filename, 'w')
        f.write(self.contents)
        f.close()
        subprocess.check_call(["git", "--git-dir=%s"% self.gitdir,
                               "--work-tree=%s" % self.worktree,
                               "commit",
                               "--author=%s@flossmanuals.net" % self.author,
                               "-m", "TWiki import: %s rev. %s" % (self.name, self.revision),
                               filename])


    def __str__(self):
        return ("<File %s revision %s branch: %s (%s, %s)>" %
                (self.name, self.revision, self.branch, self.author, self.date))

    __repr__ = __str__

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
