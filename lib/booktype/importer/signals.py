import django.dispatch

# triggered when book import is made
book_imported = django.dispatch.Signal(providing_args=["book"])

# triggered when document is imported into chapter. Should we pass imported file?
chapter_imported = django.dispatch.Signal(providing_args=["chapter"])
