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

from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Used to create a user"

    option_list = BaseCommand.option_list + (
        make_option('--username', dest='username', default=None,
            help='Specifies the username for the superuser.'),

        make_option('--email', dest='email', default=None,
            help='Specifies the email address for the user.'),

        make_option('--fullname', dest='fullname', default=None,
            help='Specifies the fullname for the user.'),

        make_option('--password', dest='password', default=None,
            help='Specifies the password address for the user.'),

        make_option('--is-superuser', action='store_true',  dest='is_superuser', 
                    default=False, help='User has superpowers.'),

        )

    requires_model_validation = False

    def handle(self, *args, **options):
        username = options.get('username', None)
        email = options.get('email', None)
        password = options.get('password', None)
        fullname = options.get('fullname', None)

        if not username or not email or not password or not fullname:
            raise CommandError("You must specify all the arguments.")

        try:
            if options.get('is_superuser'):
                user = User.objects.create_superuser(username, email, password)
            else:
                user = User.objects.create_user(username, email, password)
        
            user.first_name = fullname
            user.save()

            from booki.account.models import UserProfile
            user_profile = UserProfile(user = user)
            user_profile.save()
        except:
            raise CommandError("Could not create the user.")


