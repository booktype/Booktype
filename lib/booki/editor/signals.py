import django.dispatch


book_created = django.dispatch.Signal(providing_args=["book"])
book_version_created = django.dispatch.Signal(providing_args=["book", "version"])

chapter_created = django.dispatch.Signal(providing_args=["chapter"])
chapter_modified = django.dispatch.Signal(providing_args=["user", "chapter"])

attachment_uploaded = django.dispatch.Signal(providing_args=["attachment"])

book_toc_changed = django.dispatch.Signal()


