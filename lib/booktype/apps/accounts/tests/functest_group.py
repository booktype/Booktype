import factory
from PIL import Image
import StringIO

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.files import uploadedfile
from django.db.models.signals import post_save

from .factory_models import UserFactory, BookFactory, BookiGroupFactory
from .factory_models import PLAIN_USER_PASSWORD


class GrouppageTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.group = BookiGroupFactory()
        self.dispatcher = reverse('portal:group', args=[self.group.url_name])

    def tearDown(self):
        self.user.delete()

    def test_group(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['title'], 'Group used')

    def test_anonymous_user(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['user'].is_authenticated(), False)
        self.assertNotContains(response, 'MY DASHBOARD')
        self.assertNotContains(response, 'JOIN THIS GROUP')
        self.assertContains(response, 'SIGN IN')

    def test_loggedin_user_not_a_member(self):
        self.client.login(
            username=self.user.username,
            password=PLAIN_USER_PASSWORD
        )
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['user'].is_authenticated(), True)
        self.assertContains(response, 'MY DASHBOARD')
        self.assertNotContains(response, 'SIGN IN')
        self.assertContains(response, 'JOIN THIS GROUP')

    def test_loggedin_user_a_member(self):
        self.client.login(
            username=self.user.username,
            password=PLAIN_USER_PASSWORD
        )
        self.group.members.add(self.user)
        i = 0
        while i < 10:
            self.group.members.add(UserFactory())
            i += 1

        response = self.client.get(self.dispatcher)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['user'].is_authenticated(), True)
        self.assertContains(response, 'MY DASHBOARD')
        self.assertNotContains(response, 'SIGN IN')
        self.assertContains(response, 'LEAVE THIS GROUP')
        self.assertContains(response, 'GROUP SETTINGS')
        self.assertEquals(str(response).count('list-info'), 12)