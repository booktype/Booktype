# -*- coding: utf-8 -*-
import os
from distutils.dir_util import copy_tree

import booktype
from django.utils.six.moves import input
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Copy the files for a specified theme from skeleton to a booktype instance'

    def add_arguments(self, parser):
        parser.add_argument('<theme_name theme_name ...>', nargs=1, type=str)
        parser.add_argument('--noinput',
                            action='store_false',
                            dest='interactive',
                            default=True,
                            help='Tells Command to NOT prompt the user for input of any kind')

    def __init__(self):
        super(Command, self).__init__()
        self.booktype_source = os.path.dirname(booktype.__file__)

    def handle(self, *args, **options):
        if options.get('interactive'):
            msg = (
                "\nThis will reset your theme files with the ones coming from Booktype"
                "\nPlease confirm that you want to proceed with this action? "
                "(yes/no): ")

            confirm = input(msg)

            while True:
                if confirm not in ('yes', 'no'):
                    confirm = input('Please enter either "yes" or "no": ')
                    continue
                if confirm == 'yes':
                    self.reset_themes(options['<theme_name theme_name ...>'])
                else:
                    self.stdout.write('No action taken. Good bye!')
                break
        else:
            self.reset_themes(options['<theme_name theme_name ...>'])

    def theme_path(self, theme_name):
        return '{}/skeleton/themes/{}'.format(self.booktype_source, theme_name)

    def reset_themes(self, args):
        for theme_name in args:

            if os.path.exists(self.theme_path(theme_name)):
                self.stdout.write('Reseting `%s` theme' % theme_name)
                self.copy_theme(theme_name)
                self.stdout.write('...done!')
            else:
                self.stdout.write('Theme with name `%s` does not exist.' % theme_name)

    def copy_theme(self, theme_name):

        theme_path = self.theme_path(theme_name)
        destination = '{}/themes/{}'.format(settings.BOOKTYPE_ROOT, theme_name)
        try:
            copy_tree(theme_path, destination)
        except OSError as err:
            raise CommandError('Error while copying %s' % err)
