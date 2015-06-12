# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserTheme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('custom', models.TextField(default=b'{}', verbose_name=b'custom')),
                ('active', models.CharField(default=b'custom', max_length=32, verbose_name=b'active')),
                ('book', models.ForeignKey(verbose_name=b'book', to='editor.Book')),
                ('owner', models.ForeignKey(default=None, verbose_name=b'owner', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
