import factory

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.webdesign.lorem_ipsum import paragraphs

from booki.editor.models import Book, BookVersion, Chapter, BookStatus, BookiGroup, Language, BookHistory
from booki.account.models import UserProfile

PLAIN_USER_PASSWORD = 'testpassword'


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User

    username = factory.Sequence(lambda n: 'user%d' % n)
    email = factory.LazyAttribute(lambda obj: '%s@test.sourcefabric.org' % obj.username)
    password = make_password(PLAIN_USER_PASSWORD)


class UserProfileFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = UserProfile

    description = 'description'

    user = factory.SubFactory(UserFactory, profile=None)


class BookiGroupFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = BookiGroup

    name = 'group name'
    url_name = 'url_group_name'
    description = 'booki group description'
    owner = factory.SubFactory(UserFactory)

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for member in extracted:
                self.members.add(member)


class BookFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Book

    owner = factory.SubFactory(UserFactory)
    url_title = factory.Sequence(lambda n: 'title_{}'.format(n))
    title = factory.Sequence(lambda n: 'book title_{}'.format(n))
    status = BookStatus()
    language = Language(0, 'test language', 'tl')
    version = BookVersion(0, 0, 0, 0)
    group = factory.SubFactory(BookiGroupFactory)


class BookStatusFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = BookStatus
    book = factory.SubFactory(BookFactory)
    name = 'status name'
    weight = 0


class BookHistoryFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = BookHistory

    book = factory.SubFactory(BookFactory)
    args = factory.Sequence(lambda n: 'args_{}'.format(n))
    user = factory.SubFactory(UserFactory)