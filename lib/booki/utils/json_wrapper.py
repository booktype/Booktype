# This file is part of Booktype.
# Copyright (c) 2012 Douglas Bagnall
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

"""In Python 2.5, the json module we use is an external module called
'simplejson'.  From Python 2.6, it is a standard module called 'json'.
Just to complicate things, in Debian's Python 2.5, there is an
entirely different module called 'json', so 'import json' might apeear
to work there but do the worng thing.

This module includes the logic for ensuring that the right module gets
imported.  For simplcity of backwards compatibility, the module it
finds is called both 'simplejson' and 'json'.

>>> from booki.utils.json_wrapper import json
>>> from booki.utils.json_wrapper import simplejson
>>> json is simplejson
True
"""

try:
    import json
    if not hasattr(json, 'loads'):
        raise ImportError('accidentally imported the wrong json module.')
except ImportError, e:
    from warnings import warn
    warn('json not found: "%s", trying simplejson' % e)
    del warn
    import simplejson as json

simplejson = json
