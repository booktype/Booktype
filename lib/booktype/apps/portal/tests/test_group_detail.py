from rest_framework import status

from django.core.urlresolvers import reverse

from booktype.tests import TestCase
from booktype.tests.factory_models import UserFactory, BookFactory


class GroupDetailTest(TestCase):
    def setUp(self):
        super(GroupDetailTest, self).setUp()

        self.user = UserFactory()

        # setup for books
        self.book = BookFactory()

        # setup for groups
        self.bookGroup = self.book.group

        # add members
        self.bookGroup.members.add(1)

    def tearDown(self):
        self.user.delete()

    def test_accounts(self):
        self.dispatcher = reverse('portal:group', kwargs={'groupid': self.bookGroup.url_name})
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_group(self):
        self.dispatcher = reverse('portal:group', kwargs={'groupid': self.bookGroup.url_name})
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
