
import os
import urllib
import importlib

from booktype.utils import config
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


def get_importer_module(ext):
    """
    Function to retrieve the right module to import a file into a book
    based on a given extension
    """

    IMPORTER_MAP = config.get_configuration('BOOKTYPE_IMPORTERS')
    if ext not in IMPORTER_MAP.keys():
        raise NotImplemented("Importer for extension {} hasn't been implemented yet".format(ext))

    module_path, import_func = IMPORTER_MAP[ext]
    module = importlib.import_module(module_path)
    return getattr(module, import_func)
