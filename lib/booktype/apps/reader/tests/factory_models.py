import factory

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from booki.editor.models import Book, BookVersion

PLAIN_USER_PASSWORD = 'top_secret'

class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User

    username = factory.Sequence(lambda n: 'user%d' % n)
    email = factory.LazyAttribute(lambda obj: '%s@test.sourcefabric.org' % obj.username)
    password = make_password(PLAIN_USER_PASSWORD)

class BookFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Book

    url_title = 'first-book-test-bla-foo'
    title = 'First Book Test Bla Foo'
    owner = factory.SubFactory(UserFactory)

class BookVersionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = BookVersion

    book = factory.SubFactory(BookFactory)
    major = 1
    minor = 0