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
from optparse import make_option
from django.contrib.auth.models import User

from booki.editor import common
from booki.editor import models
from django.conf import settings

class Command(BaseCommand):
    args = "<book name>"
    help = "Rename book."

    option_list = BaseCommand.option_list + (
        make_option('--owner',
                    action='store',
                    dest='owner',
                    default=None,
                    help='Set new owner of the book.'),
        
        make_option('--new-book-title',
                    action='store',
                    dest='new_book_title',
                    default=None,
                    help='Set new book title.'),

        make_option('--new-book-url',
                    action='store',
                    dest='new_book_url',
                    default=None,
                    help='Set new book url name.'),

        )

    requires_model_validation = False

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("You must specify book name.")

        try:
            book = models.Book.objects.get(url_title__iexact=args[0])
        except models.Book.DoesNotExist:
            raise CommandError('Book "%s" does not exist.' % args[0])

        if options['new_book_title']:
            book.title = options['new_book_title']

        if options['new_book_url']:
            import os
            os.rename('%s/books/%s' % (settings.DATA_ROOT, book.url_title), '%s/books/%s' % (settings.DATA_ROOT, options['new_book_url']))

            book.url_title = options['new_book_url']

            # TODO: test this
            n = len(settings.DATA_ROOT)+len('books/')+1

            for attachment in models.Attachment.objects.filter(version__book=book):
                name = attachment.attachment.name
                j = name[n:].find('/')
                newName = '%s/books/%s%s' % (settings.DATA_ROOT, book.url_title, name[n:][j:])

                attachment.attachment.name = newName
                attachment.save()

        if options['owner']:
            try:
                user = User.objects.get(username=options['owner'])
            except User.DoesNotExist:
                raise CommandError('User "%s" does not exist. Can not finish import.' % options['owner'])

            book.owner = user

        book.save()
            
