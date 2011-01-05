from django.core.management.base import BaseCommand, NoArgsCommand
from optparse import make_option
from booki.editor import common

class Command(BaseCommand):
    help = "Imports book from book-zip."

    option_list = BaseCommand.option_list + (
        make_option('--user',
            action='store',
            dest='user',
            default='booki',
            help='Who is owner of the book'),)

    requires_model_validation = False

    def handle(self, *args, **options):
        from django.contrib.auth.models import User

        user = User.objects.get(username=options['user'])

        for fileName in args:
            common.importBookFromFile(user, fileName, createTOC=True)
        
