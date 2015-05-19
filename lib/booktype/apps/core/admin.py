from django.contrib import admin
from .models import Permission, Role, BookRole

admin.site.register(Permission)
admin.site.register(Role)
admin.site.register(BookRole)
