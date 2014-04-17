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
        self.dispatcher = reverse('accounts:groups')
        self.user = UserFactory()

# setup for groups
        self.bookiGroup = BookiGroupFactory(members=(0, 1))

    def tearDown(self):
        self.user.delete()

    def test_accounts(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['title'], 'All groups')

    def test_group(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)

        self.assertContains(response, 'group name')
        self.assertContains(response, 'url_group_name')
        self.assertContains(response, 'booki group description')
        self.assertContains(response, 'Members: 1')
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