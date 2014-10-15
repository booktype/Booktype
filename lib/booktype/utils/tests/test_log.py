# -*- coding: utf-8 -*-
# NOTE: for now this is intended to test all methods in
# log.py in old booki app. In near future we should move log.py
# into the new booktype app

from django.test import TestCase
from booktype.apps.core.tests import factory_models
from booki.utils.log import logBookHistory, logChapterHistory
from booki.editor.models import BookHistory, ChapterHistory


class PermissionsUtilsTestCase(TestCase):
    """
    Tests all methods in log.py module
    """

    def setUp(self):
        self.book = factory_models.BookFactory()
        self.book_version = factory_models.BookVersionFactory(book=self.book)
        self.chapter = factory_models.ChapterFactory(book=self.book)
        self.user = factory_models.UserFactory()

    def test_log_book_history(self):
        history = logBookHistory(
            book=self.book,
            version=self.book_version,
            chapter=self.chapter,
            user=self.user
        )

        # check returned object
        self.assertTrue(
            isinstance(history, BookHistory),
            "Returned object should be instance of BookHistory"
        )

        # checl some values also
        self.assertEqual(history.book, self.book)
        self.assertEqual(history.chapter, self.chapter)

        # test with some bad values
        none_history = logBookHistory(
            book=self.book,
            version=self.book_version,
            chapter=self.chapter,
            user=''
        )

        # check returned values for bad params
        self.assertEqual(
            none_history,
            None,
            "It should return None in case of bad parameters"
        )

    def test_log_chapter_history(self):
        chapter_content = 'Test of log chapter history'
        history = logChapterHistory(
            chapter=self.chapter,
            user=self.user,
            revision=1,
            content=chapter_content
        )

        # check returned object
        self.assertTrue(
            isinstance(history, ChapterHistory),
            "Returned object should be instance of ChapterHistory"
        )

        # checl some values also
        self.assertEqual(history.chapter, self.chapter)
        self.assertEqual(history.content, chapter_content)
        self.assertEqual(history.revision, 1)

        # test with some bad values
        none_history = logChapterHistory(
            chapter=self.chapter,
            user=''
        )

        # check returned values for bad params
        self.assertEqual(
            none_history,
            None,
            "It should return None in case of bad parameters"
        )
