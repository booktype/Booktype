# -*- coding: utf-8 -*-
# NOTE: for now this is intended to test all methods in
# log.py in old booki app. In near future we should move log.py
# into the new booktype app

from django.test import TestCase
from booktype.tests.factory_models import BookFactory, BookVersionFactory, ChapterFactory, UserFactory
from booki.utils.log import logChapterHistory
from booki.editor.models import ChapterHistory


class LogChapterHistoryTestCase(TestCase):
    """
    Tests all methods in log.py module
    """

    def setUp(self):
        super(LogChapterHistoryTestCase, self).setUp()

        self.book = BookFactory()
        self.book_version = BookVersionFactory(book=self.book)
        self.chapter = ChapterFactory(book=self.book)
        self.user = UserFactory()

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
