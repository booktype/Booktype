from rest_framework import status

from django.core.urlresolvers import reverse

from booktype.tests import TestCase
from booktype.tests.factory_models import (BookFactory, BookVersionFactory, ChapterFactory, BookTocFactory,
                                           PLAIN_USER_PASSWORD)


class DraftChapterTest(TestCase):
    def setUp(self):
        super(DraftChapterTest, self).setUp()

        self.book = BookFactory()
        self.book.version = BookVersionFactory(book=self.book)
        self.book.save()
        self.user = self.book.owner

        self.chapter = ChapterFactory()
        self.dispatcher = reverse('reader:draft_chapter_page', args=[self.book.url_title])
        self.book_toc = BookTocFactory.create_toc(self.book, self.book.version, self.chapter)

        # list of variables to check in context
        self.vars_to_check = [
            'content',
            'toc_items',
            'book_version',
            'can_edit'
        ]

    def test_context_as_anon(self):
        response = self.client.get(self.dispatcher)

        # response status code should be 200
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_can_edit_logged_in(self):
        # first login as book owner user
        self.client.login(
            username=self.user.username,
            password=PLAIN_USER_PASSWORD
        )

        response = self.client.get(self.dispatcher)

        # as anonymous user you can't edit the book
        self.assertEquals(response.context['security'].can_edit(), True)
