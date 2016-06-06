# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('editor', '0006_auto_20150913_1528'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comment_id', models.CharField(unique=True, max_length=50, verbose_name=b'cid')),
                ('author', models.CharField(default=b'', max_length=50, verbose_name=b'author')),
                ('date', models.DateTimeField(verbose_name=b'date')),
                ('content', models.TextField(default=b'', verbose_name=b'content')),
                ('text', models.TextField(default=b'', verbose_name=b'text')),
                ('status', models.PositiveSmallIntegerField(default=0, verbose_name=b'status')),
                ('state', models.PositiveSmallIntegerField(default=0, verbose_name=b'state')),
                ('is_imported', models.BooleanField(default=False, verbose_name=b'is_imported')),
                ('stored_reference', models.BooleanField(default=False)),
                ('chapter', models.ForeignKey(verbose_name=b'chapter', to='editor.Chapter')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='edit.Comment', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
