from django.core.management.base import BaseCommand, NoArgsCommand
from booki.editor import common

class Command(BaseCommand):
    help = "Imports book from book-zip."

    requires_model_validation = False

    def handle(self, *args, **options):
        from django.contrib.auth.models import User

        user = User.objects.get(username="booki")

        for fileName in args:
            common.importBookFromFileTheOldWay(user, fileName)
        
