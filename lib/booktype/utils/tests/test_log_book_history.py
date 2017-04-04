# -*- coding: utf-8 -*-
# NOTE: for now this is intended to test all methods in
# log.py in old booki app. In near future we should move log.py
# into the new booktype app

from django.test import TestCase
from booktype.tests.factory_models import BookFactory, BookVersionFactory, ChapterFactory, UserFactory
from booki.utils.log import logBookHistory
from booki.editor.models import BookHistory


class LogBookHistoryTestCase(TestCase):
    """
    Tests all methods in log.py module
    """

    def setUp(self):
        super(LogBookHistoryTestCase, self).setUp()

        self.book = BookFactory()
        self.book_version = BookVersionFactory(book=self.book)
        self.chapter = ChapterFactory(book=self.book)
        self.user = UserFactory()

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
