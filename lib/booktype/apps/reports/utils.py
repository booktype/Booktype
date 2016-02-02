from django.db import connection

from django.conf import settings
from django.contrib.auth.models import User

from booki.editor.models import Book, BookiGroup, Attachment


def get_info():
    num_of_users = User.objects.count()
    num_of_books = Book.objects.count()
    num_of_groups = BookiGroup.objects.count()

    attachments_size = 0
    for at in Attachment.objects.all():
        try:
            attachments_size += at.attachment.size
        except:
            pass

    cursor = connection.cursor()
    cursor.execute("SELECT pg_database_size(%s)", [settings.DATABASES['default']['NAME']])
    database_size = cursor.fetchone()[0]

    return {'users_num': num_of_users,
            'books_num': num_of_books,
            'groups_num': num_of_groups,
            'attachments_size': attachments_size,
            'database_size': database_size}
