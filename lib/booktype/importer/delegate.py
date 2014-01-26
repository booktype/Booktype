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


class Delegate(object):

    def get_reader_plugins(self):
        return []

    def is_valid_cover(self, image):
        """ Checks whether the provided image is a valid cover image.

        Returns True if it is valid or (False, reason) if it is not.

        Returning None signals that the validity check is not performed
        by the delegate.
        """
        return None

    def should_import_image(self, image):
        return True

    def should_import_document(self, document):
        return True
