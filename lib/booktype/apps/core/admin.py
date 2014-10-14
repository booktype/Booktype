from django.contrib import admin
from .models import Permission, Role

admin.site.register(Permission)
admin.site.register(Role)
