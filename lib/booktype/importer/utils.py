
import os
import urllib

from booki.utils.misc import bookiSlugify


def convert_file_name(file_name):
    name = os.path.basename(file_name)

    if name.rfind('.') != -1:
        _np = name[:name.rfind('.')]
        _ext = name[name.rfind('.'):]
        name = bookiSlugify(_np)+_ext

    name = urllib.unquote(name)
    name = name.replace(' ', '_')

    return name


