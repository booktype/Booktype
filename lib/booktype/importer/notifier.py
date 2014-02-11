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


class Notifier(object):

    def debug(self, message):
        """Debugging message not for the end-user."""
        pass

    def info(self, message):
        """Information that could interest the end-user."""
        pass

    def warning(self, message):
        """Important information that the end-user should be aware of."""
        pass

    def error(self, message):
        """Information about an error condition."""
        pass


class StreamNotifier(Notifier):

    def __init__(self, stream):
        self.stream = stream

    def debug(self, message):
        self.stream.write("[DEBUG] " + message + "\n")
        self.stream.flush()

    def info(self, message):
        self.stream.write("[INFO] " + message + "\n")
        self.stream.flush()

    def warning(self, message):
        self.stream.write("[WARNING] " + message + "\n")
        self.stream.flush()

    def error(self, message):
        self.stream.write("[ERROR] " + message + "\n")
        self.stream.flush()


class CollectNotifier(Notifier):

    def __init__(self):
        self.debugs   = []
        self.infos    = []
        self.warnings = []
        self.errors   = []

    def debug(self, message):
        self.debugs.append(message)

    def info(self, message):
        self.infos.append(message)

    def warning(self, message):
        self.warnings.append(message)

    def error(self, message):
        self.errors.append(message)
