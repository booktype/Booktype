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

import json

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Get value for configuration variable."
    requires_model_validation = False

    def add_arguments(self, parser):
        parser.add_argument("<key>", nargs=1, type=str)
        parser.add_argument('--as_json',
                            action='store_true',
                            dest='as_json',
                            default=False,
                            help='Value is defined as JSON encoded string.')

    def handle(self, *args, **options):
        if not hasattr(settings, 'BOOKTYPE_CONFIG'):
            raise CommandError('Does not have BOOKTYPE_CONFIG in settings.py file.')

        if not options["<key>"][0]:
            raise CommandError("You must specify variable name")

        if not settings.BOOKTYPE_CONFIG.has_key(options["<key>"][0]):
            raise CommandError("There is no such variable.")

        value = settings.BOOKTYPE_CONFIG[options["<key>"][0]]

        if options['as_json']:
            value = json.dumps(value)

        self.stdout.write(str(value) + "\n")
