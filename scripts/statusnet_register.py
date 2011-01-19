from django.contrib.auth.models import User
from booki.statusnet.models import createStatusAccount


IGNORE_USERS = ['booki', 'aerkalov', 'adam']

for user in User.objects.all().order_by('username'):
    if user.username not in IGNORE_USERS:
        print ' >> ', user.username, user.email, user.first_name
        #createStatusAccount(user.username, 'bookibooki', user.email, user.first_name
