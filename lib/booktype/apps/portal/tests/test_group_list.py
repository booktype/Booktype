from rest_framework import status

from django.core.urlresolvers import reverse

from booktype.tests import TestCase
from booktype.tests.factory_models import UserFactory, BookGroupFactory


class GroupListTest(TestCase):

    def setUp(self):
        super(GroupListTest, self).setUp()

        self.dispatcher = reverse('portal:list_groups')
        self.user = UserFactory()

        # setup for groups
        self.bookGroup = BookGroupFactory(members=(0, 1))

    def tearDown(self):
        self.user.delete()

    def test_accounts(self):
        response = self.client.get(self.dispatcher)

        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_group(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
