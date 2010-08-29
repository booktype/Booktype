from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import datetime

now = datetime.datetime.now()

def getUsers():
    from django.contrib.auth.models import User

    return User.objects.filter(date_joined__year = now.year,
                               date_joined__month = now.month,
                               date_joined__day = now.day)

def getBooks():
    from booki.editor.models import Book

    return Book.objects.filter(created__year = now.year,
                               created__month = now.month,
                               created__day = now.day)

def getGroups():
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

        # render result

        from django import template
                
        t = template.loader.get_template('booki_report.html')
        con = t.render(template.Context({"users": users,
                                         "books": books,
                                         "groups": groups,
                                         "history": history,
                                         "report_date": now
                                         }))


        if options['send_email']:
            from django.core.mail import EmailMultiAlternatives
            from booki import settings

            emails = [em[1] for em in settings.ADMINS]

            subject, from_email = 'Booki report for %s' % str(now), 'booki@booki.cc'
            text_content = con
            html_content = con

            msg = EmailMultiAlternatives(subject, text_content, from_email, emails)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        else:
            print con
