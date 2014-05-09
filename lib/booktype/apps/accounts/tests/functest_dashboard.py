# This file is part of Booktype.
# Copyright (c) 2014 Helmy Giacoman <helmy.giacoman@sourcefabric.org>
#
# Booktype is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Booktype is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Booktype.  If not, see <http://www.gnu.org/licenses/>.

from django.test import TestCase
from django.core.urlresolvers import reverse

from booktype.apps.core.tests.factory_models import UserFactory, BookFactory, BookVersionFactory
from booktype.apps.core.tests.factory_models import ChapterFactory, BookHistoryFactory
from booktype.apps.core.tests.factory_models import PLAIN_USER_PASSWORD

class DashboardTest(TestCase):
    """
    Tests Dashboard page as logged in and as anonymous user
    """

    def setUp(self):
        self.book = BookFactory()
        self.book.version = BookVersionFactory(book=self.book) # TODO: improve this
        self.book.save()
        self.user_1 = self.book.owner
        
        # need two users to be able to test collaboration within a book
        self.user_2 = UserFactory()

        # setup book content
        chapter_1 = ChapterFactory(book=self.book, version=self.book.version)
        chapter_2 = ChapterFactory(book=self.book, version=self.book.version)

        # setup content for user two in same book
        # call this "Contribution"
        book_history = BookHistoryFactory(
            book=self.book,
            user=self.user_2,
            chapter=chapter_2
        )