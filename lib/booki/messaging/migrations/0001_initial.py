# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import booki.messaging.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Endpoint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('syntax', models.CharField(unique=True, max_length=2500, verbose_name='syntax')),
            ],
            options={
                'verbose_name': 'Endpoint',
                'verbose_name_plural': 'Endpoints',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EndpointConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('notification_filter', models.CharField(max_length=2500, verbose_name='notification filter', blank=True)),
            ],
            options={
                'verbose_name': 'Endpoint config',
                'verbose_name_plural': 'Endpoint configs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Following',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('follower', models.ForeignKey(related_name=b'follower', verbose_name='follower', to='messaging.Endpoint')),
                ('target', models.ForeignKey(related_name=b'target', verbose_name='target', to='messaging.Endpoint')),
            ],
            options={
                'verbose_name': 'Following',
                'verbose_name_plural': 'Followings',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now=True, verbose_name='timestamp')),
                ('content', models.TextField(verbose_name='content')),
                ('attachment', models.FileField(upload_to=booki.messaging.models.uploadAttachmentTo, max_length=2500, verbose_name='attachment')),
                ('snippet', models.TextField(verbose_name='snippet')),
                ('context_url', models.TextField(verbose_name='context')),
                ('sender', models.ForeignKey(verbose_name='sender', to='messaging.Endpoint')),
            ],
            options={
                'verbose_name': 'Post',
                'verbose_name_plural': 'Posts',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PostAppearance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(verbose_name='timestamp')),
                ('endpoint', models.ForeignKey(verbose_name='endpoint', to='messaging.Endpoint')),
                ('post', models.ForeignKey(verbose_name='post', to='messaging.Post')),
            ],
            options={
                'verbose_name': 'Post appearance',
                'verbose_name_plural': 'Post appearances',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='endpoint',
            name='config',
            field=models.ForeignKey(null=True, blank=True, to='messaging.EndpointConfig', unique=True),
            preserve_default=True,
        ),
    ]
