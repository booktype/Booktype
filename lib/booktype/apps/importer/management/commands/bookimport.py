# This file is part of Booktype.
# Copyright (c) 2013 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

from booktype.utils.misc import import_book_from_file

class Command(BaseCommand):
    args = "<epub file> [, <epub file>, ...]"
    help = "Imports one or many books from epub files."

    option_list = BaseCommand.option_list + (
        make_option('--owner',
                    action='store',
                    dest='owner',
                    default='booki',
                    help='Who is owner of the imported book.'),
        
        make_option('--new-book-title',
                    action='store',
                    dest='new_book_title',
                    default=None,
                    help='Title of the new book.'),

        make_option('--new-book-url',
                    action='store',
                    dest='new_book_url',
                    default=None,
                    help='URL name of the new book.'),

        )

    requires_model_validation = False

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError("You must specify at least one booki-zip filename.")

        try:
            user = User.objects.get(username=options['owner'])
        except User.DoesNotExist:
            raise CommandError('User "%s" does not exist. Can not finish import.' % options['owner'])

        for fileName in args:
            try:
                extraOptions = {}

                if options['new_book_title']:
                    extraOptions['book_title'] = options['new_book_title']

                if options['new_book_url']:
                    extraOptions['book_url'] = options['new_book_url']

                import_book_from_file(fileName, user, **extraOptions)
            except IOError:
                raise CommandError('File "%s" does not exist. Can not finish import.' % fileName)
            else:
                if options['verbosity'] in ['1', '2']:
                    print 'EPUB "%s" file successfully imported.' % fileName
                
        
