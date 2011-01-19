import django.dispatch


account_created = django.dispatch.Signal(providing_args=["password"])

account_status_changed = django.dispatch.Signal(providing_args=["message"])
