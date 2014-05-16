from django.test import TestCase
from django.core.urlresolvers import reverse

from booktype.apps.core.tests.factory_models import UserFactory, BookFactory


class GrouppageTest(TestCase):
    def setUp(self):
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
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['title'], 'Group used')

    def test_group(self):
        self.dispatcher = reverse('portal:group', kwargs={'groupid': self.bookGroup.url_name})
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)

        self.assertContains(response, self.bookGroup.name)
        self.assertContains(response, self.bookGroup.description)
        self.assertContains(response, 'Members: 1')
        self.assertContains(response, 'Books: ')