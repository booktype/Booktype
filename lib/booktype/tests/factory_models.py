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

import factory

from faker import Faker

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from booki.editor.models import Book, BookVersion, Chapter
from booki.editor.models import BookStatus, BookToc, BookHistory
from booki.editor.models import BookiGroup

from booktype.apps.account.models import UserProfile
from booktype.apps.core.models import Permission, Role, BookRole

PLAIN_USER_PASSWORD = 'top_secret'

fake = Faker()


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'user%d' % n)
    email = factory.LazyAttribute(lambda obj: '%s@test.sourcefabric.org' % obj.username)
    password = make_password(PLAIN_USER_PASSWORD)


class UserProfileFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserProfile

    description = 'description'
    user = factory.SubFactory(UserFactory, profile=None)


class BookGroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = BookiGroup

    name = factory.Sequence(lambda n: 'group name %d' % n)
    url_name = factory.Sequence(lambda n: 'url-group-name-%d' % n)
    description = 'booki group description'
    owner = factory.SubFactory(UserFactory)

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for member in extracted:
                self.members.add(member)


class BookFactory(factory.DjangoModelFactory):
    class Meta:
        model = Book

    url_title = factory.Sequence(lambda n: 'first-book-test-bla-foo-%d' % n)
    title = factory.Sequence(lambda n: 'First Book Test Bla Foo %d' % n)
    group = factory.SubFactory(BookGroupFactory)
    owner = factory.SelfAttribute('group.owner')


class BookStatusFactory(factory.DjangoModelFactory):
    class Meta:
        model = BookStatus

    book = factory.SubFactory(BookFactory)
    name = factory.Sequence(lambda n: 'name %d' % n)
    weight = factory.Sequence(lambda n: n)


class BookVersionFactory(factory.DjangoModelFactory):
    class Meta:
        model = BookVersion

    book = factory.SubFactory(BookFactory)
    major = 1
    minor = 0


class ChapterFactory(factory.DjangoModelFactory):
    class Meta:
        model = Chapter

    version = factory.SubFactory(BookVersionFactory)
    book = factory.SubFactory(BookFactory)

    url_title = factory.Sequence(lambda n: 'chapter-%d' % n)
    title = factory.Sequence(lambda n: 'Chapter %d' % n)
    status = factory.SubFactory(BookStatusFactory)
    content = fake.paragraph(4)


class BookTocFactory(factory.DjangoModelFactory):
    class Meta:
        model = BookToc

    @classmethod
    def create_toc(cls, book, book_version, chapter):
        # create section item
        cls(
            book=book,
            version=book_version,
            name='Section One',
            chapter=None,
            weight=0,
            typeof=0
        )

        # create chapter item
        cls(
            book=book,
            version=book_version,
            name='Chapter 1',
            chapter=chapter,
            weight=1,
            typeof=1
        )


class BookHistoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = BookHistory

    book = factory.SubFactory(BookFactory)
    user = factory.SubFactory(UserFactory)


class PermissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Permission

    description = factory.Sequence(lambda n: 'Permission %d' % n)


class RoleFactory(factory.DjangoModelFactory):
    class Meta:
        model = Role

    name = factory.Sequence(lambda n: 'Role %d' % n)


class BookRoleFactory(factory.DjangoModelFactory):
    class Meta:
        model = BookRole

    book = factory.SubFactory(BookFactory)
    role = factory.SubFactory(RoleFactory)
