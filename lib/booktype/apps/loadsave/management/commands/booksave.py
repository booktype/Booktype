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

import shutil
import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from booki.editor import common, models


class Command(BaseCommand):
    help = "Export book content as EPUB file."
    args = "<book name>"

    option_list = BaseCommand.option_list + (
        make_option('--book-version',
            action='store',
            dest='book_version',
            default=None,
            help='Book version, e.g.'),

        make_option('--output',
            action='store',
            dest='output_name',
            default=None,
            help='Output filename or -- for STDOUT, e.g. my_book.zip.'),
        )

    requires_model_validation = False

    def handle(self, *args, **options):

        if len(args) == 0:
            raise CommandError("You must specify book name!")

        try:
            book = models.Book.objects.get(url_title__iexact=args[0])
        except models.Book.DoesNotExist:
            raise CommandError('Book "%s" does not exist.' % args[0])

        book_version = book.get_version(options['book_version'])

        if not book_version:
            raise CommandError('Book version %s does not exist.' % options['book_version'])

        from booktype.utils.misc import export_book

        fileName = '%s.epub' % book.url_title
        if options['output_name']:
            fileName = options['output_name']

        export_book(fileName, book_version)

        if options['verbosity'] in ['1', '2']:
            print 'Book successfully exported into "%s" file.' % fileName

        
