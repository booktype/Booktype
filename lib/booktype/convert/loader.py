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

import logging
import inspect
import importlib

from .base import BaseConverter

logger = logging.getLogger("booktype.convert")


def find_all(module_names=None):
    """
    Method to load all the converter classes. If module_names params is not
    given it will use default booktype one.

    :Args:
      - module_names: Tuple of converter modules

    :Returns:
      - A dict of the successfully loaded modules
    """

    standard_module = 'booktype.convert.converters'
    if module_names is None:
        module_names = (standard_module, )

    # A valid Converter class should match next criterias:
    # - be subclass of BaseConverter
    # - has the attribute `name` that match with some
    #   exporting profile: mpdf, screenpdf, epub, ...
    def pred(klass):
        return (
            inspect.isclass(klass) and
            issubclass(klass, BaseConverter) and
            hasattr(klass, "name")
        )

    # We need to make sure that we're not using an imported converter class
    # instead of a one defined in current inspected module. So, we check
    # if the klass belongs to current inspected module or at least belongs to
    # the standard booktype.convert.converters module which is the only allowed
    # to import all the converters instead of define them inside the module
    # Issue reference: https://dev.sourcefabric.org/browse/BK-1892
    def allowed_module(klass, module_name):
        return (
            klass.__module__ == module_name or
            module_name == standard_module
        )

    registry = {}

    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            print("could not load module %s: %s" % (module_name, e))
            continue

        # Run over all the classes for the given current module_name
        for _, klass in inspect.getmembers(module, pred):
            if allowed_module(klass, module_name):
                if klass.name in registry:
                    logger.warn("Converter class with name `%s` has been already loaded" % klass.name)
                    continue
                else:
                    registry[klass.name] = klass

    return registry
