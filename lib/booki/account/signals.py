import django.dispatch


account_created = django.dispatch.Signal(providing_args=["password"])
