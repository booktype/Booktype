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

from booki.utils.json_wrapper import simplejson

from booki.editor import models

# logBookHistory

def logBookHistory(book = None, version = None, chapter = None, chapter_history = None, args = {}, user=None, kind = 'unknown'):
    """
    Creates history record for book change. 

    @type book: C{booki.editor.models.Book}
    @param book: Book object
    @type version: C{booki.editor.models.BookVersion}
    @param version: Book version object
    @type chapter: C{booki.editor.models.Chapter}
    @param chapter: Chapter object
    @type chapter_history: C{booki.editor.models.ChapterHistory}
    @param chapter_history: Chapter history object
    @type args: C{dict}
    @param args: Additional arguments
    @type user: C{django.contrib.auth.models.User}
    @param user: User who did modifications
    @type kind: C{string}
    @param kind: What kind of modification was done
    """

    history = models.BookHistory(book = book,
                                 version = version,
                                 chapter = chapter,
                                 chapter_history = chapter_history,
                                 args = simplejson.dumps(args),
                                 user = user,
                                 kind = models.HISTORY_CHOICES.get(kind, 0))
    history.save()

# logChapterHistory

def logChapterHistory(chapter = None, content = None, user = None, comment = '', revision = None):
    """
    Creates history record for chapter change.

    @type chapter: C{booki.editor.models.Chapter}
    @param chapter: Chapter object
    @type content: C{string}
    @param content: Old content
    @type user: C{django.contrib.auth.models.User}
    @param user: Booki user object
    @type comment: C{string}
    @param comment: Comment about this change
    @type revision: C{int}
    @param revision: Revision number for this change
    """

    history = models.ChapterHistory(chapter = chapter,
                                    content = content,
                                    user = user,
                                    revision = revision,
                                    comment = comment)
    history.save()

    return history



def logError(msg, *args):
    """
    Logs error message.

    @type msg: C{string}
    @param msg: Error message
    """

    import logging
    logging.getLogger("booki").error(msg, *args)

def logWarning(msg, *args):
    """
    Logs warning message.

    @type msg: C{string}
    @param msg: Warning message
    """

    import logging
    logging.getLogger("booki").warning(msg, *args)

def printStack(*extra):
    """
    Prints entire stack as error message.
    """

    import traceback
    logError(traceback.format_exc())
    for e in extra:
        logError(e)
