import datetime

from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from booki.editor import models
from booki.utils.log import logBookHistory

def createBook(user, bookTitle, status = "imported", bookURL = None):
    """
    Create book and sets status.

    TODO: status?
    """

    if bookURL:
        url_title = bookURL
    else:
        url_title = slugify(bookTitle)

    book = models.Book(url_title = url_title,
                       title = bookTitle,
                       owner = user, 
                       published = datetime.datetime.now())

    book.save()

    # put this in settings file
    status_default = ["published", "not published", "imported"]
    n = len(status_default)

    for statusName in status_default:
        status = models.BookStatus(book=book, name=statusName, weight=n)
        status.save()
        n -= 1

    # not use "not published" but first in the list maybe, or just status
    book.status = models.BookStatus.objects.get(book=book, name="not published")
    book.save()
    
    
    version = models.BookVersion(book = book,
                                 major = 1,
                                 minor = 0,
                                 name = 'initial',
                                 description = '')
    version.save()

    book.version = version
    book.save()

    logBookHistory(book = book, 
                   version = version,
                   user = user,
                   kind = 'book_create')

    import booki.editor.signals    
    booki.editor.signals.book_created.send(sender = user, book = book)

    return book
