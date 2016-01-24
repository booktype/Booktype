# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

from django.core.exceptions import PermissionDenied
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from django.utils import feedgenerator
from django.contrib.auth.models import User

from booki.editor import models

from booktype.apps.core.views import get_security_for_book


class BookFeedRSS(Feed):
    """
    This represents RSS feed for a book.
    """

    def __init__(self, *args, **kwargs):
        super(BookFeedRSS, self).__init__(*args, **kwargs)

        self.security = None

    def check_permissions(self, request, *args, **kwargs):
        if not self.security.has_perm("reader.can_view_book_info"):
            raise PermissionDenied

    def get_object(self, request, bookid):
        book = get_object_or_404(models.Book, url_title=bookid)
        self.security = get_security_for_book(request.user, book)
        self.check_permissions(request)

        return book

    def title(self, obj):
        return obj.title

    def link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return obj.title

    def items(self, obj):
        return models.ChapterHistory.objects.filter(chapter__book=obj.id).order_by('-modified')[:50]

    def item_title(self, item):
        return item.chapter.title

    def item_description(self, item):
        return item.content

    def item_link(self, item):
        return item.chapter.get_absolute_url()

    def item_author_name(self, item):
        return item.user.first_name

    def item_author_email(self, item):
        return item.user.email

    def item_author_link(self, item):
        return '/accounts/%s/' % item.user.username

    def item_pubdate(self, item):
        return item.modified


class BookFeedAtom(BookFeedRSS):
    """
    This represents Atom feed for a book.
    """

    feed_type = feedgenerator.Atom1Feed


class ChapterFeedRSS(BookFeedRSS):
    """
    This represents RSS feed for a chapter.
    """

    def get_object(self, request, bookid, chapterid):
        super(ChapterFeedRSS, self).get_object(request, bookid)
        return get_object_or_404(models.Chapter, book__url_title=bookid, url_title=chapterid)

    def title(self, obj):
        return obj.title

    def link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return obj.title

    def items(self, obj):
        return models.ChapterHistory.objects.filter(chapter=obj.id).order_by('-modified')[:50]

    def item_title(self, item):
        return item.chapter.title

    def item_description(self, item):
        return item.content

    def item_link(self, item):
        return item.chapter.get_absolute_url()

    def item_author_name(self, item):
        return item.user.first_name

    def item_author_email(self, item):
        return item.user.email

    def item_author_link(self, item):
        return '/accounts/%s/' % item.user.username

    def item_pubdate(self, item):
        return item.modified


class ChapterFeedAtom(ChapterFeedRSS):
    """
    This represents Atom feed for a chapter.
    """

    feed_type = feedgenerator.Atom1Feed


class UserFeedRSS(Feed):
    """
    This represents RSS feed for a user.
    """

    def get_object(self, request, userid):
        return get_object_or_404(User, username=userid)

    def title(self, obj):
        return obj.username or obj.first_name

    def link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return obj.username or obj.first_name

    def items(self, obj):
        return models.ChapterHistory.objects.filter(user=obj.id, chapter__book__hidden=False).order_by('-modified')[:50]

    def item_title(self, item):
        return item.chapter.title

    def item_description(self, item):
        return item.content

    def item_link(self, item):
        return item.chapter.get_absolute_url()

    def item_author_name(self, item):
        return item.user.first_name

    def item_author_email(self, item):
        return item.user.email

    def item_author_link(self, item):
        return '/accounts/%s/' % item.user.username

    def item_pubdate(self, item):
        return item.modified


class UserFeedAtom(UserFeedRSS):
    """
    This represents Atom feed for a user.
    """

    feed_type = feedgenerator.Atom1Feed
