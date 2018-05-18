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

from django.core.management.base import BaseCommand

from django.conf import settings


class Command(BaseCommand):
    help = "List all user defined configuration variables."
    requires_model_validation = False

    def add_arguments(self, parser):
        parser.add_argument('--values',
                            action='store_true',
                            dest='values',
                            default=False,
                            help='Show variable values.')

    def handle(self, *args, **options):
        if not hasattr(settings, 'BOOKTYPE_CONFIG'):
            self.stderr.write('Does not have BOOKTYPE_CONFIG in settings.py file.')
            return False

        for name in settings.BOOKTYPE_CONFIG.iterkeys():
            s = name

            if options['values']:
                value = settings.BOOKTYPE_CONFIG[name]

                s += ' = '

                if type(value) == type(' '):
                    s += '"%s"' % value
                elif type(value) == type(u' '):
                    s += '"%s"' % value.encode('utf8')
                else:
                    # this part could create problems
                    s += str(value)

            s += "\n"

            self.stdout.write(s)
