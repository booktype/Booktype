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

import string


def _is_delimiter(c):
    try:
        if c in string.whitespace:
            return True
        else:
            return False
    except UnicodeEncodeError:
        return False


def _is_punctuation(c):
    try:
        if c in string.punctuation:
            return True
        else:
            return False
    except UnicodeEncodeError:
        return False


def _wordcount(i):
    count = 0
    try:
        while True:
            if not _is_delimiter(next(i)):
                count += 1
                while not _is_delimiter(next(i)):
                    pass
    except StopIteration:
        return count


def wordcount(text):
    if isinstance(text, str):
        text = unicode(text, "utf-8")
    return _wordcount(iter(text))


def charcount(text):
    if isinstance(text, str):
        text = unicode(text, "utf-8")
    count = 0
    try:
        i = iter(text)
        while True:
            foo = next(i)
            if not _is_delimiter(foo):
                count += 1
    except StopIteration:
        return count


def charspacecount(text):
    if isinstance(text, str):
        text = unicode(text, "utf-8")
    count = 0
    try:
        i = iter(text)
        while True:
            next(i)
            count += 1
    except StopIteration:
        return count


if __name__ == "__main__":
    print wordcount("")
    print wordcount("    ")
    print wordcount("    a")
    print wordcount("      ,., ....")
    print wordcount(" a b  ,., ....")
    print wordcount(" a b  ,., .... c ")
    print wordcount(",,, 1 2 3 4 5 6 7 8 9 deset ,,,.. jedanaest")
    print charspacecount("ab cd")
