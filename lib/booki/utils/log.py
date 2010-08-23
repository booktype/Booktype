import simplejson 

from booki.editor import models

# logBookHistory

def logBookHistory(book = None, version = None, chapter = None, chapter_history = None, args = {}, user=None, kind = 'unknown'):
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
    history = models.ChapterHistory(chapter = chapter,
                                    content = content,
                                    user = user,
                                    revision = revision,
                                    comment = comment)
    history.save()

    return history



def logError(msg, *args):
    import logging
    logging.getLogger("booki").error(msg, *args)

def logWarning(msg, *args):
    import logging
    logging.getLogger("booki").warning(msg, *args)

    
def printStack(*extra):
    import traceback
    logError(traceback.format_exc())
    for e in extra:
        logError(e)
                            