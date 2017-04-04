from rest_framework import status

from django.core.urlresolvers import reverse

from booktype.tests import TestCase
from booktype.tests.factory_models import BookFactory, BookVersionFactory, PLAIN_USER_PASSWORD


class EditBookInfoTest(TestCase):
    def setUp(self):
        super(EditBookInfoTest, self).setUp()

        self.book = BookFactory()
        self.book.version = BookVersionFactory(book=self.book)
        self.book.save()
        self.user = self.book.owner

        self.dispatcher = reverse('reader:edit_info_book', args=[self.book.url_title])

    def reload_from_db(self, obj):
        """
        Returns reloaded attributes of a given object from the database
        """
        return obj.__class__.objects.get(pk=obj.id)

    def test_anon_user(self):
        response = self.client.get(self.dispatcher)

        # response status code should be 302, you're not logged in
        self.assertEquals(response.status_code, status.HTTP_302_FOUND)

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
        self.assertTemplateUsed(response, "reader/book_info_edit.html")

        # check if book object is in context
        self.assertTrue('book' in response.context)

        # check some content in response
        self.assertContains(response, 'Book description')
        self.assertContains(response, 'Book image')

        # ---- POST method -----
        new_description = 'lorem ipsum testing'
        response = self.client.post(self.dispatcher, dict(description=new_description))

        # response status code should be 200
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        # test if description has been updated correctly
        updated_book = self.reload_from_db(self.book)
        self.assertTrue(updated_book.description == new_description)

        # in post method, the template must have changed
        self.assertTemplateUsed(response, "reader/book_info_edit_redirect.html")
