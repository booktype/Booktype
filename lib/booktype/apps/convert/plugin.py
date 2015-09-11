# This file is part of Booktype.
# Copyright (c) 2015 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
#
# Booktype is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Booktype is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Booktype.  If not, see <http://www.gnu.org/licenses/>.

import importlib
import logging

from booktype.utils import config

logger = logging.getLogger("booktype.convert")


class BasePlugin(object):
    def __init__(self, convert):
        """Base abstract class for all Theme plugins.

        :Args:
          - convert: Conversion object
        """

        self.convert = convert


class ExternalScriptPlugin(BasePlugin):
    """Base class for all Theme plugins which will execute external 
    script to produce output file.
    """
    def pre_convert(self, book):
        """Called before conversion process starts.

        :Args:
          - book: EPUB object for input file
        """
        raise NotImplementedError

    def post_convert(self, book, output_path):
        """Called when conversion process has ended.

        :Args:
          - book: EPUB object for input file
          - output_path: File path for output file
        """
        raise NotImplementedError

    def fix_content(self, content):
        """Transform chapter content.

        This method is used to modify content of each content. This is used when
        we need to add certain elements or classes to prepare the content mPDF 
        rendering.

        :Args:
          - content: lxml element object
        """
        raise NotImplementedError


class MPDFPlugin(ExternalScriptPlugin):
    "Base class for mPDF themes"

    def get_mpdf_config(self):
        """Returns mPDF options required for this theme.

        There are always certain mPDF options which are required for different
        themes. Instead of setting global mPDF configuration it is also 
        possible to define it per theme.

        :Returns:
          - Returns dictionary with mPDF options for this theme.
        """
        return {}


class ConversionPlugin(BasePlugin):
    """Base class for theme plugins which are not using external scripts
    to create required content.
    """

    def pre_convert(self, original_book, book):
        """Called before conversion process starts.

        :Args:
          - original_book:
          - book:
        """
        raise NotImplementedError

    def post_convert(self, original_book, book, output_path):
        """Called when conversion process has ended.

        :Args:
          - original_book: 
          - output_path:
          - 
        """        
        raise NotImplementedError

    def fix_content(self, content):
        """Transform chapter content.

        :Args:
          - content: lxml element object
        """

        raise NotImplementedError


def load_theme_plugin(convert_type, theme_name):
    """Load theme plugin for certain conversion and theme. Returns reference
    to plugin theme which has to be initialised later on.

    :Args:
      - convert_type: Type of conversion (mpdf, screenpdf, epub, ...)
      - theme_name: Theme name

    :Returns:
      Returns reference to plugin class which has to be initialised.
    """

    plgn = None

    plugins = config.get_configuration('BOOKTYPE_THEME_PLUGINS')

    try:
        module_name = plugins.get(theme_name, None)
        
        if module_name:
            module = importlib.import_module(module_name)
            plgn = module.__convert__.get(convert_type, None)
            return plgn
    except:
        logger.exception('Can not load the theme plugin.')

    return plgn


