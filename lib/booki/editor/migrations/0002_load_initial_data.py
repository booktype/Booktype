# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.core.management import call_command

LICENSES_URL = [
    {'pk': 1, 'url': 'http://choosealicense.com/licenses/unlicense/'},
    {'pk': 2, 'url': 'http://choosealicense.com/licenses/mit/'},
    {'pk': 3, 'url': 'http://choosealicense.com/licenses/cc0/'},
    {'pk': 4, 'url': 'http://creativecommons.org/licenses/by/4.0/legalcode'},
    {'pk': 5, 'url': 'http://creativecommons.org/licenses/by-sa/4.0/legalcode'},
    {'pk': 6, 'url': 'http://creativecommons.org/licenses/by-nd/4.0/legalcode'},
    {'pk': 7, 'url': 'http://creativecommons.org/licenses/by-nc/4.0/legalcode'},
    {'pk': 8, 'url': 'http://creativecommons.org/licenses/by-nc-sa/4.0/legalcode'},
    {'pk': 9, 'url': 'http://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'},
    {'pk': 10, 'url': 'http://choosealicense.com/licenses/gpl-3.0/'},
    {'pk': 11, 'url': 'http://choosealicense.com/licenses/agpl-3.0/'},
    {'pk': 12, 'url': 'http://choosealicense.com/licenses/no-license/'}
]


def load_data(apps, schema_editor):
    Language = apps.get_model('editor', 'Language')  # noqa
    License = apps.get_model('editor', 'License')  # noqa

    # load initial fixtures
    if Language.objects.count() == 0:
        call_command('loaddata', 'languages.json')

    if License.objects.count() == 0:
        call_command('loaddata', 'documentation_licenses.json')

    # now fix the licenses urls
    for data in LICENSES_URL:
        try:
            license = License.objects.get(pk=data['pk'])
            license.url = data['url']
            license.save()
            print "Updating url '%s' to license '%s'" % (data['url'], license.name)
        except License.DoesNotExist:
            print "License with pk %s does not exist. Doing nothing" % data['pk']


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_data)
    ]
