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

def getUsers():
    """Get users who registered today."""

    from django.contrib.auth.models import User

    return User.objects.filter(date_joined__year = now.year,
                               date_joined__month = now.month,
                               date_joined__day = now.day)

def getBooks():
    """Get books created today."""

    from booki.editor.models import Book

    return Book.objects.filter(created__year = now.year,
                               created__month = now.month,
                               created__day = now.day)

def getGroups():
    """Get groups created today."""

    from booki.editor.models import BookiGroup

    return BookiGroup.objects.filter(created__year = now.year,
                                     created__month = now.month,
                                     created__day = now.day)
    

def getHistory():
    from booki.editor.models import BookHistory
    from django.db.models import Count

    from booki.editor.models import Book

    history = []

    for books2 in BookHistory.objects.filter(modified__year = now.year,
                                             modified__month = now.month,
                                             modified__day = now.day).values('book').annotate(Count('book')).order_by("-book__count"):
        
        bookName = Book.objects.get(pk=books2['book']).title
        
        history.append((bookName, [h.chapter_history for h in BookHistory.objects.filter(book__id=books2['book'],
                                                              chapter_history__isnull=False,
                                                             modified__year = now.year,
                                                             modified__month = now.month,
                                                             modified__day = now.day)]))

#        history.append((bookName, BookHistory.objects.filter(book__id=books2['book'],
#                                                             modified__year = now.year,
#                                                             modified__month = now.month,
#                                                             modified__day = now.day)))

    
    return history

def getInfo():
    from django.contrib.auth.models import User
    from booki.editor.models import Book, Attachment
    from django.db import connection

    numOfUsers = len(User.objects.all())
    numOfBooks = len(Book.objects.all())

    attachmentsSize = 0
    for at in Attachment.objects.all():
        try:
            attachmentsSize += at.attachment.size
        except:
            pass

    cursor = connection.cursor()
    cursor.execute("SELECT pg_database_size(%s)", [settings.DATABASE_NAME]);
    databaseSize = cursor.fetchone()[0]

    return {'users_num': numOfUsers,
            'books_num': numOfBooks,
            'attachments_size': attachmentsSize,
            'database_size': databaseSize}
    

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
            help='N days ago'),
        )



    def handle(self, *args, **options):
        global now

        now = now - datetime.timedelta(days=int(options['days']))

        users = getUsers()
        books = getBooks()
        groups = getGroups()
        history = getHistory()
        info = getInfo()

        try:
            BOOKI_NAME = settings.BOOKI_NAME
        except AttributeError:
            BOOKI_NAME = 'Booki name'

        # render result

        from django import template
                
        t = template.loader.get_template('booki_report.html')
        con = t.render(template.Context({"users": users,
                                         "books": books,
                                         "groups": groups,
                                         "history": history,
                                         "report_date": now,
                                         "info": info,
                                         "booki_name": BOOKI_NAME
                                         }))


        if options['send_email']:
            from django.core.mail import EmailMultiAlternatives

            try:
                REPORT_EMAIL_USER = settings.REPORT_EMAIL_USER
            except AttributeError:
                REPORT_EMAIL_USER = 'booki@booki.cc'

            emails = [em[1] for em in settings.ADMINS]

            subject = 'Booki report for %s (%s)' % (BOOKI_NAME, now.strftime("%A %d %B %Y"))
            text_content = con
            html_content = con

            msg = EmailMultiAlternatives(subject, text_content, REPORT_EMAIL_USER, emails)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        else:
            print con
