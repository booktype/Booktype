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
import datetime

from django.conf import settings

now = datetime.datetime.now()

import os.path
import re


def getUsers():
    """Get users who registered today."""

    from django.contrib.auth.models import User

    return User.objects.filter(date_joined__year = now.year,
                               date_joined__month = now.month,
                               date_joined__day = now.day)

    return None

def getBooks():
    """Get books created today."""

    from booki.editor.models import Book

    return Book.objects.filter(created__year = now.year,
                               created__month = now.month,
                               created__day = now.day)
    
    return None
    
def getGroups():
    """Get groups created today."""

    from booki.editor.models import BookiGroup

    return BookiGroup.objects.filter(created__year = now.year,
                                     created__month = now.month,
                                     created__day = now.day)

    return None
                                         

def getHistory():
    from booki.editor.models import BookHistory
    from django.db.models import Count

    from booki.editor.models import Book

    history = []
    
    for books2 in BookHistory.objects.filter(modified__year = now.year,
                                             modified__month = now.month,
                                             modified__day = now.day).values('book').annotate(Count('book')).order_by("-book__count"):
        
        book = Book.objects.get(pk=books2['book'])
        
        history.append((book, [h.chapter_history for h in BookHistory.objects.filter(book__id=books2['book'],
                                                                                     chapter_history__isnull=False,
                                                                                     modified__year = now.year,
                                                                                     modified__month = now.month,
                                                                                     modified__day = now.day)]))

    return history

def getInfo():
    from django.contrib.auth.models import User
    from booki.editor.models import Book, Attachment, BookiGroup
    from django.db import connection

    numOfUsers = len(User.objects.all())
    numOfBooks = len(Book.objects.all())
    numOfGroups = len(BookiGroup.objects.all())

    attachmentsSize = 0
    for at in Attachment.objects.all():
        try:
            attachmentsSize += at.attachment.size
        except:
            pass

    cursor = connection.cursor()
    cursor.execute("SELECT pg_database_size(%s)", [settings.DATABASES['default']['NAME']]);
    databaseSize = cursor.fetchone()[0]

    return {'users_num': numOfUsers,
            'books_num': numOfBooks,
            'groups_num': numOfGroups,
            'attachments_size': attachmentsSize,
            'database_size': databaseSize}

def getChart():
    from booki.editor import models
    from django.db.models import Count

    hours = [0]*24
    max_num = 0

    for x in models.BookHistory.objects.filter(modified__year = now.year, modified__month = now.month, modified__day = now.day).extra({'modified': 'EXTRACT (HOUR FROM modified)'}).values('modified').annotate(count=Count('id')):
        cnt = x['count']

        hours[int(x['modified'])] = cnt

        if cnt > max_num: max_num = cnt        

    for x in range(len(hours)):
        try:
            hours[x] = int(float(hours[x])/float(max_num)*200.0)
        except ZeroDivisionError:
            hours[x] = 0

    return hours

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--send-email',
            action='store_true',
            dest='send_email',
            default=False,
            help='Send email to admin'),

        make_option('--days',
            action='store',
            dest='days',
            default=0,
            help='N days ago')
        )



    def handle(self, *args, **options):
        global now

        now = now - datetime.timedelta(days=int(options['days']))

        users = getUsers()
        books = getBooks()
        groups = getGroups()
        history = getHistory()
        info = getInfo()

        chart = getChart()

        try:
            BOOKTYPE_NAME = settings.BOOKI_NAME
        except AttributeError:
            BOOKTYPE_NAME = 'Booktype'

        # render result

        from django import template

        t = template.loader.get_template('booktype_daily_report.html')
        con = t.render(template.Context({"users": users,
                                         "books": books,
                                         "groups": groups,
                                         "history": history,
                                         "report_date": now,
                                         "info": info,
                                         "booki_name": BOOKTYPE_NAME,
                                         "site_url": settings.BOOKI_URL
                                         }))


        if options['send_email']:
            from django.core.mail import EmailMultiAlternatives

            try:
                REPORT_EMAIL_USER = settings.REPORT_EMAIL_USER
            except AttributeError:
                REPORT_EMAIL_USER = 'booktype@booktype.pro'

            emails = [em[1] for em in settings.ADMINS]

            subject = 'Daily report for %s (%s)' % (BOOKTYPE_NAME, now.strftime("%A %d %B %Y"))

            text_content = con
            html_content = con

            msg = EmailMultiAlternatives(subject, text_content, REPORT_EMAIL_USER, emails)
            msg.attach_alternative(html_content, "text/html")

            # Make graph
            import ImageFont, ImageDraw, Image
            
            from booki.editor import models as ed
            font = ImageFont.truetype("%s/management/commands/linear-by-braydon-fuller.otf" % os.path.dirname(ed.__file__), 12)
            
            text_size =  font.getsize("23")
            image = Image.new("RGB", (20+(7+text_size[0])*24, 200+2+12), (255, 255, 255))
            draw = ImageDraw.Draw(image)

            bottom_padding = text_size[1]+12
            
            draw.line((0, image.size[1]-bottom_padding) + (image.size[0], image.size[1]-bottom_padding), fill = (128, 128, 128))
            draw.line((0, image.size[1]-bottom_padding-1) + (image.size[0], image.size[1]-bottom_padding-1), fill = (128, 128, 128))

            for x in range(24):
                draw.text((10+(7+text_size[0])*x, image.size[1]-bottom_padding+6), '%02d' % x, font=font, fill=(0,0,0))

            for n in range(len(chart)):
                value = chart[n]

                if value > 0:
                    draw.rectangle((10+(7+text_size[0])*n, image.size[1]-bottom_padding-2-value, 10+(7+text_size[0])*(n+1), image.size[1]-bottom_padding-2), fill=(95, 158, 237))

            import StringIO
            output = StringIO.StringIO()
    
            image.save(output, 'PNG')
            data = output.getvalue()

            from email.MIMEImage import MIMEImage

            msgImage = MIMEImage(data)
            msgImage.add_header('Content-ID', '<graph.png>')
            msg.attach(msgImage) 

            msg.send()
        else:
            print con
