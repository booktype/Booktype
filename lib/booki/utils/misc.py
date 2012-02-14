# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

from django.template.defaultfilters import slugify

def bookiSlugify(text):
    """
    Wrapper for default Django function. Default function does not work with unicode strings.

    @type text: C{string}
    @param: Text you want to slugify

    @rtype: C{string}
    @return: Returns slugified text
    """
    
    try:
        import unidecode

        text = unidecode.unidecode(text)
    except ImportError:
        pass

    return slugify(text)
