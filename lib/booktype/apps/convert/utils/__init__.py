# This file is part of Booktype.
# Copyright (c) 2013 Borko Jandras <borko.jandras@sourcefabric.org>
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

from django.conf import settings

from .. import default_settings


def get_converter_module_names():
    try:
        return settings.BOOKTYPE_CONVERTER_MODULES
    except AttributeError:
        return default_settings.BOOKTYPE_CONVERTER_MODULES


def path2url(path, base=None):
    if base is None:
        base_path, base_url = settings.MEDIA_ROOT, settings.MEDIA_URL
    else:
        base_path, base_url = base

    if not base_path.endswith("/"):
        base_path += "/"
    if not base_url.endswith("/"):
        base_url += "/"

    if not path.startswith(base_path):
        raise ValueError("path not inside base path")

    return base_url + path[len(base_path):]
