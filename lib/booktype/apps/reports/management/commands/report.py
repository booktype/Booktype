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

import os.path
import datetime
import StringIO
from email.MIMEImage import MIMEImage

from django import template
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count
from django.utils.translation import ugettext
from django.contrib.auth.models import User

from booki.editor.models import Book, BookiGroup, BookHistory
from booktype.utils import config

from ...utils import get_info

try:
    from PIL import ImageFont, ImageDraw, Image
except ImportError:
    import ImageFont, ImageDraw, Image

now = datetime.datetime.now()


def get_history():
    history = []

    book_history = BookHistory.objects.filter(
        modified__year=now.year,
        modified__month=now.month,
        modified__day=now.day
    ).values('book').annotate(Count('book')).order_by("-book__count")

    for books2 in book_history:
        book = Book.objects.get(pk=books2['book'])

        history.append((book, [h.chapter_history for h in BookHistory.objects.filter(book__id=books2['book'],
                                                                                     chapter_history__isnull=False,
                                                                                     modified__year=now.year,
                                                                                     modified__month=now.month,
                                                                                     modified__day=now.day)]))

    return history


def get_chart():
    hours = [0] * 24
    max_num = 0

    book_history = BookHistory.objects.filter(
        modified__year=now.year,
        modified__month=now.month,
        modified__day=now.day
    ).extra(
        {'modified': 'EXTRACT (HOUR FROM modified)'}
    ).values('modified').annotate(count=Count('id'))

    for x in book_history:
        cnt = x['count']
        hours[int(x['modified'])] = cnt

        if cnt > max_num: max_num = cnt

    for x in range(len(hours)):
        try:
            hours[x] = int(float(hours[x]) / float(max_num) * 200.0)
        except ZeroDivisionError:
            hours[x] = 0

    return hours


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--send-email',
                            action='store_true',
                            dest='send_email',
                            default=False,
                            help='Send email to admin')

        parser.add_argument('--days',
                            action='store',
                            dest='days',
                            default=0,
                            help='N days ago')

    def handle(self, *args, **options):
        global now

        now -= datetime.timedelta(days=int(options['days']))

        # get users who registered today
        users = User.objects.filter(date_joined__year=now.year,
                                    date_joined__month=now.month,
                                    date_joined__day=now.day)

        # get books created today
        books = Book.objects.filter(created__year=now.year,
                                    created__month=now.month,
                                    created__day=now.day)

        # get groups created today
        groups = BookiGroup.objects.filter(created__year=now.year,
                                           created__month=now.month,
                                           created__day=now.day)

        history = get_history()
        info = get_info()
        chart = get_chart()

        BOOKTYPE_NAME = settings.BOOKTYPE_SITE_NAME

        if not BOOKTYPE_NAME:
            BOOKTYPE_NAME = 'Booktype'

        # render result
        t = template.loader.get_template('reports/booktype_daily_report.html')

        con = t.render({"users": users,
                        "books": books,
                        "groups": groups,
                        "history": history,
                        "report_date": now,
                        "info": info,
                        "booktype_name": BOOKTYPE_NAME,
                        "site_url": settings.BOOKTYPE_URL
                        })

        if options['send_email']:
            reports_email_from = config.get_configuration('REPORTS_EMAIL_FROM')
            reports_email_users = config.get_configuration('REPORTS_EMAIL_USERS')

            subject = ugettext('Daily report for {0} ({1})').format(BOOKTYPE_NAME, now.strftime("%A %d %B %Y"))

            text_content = con
            html_content = con

            msg = EmailMultiAlternatives(subject, text_content, reports_email_from, reports_email_users)
            msg.attach_alternative(html_content, "text/html")

            # Make graph
            font_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                     '../../fonts/linear-by-braydon-fuller.otf'))

            if config.get_configuration('REPORTS_CUSTOM_FONT_PATH'):
                font_path = config.get_configuration('REPORTS_CUSTOM_FONT_PATH')

            font = ImageFont.truetype(font_path, 12)

            text_size = font.getsize("23")
            image = Image.new("RGB", (20 + (7 + text_size[0]) * 24, 200 + 2 + 12), (255, 255, 255))
            draw = ImageDraw.Draw(image)

            bottom_padding = text_size[1] + 12

            draw.line((0, image.size[1] - bottom_padding) + (image.size[0], image.size[1] - bottom_padding),
                      fill=(128, 128, 128))
            draw.line((0, image.size[1] - bottom_padding - 1) + (image.size[0], image.size[1] - bottom_padding - 1),
                      fill=(128, 128, 128))

            for x in range(24):
                draw.text((10 + (7 + text_size[0]) * x, image.size[1] - bottom_padding + 6), '%02d' % x, font=font,
                          fill=(0, 0, 0))

            for n in range(len(chart)):
                value = chart[n]

                if value > 0:
                    draw.rectangle((10 + (7 + text_size[0]) * n, image.size[1] - bottom_padding - 2 - value,
                                    10 + (7 + text_size[0]) * (n + 1), image.size[1] - bottom_padding - 2),
                                   fill=(95, 158, 237))

            output = StringIO.StringIO()
            image.save(output, 'PNG')

            data = output.getvalue()

            msgImage = MIMEImage(data)
            msgImage.add_header('Content-ID', '<graph.png>')
            msg.attach(msgImage)
            msg.send()
        else:
            self.stdout.write(con)
