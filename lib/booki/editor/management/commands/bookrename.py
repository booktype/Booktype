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

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from booki.editor import models
from booktype.utils.book import rename_book


class Command(BaseCommand):
    help = "Rename book."
    requires_model_validation = False
    BOOK_NAME = '<book name>'

    def add_arguments(self, parser):
        parser.add_argument(self.BOOK_NAME, nargs=1, type=str)
        parser.add_argument('--owner',
                            action='store',
                            dest='owner',
                            default=None,
                            help='Set new owner of the book.')

        parser.add_argument('--new-book-title',
                            action='store',
                            dest='new_book_title',
                            default=None,
                            help='Set new book title.')

        parser.add_argument('--new-book-url',
                            action='store',
                            dest='new_book_url',
                            default=None,
                            help='Set new book url name.')

    def handle(self, *args, **options):
        book_name = options[self.BOOK_NAME][0]

        if not book_name:
            raise CommandError("You must specify book name.")

        try:
            book = models.Book.objects.get(url_title__iexact=book_name)
        except models.Book.DoesNotExist:
            raise CommandError('Book "%s" does not exist.' % book_name)

        if options['new_book_title']:
            book.title = options['new_book_title']

        if options['new_book_url']:
            rename_book(book,  book.title, options['new_book_url'])

        if options['owner']:
            try:
                user = User.objects.get(username=options['owner'])
            except User.DoesNotExist:
                raise CommandError('User "%s" does not exist. Can not finish import.' % options['owner'])

            book.owner = user

        book.save()
            
