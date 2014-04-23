import factory
from PIL import Image
import StringIO

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.files import uploadedfile
from django.db.models.signals import post_save

from booki.editor.models import Book, BookStatus, Language, BookVersion, BookiGroup
from booki.account.models import UserProfile


class GrouppageTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

# setup for groups
        self.bookiGroup = BookiGroupFactory(members=(0, 1))

# setup for books
        self.book = BookFactory()

    def tearDown(self):
        self.user.delete()

    def test_accounts(self):
        self.dispatcher = reverse('accounts:group', kwargs={'groupid': self.bookiGroup.url_name})
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['title'], 'Group used')

    def test_group(self):
        self.dispatcher = reverse('accounts:group', kwargs={'groupid': self.bookiGroup.url_name})
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)

        self.assertContains(response, self.bookiGroup.name)
        self.assertContains(response, self.bookiGroup.description)
        self.assertContains(response, 'Members: 2')
        self.assertContains(response, 'Books: ')


class UserFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = User

    username = factory.Sequence(lambda n: "user_%d" % n)


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

    url_title = factory.Sequence(lambda n: 'title_{}'.format(n))
    title = 'book title'
    status = BookStatus()
    language = Language(0, 'test language', 'tl')
    version = BookVersion(0, 0, 0, 0)
    group = factory.SubFactory(BookiGroupFactory)
    owner = factory.SubFactory(UserFactory)
    hidden = False


class BookStatusFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = BookStatus
    book = factory.SubFactory(BookFactory)
    name = 'status name'
    weight = 0