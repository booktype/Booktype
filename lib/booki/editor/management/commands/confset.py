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

from django.conf import settings

from booki.utils import config
from booki.utils.json_wrapper import json

class Command(BaseCommand):
    args = "<name> <value>"
    help = "Set value for configuration variable."

    option_list = BaseCommand.option_list + (
        make_option('--as_json',
                    action='store_true',
                    dest='as_json',
                    default=False,
                    help='Value is defined as JSON encoded string.'),

        make_option('--integer',
                    action='store_true',
                    dest='integer',
                    default=False,
                    help='Value is a integer.'),

        make_option('--float',
                    action='store_true',
                    dest='float',
                    default=False,
                    help='Value is a float.'),

        make_option('--append',
                    action='store_true',
                    dest='append',
                    default=False,
                    help='Append value to the end of list.'),

        make_option('--remove',
                    action='store_true',
                    dest='remove',
                    default=False,
                    help='Remove value from the list.'),
        )

    requires_model_validation = False

    def handle(self, *args, **options):
        if not hasattr(settings, 'BOOKTYPE_CONFIG'):
            raise CommandError('Does not have BOOKTYPE_CONFIG in settings.py file.')

        if len(args) != 2:
            raise CommandError("You must specify variable name and value.")

        key = args[0]
        value = args[1]

        if options['integer']:
            try:
                value = int(value)
            except ValueError:
                raise CommandError("I don't think this %s is a number!" % value)

        if options['float']:
            try:
                value = float(value)
            except ValueError:
                raise CommandError("I don't think this %s is a number!" % value)
                

        if options['as_json']:
            try:
                value = json.loads(value)
            except ValueError:
                raise CommandError("Not a valid JSON string.")

        if options['append']:
            # ovo neshto ne radi sa as_jsonom
            lst = config.getConfiguration(key, [])

            if type(lst) == type([]):
                lst.append(value)
                config.setConfiguration(key, lst)
            else:
                raise CommandError("Can not append to something that is not a list")
        elif options['remove']:
            lst = config.getConfiguration(key, [])

            if type(lst) == type([]):
                try:
                    lst.remove(value)
                except ValueError:
                    raise CommandError("I can't see it!")

                config.setConfiguration(key, lst)
            else:
                raise CommandError("Can not append to something that is not a list")
        else:
            config.setConfiguration(key, value)
            
        try:
            config.saveConfiguration()
        except config.ConfigurationError:
            raise CommandError("Could not save the file.")

