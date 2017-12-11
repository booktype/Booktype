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

from rest_framework import status

from django.core.urlresolvers import reverse

from booktype.tests import TestCase
from booktype.tests.factory_models import (UserFactory, BookFactory, BookVersionFactory, ChapterFactory,
                                           BookHistoryFactory, PLAIN_USER_PASSWORD)


class DashboardTest(TestCase):
    """
    Tests Dashboard page as logged in and as anonymous user
    """

    def setUp(self):
        super(DashboardTest, self).setUp()

        self.book = BookFactory()
        self.book.version = BookVersionFactory(book=self.book)  # TODO: improve this
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

        self.dispatcher = reverse('accounts:view_profile', args=[self.user_1.username])

    def _test_base_details(self, response):
        # context should contain all below variables
        context_vars = [
            'books',
            'books_collaborating',
            'licenses',
            'groups',
            'recent_activity'
        ]

        for var in context_vars:
            self.assertTrue(var in response.context)

    def test_as_anonymous(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_as_account_owner(self):
        self.client.login(
            username=self.user_2.username,
            password=PLAIN_USER_PASSWORD
        )

        own_dispatcher = reverse('accounts:view_profile', args=[self.user_2.username])
        response = self.client.get(own_dispatcher)
        context = response.context

        # as authenticated user, test basic details
        self._test_base_details(response)

        # response should contain next things
        self.assertContains(response, 'My Dashboard')
        self.assertContains(response, 'Log out')
        self.assertContains(response, 'Participating Books')
        self.assertContains(response, '#createBookModal')
        self.assertContains(response, 'id="user-settings"')

        # this user is collaborating with other books
        self.assertTrue(len(context['books_collaborating']) >= 1)
        self.assertTrue(self.book in context['books_collaborating'])

        # this user has no groups belonging
        self.assertTrue(len(context['groups']) == 0)

    def test_other_user_dashboard(self):
        self.client.login(
            username=self.user_2.username,
            password=PLAIN_USER_PASSWORD
        )

        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN
                          )
