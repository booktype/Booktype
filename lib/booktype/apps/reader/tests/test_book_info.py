from rest_framework import status

from django.core.urlresolvers import reverse

from booktype.tests import TestCase
from booktype.tests.factory_models import BookFactory, BookVersionFactory, PLAIN_USER_PASSWORD


class BookInfoTest(TestCase):

    def setUp(self):
        super(BookInfoTest, self).setUp()

        self.book = BookFactory()
        self.book.version = BookVersionFactory(book=self.book)
        self.book.save()
        self.user = self.book.owner

        self.dispatcher = reverse('reader:infopage', args=[self.book.url_title])

        # list of variables to check in context
        self.vars_to_check = [
            'book_collaborators',
            'book_admins',
            'book_history',
            'book_group',
            'is_book_admin'
        ]

    def test_details_as_anonymous(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_details_as_owner_logged_in(self):
        # first login with book owner user
        self.client.login(
            username=self.user.username,
            password=PLAIN_USER_PASSWORD
        )

        response = self.client.get(self.dispatcher)

        # check status code
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        # check if context has been filled correctly
        for key in self.vars_to_check:
            self.assertTrue(key in response.context)

        # owner is also book admin, so this should be True
        self.assertEquals(response.context['is_book_admin'], True)

        # check admin actions available in response
        self.assertContains(response, 'Edit Book Info')
        self.assertContains(response, 'Delete Book')
