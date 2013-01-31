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
week_ago = None


import os.path
import re


def getUsers():
    """Get users who registered today."""

    from django.contrib.auth.models import User

    return User.objects.filter(date_joined__gte = week_ago)

    return None


def getBooks():
    """Get books created today."""

    from booki.editor.models import Book

    return Book.objects.filter(created__gte = week_ago)
    
    
def getGroups():
    """Get groups created today."""

    from booki.editor.models import BookiGroup

    return BookiGroup.objects.filter(created__gte = week_ago)


def getHistory():
    from booki.editor.models import BookHistory
    from django.db.models import Count

    from booki.editor.models import Book

    history = []
    
    for books2 in BookHistory.objects.filter(modified__gte = week_ago).values('book').annotate(Count('book')).order_by("-book__count"):        
        book = Book.objects.get(pk=books2['book'])
        
        history.append((book, [h.chapter_history for h in BookHistory.objects.filter(book__id=books2['book'],
                                                                                     chapter_history__isnull=False,
                                                                                     modified__gte = week_ago)]))

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
    from django.db.models import Count
    from booki.editor import models
    import math

    hours = []
    max_num = 0

    for days in range(7):
        that_day = week_ago + datetime.timedelta(days=days)
        hours.append([0]*7)

        for x in models.BookHistory.objects.filter(modified__year = that_day.year, modified__month = that_day.month, modified__day = that_day.day).extra({'modified': 'EXTRACT (HOUR FROM modified)'}).values('modified').annotate(count=Count('id')):            
            cnt = x['count']
            hours[days][int(x['modified']/4)] += cnt

            if cnt > max_num: max_num = cnt        

    for y in range(7):
        for x in range(6):
            try:
                hours[y][x] = int(float(hours[y][x])/float(max_num)*200.0)
            except ZeroDivisionError:
                hours[y][x] = 0

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
        global week_ago

        now = now - datetime.timedelta(days=int(options['days']))
        week_ago = now - datetime.timedelta(days=7)

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

        from booki.editor import models
        from django.db.models import Count

        active_books = [models.Book.objects.get(id=b['book']) for b in models.BookHistory.objects.filter(modified__gte = week_ago).values('book').annotate(Count('book')).order_by("-book__count")[:10]]
        # render result
        from django.contrib.auth.models import User
        active_users = [User.objects.get(id=b['user']) for b in models.BookHistory.objects.filter(modified__gte = week_ago).values('user').annotate(Count('user')).order_by("-user__count")[:10]]

        from django import template

        t = template.loader.get_template('booktype_weekly_report.html')
        con = t.render(template.Context({"users": users,
                                         "books": books,
                                         "groups": groups,
                                         "history": history,
                                         "report_date": now,
                                         "info": info,
                                         "booki_name": BOOKTYPE_NAME,
                                         "week_ago": week_ago,
                                         "now_date": now,
                                         "active_books": active_books,
                                         "active_users": active_users,
                                         "site_url": settings.BOOKI_URL
                                         }))
        

        if options['send_email']:
            from django.core.mail import EmailMultiAlternatives

            try:
                REPORT_EMAIL_USER = settings.REPORT_EMAIL_USER
            except AttributeError:
                REPORT_EMAIL_USER = 'booktype@booktype.pro'

            emails = [em[1] for em in settings.ADMINS]

            subject = 'Weekly report for %s (%s)' % (BOOKTYPE_NAME, now.strftime("%A %d %B %Y"))

            text_content = con
            html_content = con

            msg = EmailMultiAlternatives(subject, text_content, REPORT_EMAIL_USER, emails)
            msg.attach_alternative(html_content, "text/html")

            # Make graph
            import ImageFont, ImageDraw, Image

            from booki.editor import models as ed
            import os.path
            font = ImageFont.truetype("%s/management/commands/linear-by-braydon-fuller.otf" % os.path.dirname(ed.__file__), 12)
            
            text_size =  font.getsize("P")
            image = Image.new("RGB", (40+(7*6*10), 200+2+12), (255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            bottom_padding = text_size[1]+12

            for y in range(7):
                for x in range(6):
                    value = chart[y][x]

                    if value > 0:
                        draw.rectangle((20+y*60+x*10, image.size[1]-bottom_padding-2-value, 20+y*60+(1+x)*10, image.size[1]-bottom_padding-2), fill=(95, 158, 237))
            
            draw.line((0, image.size[1]-bottom_padding) + (image.size[0], image.size[1]-bottom_padding), fill = (128, 128, 128))
            draw.line((0, image.size[1]-bottom_padding-1) + (image.size[0], image.size[1]-bottom_padding-1), fill = (128, 128, 128))

            for x in range(8):
                draw.ellipse((20+x*60-3, image.size[1]-bottom_padding-3, 20+x*60+3, image.size[1]-bottom_padding+3), fill = (128, 128,128))
                draw.rectangle((20+x*60-2+30, image.size[1]-bottom_padding-2, 20+x*60+30+2, image.size[1]-bottom_padding+2), fill = (128, 128,128))

            def _width(s):
                return font.getsize(s)[0]

            def _day(n):
                s = (week_ago+datetime.timedelta(days=n)).strftime('%d.%m')
                draw.text((20+n*60-_width(s)/2, image.size[1]-bottom_padding+6), s, font=font, fill=(0,0,0))

            for d in range(8):
                _day(d)

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
            pass
            #print con
