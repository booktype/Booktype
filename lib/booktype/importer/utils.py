
import os
import urllib

from booktype.utils.misc import booktype_slugify


def convert_file_name(file_name):
    name = os.path.basename(file_name)

    if name.rfind('.') != -1:
        _np = name[:name.rfind('.')]
        _ext = name[name.rfind('.'):]
        name = booktype_slugify(_np)+_ext

    name = urllib.unquote(name)
    name = name.replace(' ', '_')

    return name


