import factory

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.webdesign.lorem_ipsum import paragraphs

from booki.editor.models import Book, BookVersion, Chapter
from booki.editor.models import BookStatus, BookToc

PLAIN_USER_PASSWORD = 'top_secret'

class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User

    username = factory.Sequence(lambda n: 'user%d' % n)
    email = factory.LazyAttribute(lambda obj: '%s@test.sourcefabric.org' % obj.username)
    password = make_password(PLAIN_USER_PASSWORD)

class BookFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Book

    url_title = factory.Sequence(lambda n: 'first-book-test-bla-foo-%d' % n)
    title = factory.Sequence(lambda n: 'First Book Test Bla Foo %d' % n)
    owner = factory.SubFactory(UserFactory)

class BookStatusFactory(factory.DjangoModelFactory):
    FACTORY_FOR = BookStatus

    book = factory.SubFactory(BookFactory)
    name = factory.Sequence(lambda n: 'name %d' % n)
    weight = factory.Sequence(lambda n: n)

class BookVersionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = BookVersion

    book = factory.SubFactory(BookFactory)
    major = 1
    minor = 0

class ChapterFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Chapter

    version = factory.SubFactory(BookVersionFactory)
    book = factory.SubFactory(BookFactory)

    url_title = factory.Sequence(lambda n: 'chapter-%d' % n)
    title = factory.Sequence(lambda n: 'Chapter %d' % n)
    status = factory.SubFactory(BookStatusFactory)
    content = paragraphs(4)

class BookTocFactory(factory.DjangoModelFactory):
    FACTORY_FOR = BookToc

    @classmethod
    def create_toc(cls, book, book_version, chapter):
        
        # create section item
        cls(
            book = book,
            version = book_version,
            name = 'Section One',
            chapter = None,
            weight = 0,
            typeof = 0
        )

        # create chapter item
        cls(
            book = book,
            version = book_version,
            name = 'Chapter 1',
            chapter = chapter,
            weight = 1,
            typeof = 1
        )