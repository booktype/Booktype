# This file is part of Booktype.
# Copyright (c) 2012
# Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

import json

from booktype.apps.export.models import ExportSettings
from booktype.utils import config


def get_settings(book, export_format):
    """Get export settings for certain book and export format.

    :Args:
      - book (:class:`booki.editor.models.Book`: Book instance
      - export_format: Type of export format

    :Returns:
      Returns a dictionarty with settings for the certain format.
    """

    try:
        pw = ExportSettings.objects.get(book=book,
            typeof=export_format)

        settings_options = json.loads(pw.data)
    except ExportSettings.DoesNotExist:
        settings_options = config.get_configuration('EXPORT_SETTINGS')[export_format]
    except:
        settings_options = config.get_configuration('EXPORT_SETTINGS')[export_format]

    return settings_options


def get_settings_as_dictionary(book, export_format):
    return {elem['name']:elem['value'] for elem in get_settings(book, export_format)}


def set_settings(book, export_format, data):
    """Set export settings for certain book and export format.

    :Args:
      - book (:class:`booki.editor.models.Book`: Book instance
      - export_format: Type of export format
      - data: Dictionaty with new export settings

    """

    pw, created = ExportSettings.objects.get_or_create(book=book,
        typeof=export_format)

    pw.data = json.dumps(data)
    pw.save()