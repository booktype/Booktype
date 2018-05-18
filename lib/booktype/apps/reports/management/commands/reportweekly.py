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

import StringIO
import os.path
import datetime
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
week_ago = None


def get_history():
    history = []

    for books2 in BookHistory.objects.filter(modified__gte=week_ago).values('book').annotate(Count('book')).order_by(
            "-book__count"):
        book = Book.objects.get(pk=books2['book'])

        history.append((book, [h.chapter_history for h in BookHistory.objects.filter(book__id=books2['book'],
                                                                                     chapter_history__isnull=False,
                                                                                     modified__gte=week_ago)]))

    return history


def get_chart():
    hours = []
    max_num = 0

    for days in range(7):
        that_day = week_ago + datetime.timedelta(days=days)
        hours.append([0] * 7)

        book_history = BookHistory.objects.filter(
            modified__year=that_day.year,
            modified__month=that_day.month,
            modified__day=that_day.day
        ).extra(
            {'modified': 'EXTRACT (HOUR FROM modified)'}
        ).values('modified').annotate(count=Count('id'))

        for x in book_history:
            cnt = x['count']
            hours[days][int(x['modified'] / 4)] += cnt

            if cnt > max_num: max_num = cnt

    for y in range(7):
        for x in range(6):
            try:
                hours[y][x] = int(float(hours[y][x]) / float(max_num) * 200.0)
            except ZeroDivisionError:
                hours[y][x] = 0

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
        global week_ago

        now -= datetime.timedelta(days=int(options['days']))
        week_ago = now - datetime.timedelta(days=7)

        # get users who joined during last week
        users = User.objects.filter(date_joined__gte=week_ago)

        # get books created during week
        books = Book.objects.filter(created__gte=week_ago)

        # get groups created during week
        groups = BookiGroup.objects.filter(created__gte=week_ago)

        history = get_history()
        info = get_info()
        chart = get_chart()

        BOOKTYPE_NAME = settings.BOOKTYPE_SITE_NAME

        if not BOOKTYPE_NAME:
            BOOKTYPE_NAME = 'Booktype'

        active_books = [Book.objects.get(id=b['book']) for b in
                        BookHistory.objects.filter(modified__gte=week_ago).values('book').annotate(
                            Count('book')).order_by("-book__count")[:10]]
        # render result

        active_users = [User.objects.get(id=b['user']) for b in
                        BookHistory.objects.filter(modified__gte=week_ago).values('user').annotate(
                            Count('user')).order_by("-user__count")[:10]]

        t = template.loader.get_template('reports/booktype_weekly_report.html')
        con = t.render({"users": users,
                                "books": books,
                                "groups": groups,
                                "history": history,
                                "report_date": now,
                                "info": info,
                                "booktype_name": BOOKTYPE_NAME,
                                "week_ago": week_ago,
                                "now_date": now,
                                "active_books": active_books,
                                "active_users": active_users,
                                "site_url": settings.BOOKTYPE_URL
                                })

        if options['send_email']:
            reports_email_from = config.get_configuration('REPORTS_EMAIL_FROM')
            reports_email_users = config.get_configuration('REPORTS_EMAIL_USERS')

            subject = ugettext('Weekly report for ({0} - {1})').format(BOOKTYPE_NAME, now.strftime("%A %d %B %Y"))

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

            text_size = font.getsize("P")
            image = Image.new("RGB", (40 + (7 * 6 * 10), 200 + 2 + 12), (255, 255, 255))
            draw = ImageDraw.Draw(image)

            bottom_padding = text_size[1] + 12

            for y in range(7):
                for x in range(6):
                    value = chart[y][x]

                    if value > 0:
                        draw.rectangle((20 + y * 60 + x * 10, image.size[1] - bottom_padding - 2 - value,
                                        20 + y * 60 + (1 + x) * 10, image.size[1] - bottom_padding - 2),
                                       fill=(95, 158, 237))

            draw.line((0, image.size[1] - bottom_padding) + (image.size[0], image.size[1] - bottom_padding),
                      fill=(128, 128, 128))
            draw.line((0, image.size[1] - bottom_padding - 1) + (image.size[0], image.size[1] - bottom_padding - 1),
                      fill=(128, 128, 128))

            for x in range(8):
                draw.ellipse((20 + x * 60 - 3, image.size[1] - bottom_padding - 3, 20 + x * 60 + 3,
                              image.size[1] - bottom_padding + 3), fill=(128, 128, 128))
                draw.rectangle((20 + x * 60 - 2 + 30, image.size[1] - bottom_padding - 2, 20 + x * 60 + 30 + 2,
                                image.size[1] - bottom_padding + 2), fill=(128, 128, 128))

            def _width(s):
                return font.getsize(s)[0]

            def _day(n):
                s = (week_ago + datetime.timedelta(days=n)).strftime('%d.%m')
                draw.text((20 + n * 60 - _width(s) / 2, image.size[1] - bottom_padding + 6), s, font=font,
                          fill=(0, 0, 0))

            for d in range(8):
                _day(d)

            output = StringIO.StringIO()

            image.save(output, 'PNG')
            data = output.getvalue()

            msgImage = MIMEImage(data)
            msgImage.add_header('Content-ID', '<graph.png>')
            msg.attach(msgImage)

            msg.send()
        else:
            self.stdout.write(con)
