import datetime

from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from booki.editor import models
from booki.utils.log import logBookHistory

def createBook(user, bookTitle, status = "imported", bookURL = None):
    """
    Creates book.

    @todo: Do something about status.

    @type user: C{django.contrib.auth.models.User}
    @param user: Booki user who will be book owner
    @type bookTitle: C{string}
    @param bookTitle: Title for the book. If bookURL is omitted it will slugify title for the url version
    @type status: C{string} 
    @param status: String name for the status (optional)
    @type bookURL: C{string}
    @param bookURL: URL title for the book (optional)

    @rtype: C{booki.editor.models.Book}
    @return: Returns book object
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
