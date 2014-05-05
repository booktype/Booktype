import factory
from PIL import Image
import StringIO

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.files import uploadedfile
from django.db.models.signals import post_save

from .factory_models import UserFactory, BookFactory, BookiGroupFactory, BookHistoryFactory
from .factory_models import PLAIN_USER_PASSWORD


class FrontpageTest(TestCase):
    def setUp(self):
        self.dispatcher = reverse('portal:frontpage')
        self.user = UserFactory()

    def tearDown(self):
        self.user.delete()

    def test_frontpage(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['title'], 'Home')

    def test_anonymous_user(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['user'].is_authenticated(), False)
        self.assertNotContains(response, 'MY DASHBOARD')
        self.assertContains(response, 'SIGN IN')

    def test_loggedin_user(self):
        self.client.login(
            username=self.user.username,
            password=PLAIN_USER_PASSWORD
        )
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['user'].is_authenticated(), True)
        self.assertContains(response, 'MY DASHBOARD')
        self.assertNotContains(response, 'SIGN IN')

    def test_many_books(self):
        i = 0
        while (i < 10):
            book = BookFactory()
            i += 1
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)

        self.assertEquals(str(response).count('book-info'), 4)

    def test_many_people(self):
        i = 0
        while(i < 10):
            user = UserFactory()
            i += 1
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(str(response).count('people-info'), 2)

    def test_many_groups(self):
        i = 0
        while i < 10:
            bookiGroup = BookiGroupFactory()
            i += 1
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(str(response).count('list-info'), 5)

    def test_recent_activity(self):
        i = 0
        while (i < 10):
            bookHistory = BookHistoryFactory()
            i += 1
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(str(response).count('list-info'), 5)