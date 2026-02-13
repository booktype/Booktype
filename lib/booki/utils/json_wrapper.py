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

"""In Python 3, the json module is always available as a standard module.
This module maintains backward compatibility with code that might still
import from booki.utils.json_wrapper.

>>> from booki.utils.json_wrapper import json
>>> from booki.utils.json_wrapper import simplejson
>>> json is simplejson
True
"""

import json

simplejson = json
