# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPassword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('secretcode', models.CharField(max_length=30, verbose_name='secretcode')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='created')),
                ('remote_useragent', models.CharField(default=b'', max_length=1000, verbose_name='remote useragent', blank=True)),
                ('remote_addr', models.CharField(default=b'', max_length=1000, verbose_name='remote addr', blank=True)),
                ('remote_host', models.CharField(default=b'', max_length=1000, verbose_name='remote host', blank=True)),
                ('user', models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mood', models.CharField(default=b'', max_length=1000, verbose_name='mood', blank=True)),
                ('image', models.ImageField(upload_to=b'profile_images/', null=True, verbose_name='image', blank=True)),
                ('description', models.CharField(default=b'', max_length=2500, verbose_name='description')),
                ('user', models.ForeignKey(related_name=b'profile', verbose_name='user', to=settings.AUTH_USER_MODEL, unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
