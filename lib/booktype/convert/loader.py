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

import types
import importlib

import logging

from .base import BaseConverter


logger = logging.getLogger("booktype.convert")


def find_all(module_names=None):
    if module_names is None:
        module_names = ("booktype.convert.converters", )
    registry = {}
    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except:
            print("could not load module " + module_name)
            continue
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if type(attr) is types.TypeType and issubclass(attr, BaseConverter):
                if hasattr(attr, "name"):
                    registry[attr.name] = attr
    return registry
