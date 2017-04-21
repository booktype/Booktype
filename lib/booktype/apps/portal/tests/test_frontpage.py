from rest_framework import status

from django.core.urlresolvers import reverse

from booktype.tests import TestCase
from booktype.tests.factory_models import UserFactory, BookGroupFactory, BookFactory


class FrontpageTest(TestCase):

    def setUp(self):
        super(FrontpageTest, self).setUp()

        self.dispatcher = reverse('portal:frontpage')
        self.user = UserFactory()

        # setup for groups
        BookGroupFactory(members=(0, 1))

        # setup for books
        BookFactory()

    def tearDown(self):
        self.user.delete()

    def test_frontpage(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.context['title'], 'Home')

    def test_books(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertNotContains(response, 'book title')

    def test_people(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertNotContains(response, 'user_')

    def test_groups(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertNotContains(response, 'group name')
        self.assertNotContains(response, 'url_group_name')
        self.assertNotContains(response, 'booki group description')
        self.assertNotContains(response, 'Members: 1')
        self.assertNotContains(response, 'Books: ')
