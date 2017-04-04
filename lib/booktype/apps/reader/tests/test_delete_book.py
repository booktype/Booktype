from rest_framework import status

from django.core.urlresolvers import reverse

from booktype.tests import TestCase
from booktype.tests.factory_models import BookFactory, BookVersionFactory, UserFactory, PLAIN_USER_PASSWORD


class DeleteBookTest(TestCase):
    def setUp(self):
        super(DeleteBookTest, self).setUp()

        self.book = BookFactory()
        self.book.version = BookVersionFactory(book=self.book)
        self.book.save()
        self.user = self.book.owner

        self.dispatcher = reverse('reader:delete_book', args=[self.book.url_title])

    def test_as_not_owner(self):
        # first login as other user not owner or admin
        other_user = UserFactory()

        self.client.login(
            username=other_user.username,
            password=PLAIN_USER_PASSWORD
        )

        # ---- POST method -----
        response = self.client.post(self.dispatcher, dict(title=self.book.title))

        # response status code should be 200
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        # template must be the delete_error_template, because user doesn't
        # have enough rights to delete the book
        self.assertTemplateUsed(response, "reader/book_delete_error.html")

    def test_as_book_owner(self):
        # first login as book owner user
        self.client.login(
            username=self.user.username,
            password=PLAIN_USER_PASSWORD
        )

        # ---- GET method ----
        response = self.client.get(self.dispatcher)

        # response status code should be 200
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        # check if returning the right template
        self.assertTemplateUsed(response, "reader/book_delete.html")

        # check if content in response
        self.assertContains(response, 'Delete Book')

        # ---- POST method -----
        response = self.client.post(self.dispatcher, dict(title=self.book.title))

        # response status code should be 200
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        # in post method, the template must have changed
        self.assertTemplateUsed(response, "reader/book_delete_redirect.html")

        # check if book registry is not in database anymore
        Book = self.book.__class__
        self.assertRaises(Book.DoesNotExist, Book.objects.get, pk=self.book.id)
