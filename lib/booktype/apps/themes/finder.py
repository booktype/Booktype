import os

from collections import OrderedDict as SortedDict
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils._os import safe_join

from django.contrib.staticfiles import utils, finders


class ThemeFinder(finders.BaseFinder):
    """Finder of static files for our themes.

    Themes are installed at $INSTANCE/themes/ directory. Inside that directory custom themes can have
    static files for using over the web. This ThemeFinder will find these files and put them with
    the rest of the static files on the system.
    """

    def __init__(self, apps=None, *args, **kwargs):
        # List of locations with static files
        self.locations = []
        # Maps dir paths to an appropriate storage instance
        self.storages = SortedDict()

        for theme_name in os.listdir('{}/themes/'.format(settings.BOOKTYPE_ROOT)):
            theme_dir = '{}/themes/{}'.format(settings.BOOKTYPE_ROOT, theme_name)
            static_dir = '{}/static/'.format(theme_dir)

            if os.path.isdir(static_dir):
                theme_prefix = 'themes/{}'.format(theme_name)
                self.locations.append((theme_prefix, static_dir))

                filesystem_storage = FileSystemStorage(location=static_dir)
                filesystem_storage.prefix = theme_prefix
                self.storages[static_dir] = filesystem_storage

        super(ThemeFinder, self).__init__(*args, **kwargs)

    def find(self, path, all=False):
        matches = []
        for prefix, root in self.locations:
            matched_path = self.find_location(root, path, prefix)
            if matched_path:
                if not all:
                    return matched_path
                matches.append(matched_path)
        return matches

    def find_location(self, root, path, prefix=None):
        if prefix:
            prefix = '%s%s' % (prefix, os.sep)
            if not path.startswith(prefix):
                return None
            path = path[len(prefix):]
        path = safe_join(root, path)
        if os.path.exists(path):
            return path

    def list(self, ignore_patterns):
        for prefix, root in self.locations:
            storage = self.storages[root]
            for path in utils.get_files(storage, ignore_patterns):
                yield path, storage
