from django.test import TestCase
from django.core.urlresolvers import reverse

from booktype.apps.core.tests.factory_models import UserFactory, BookGroupFactory


class GrouppageTest(TestCase):
    def setUp(self):
        self.dispatcher = reverse('portal:list_groups')
        self.user = UserFactory()

        # setup for groups
        self.bookGroup = BookGroupFactory(members=(0, 1))

    def tearDown(self):
        self.user.delete()

    def test_accounts(self):
        response = self.client.get(self.dispatcher)

        self.assertEquals(response.status_code, 403)

        # This is temporary. We should test this logic in new tests
        # self.assertEquals(response.context['title'], 'All groups')

    def test_anonymous_group(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 403)

        # This is temporary. We should test this logic in new tests
        # self.assertNotContains(response, self.bookGroup.name)
        # self.assertNotContains(response, self.bookGroup.url_name)
        # self.assertNotContains(response, 'booki group description')
        # self.assertNotContains(response, 'Members: 1')
        # self.assertNotContains(response, 'Books: 0')