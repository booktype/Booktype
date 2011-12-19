import models
from django.contrib import admin

from booki.account.models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    fk_name = 'user'
    max_num = 1

class UserAdmin(AuthUserAdmin):
    inlines = [UserProfileInline,]

# unregister old user admin
admin.site.unregister(User)
# register new user admin
admin.site.register(User, UserAdmin)

admin.site.register(models.License)
admin.site.register(models.Book)
admin.site.register(models.Info)
admin.site.register(models.Chapter)
admin.site.register(models.Attachment)
admin.site.register(models.Language)
admin.site.register(models.BookStatus)
admin.site.register(models.BookToc)
admin.site.register(models.BookiGroup)
admin.site.register(models.BookNotes)
