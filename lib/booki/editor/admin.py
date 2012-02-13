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

# customize some lists with additional column and filters
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'created', 'owner', 'hidden')
    list_filter = ['hidden', 'group']
    ordering = ['title']
    search_fields = ['title']

class InfoAdmin(admin.ModelAdmin):
    list_filter = ['book']

class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'version', 'revision', 'modified')
    ordering = ['title']
    list_filter = ['book']
    search_fields = ['title']

class AttachmentAdmin(admin.ModelAdmin):
    list_filter = ['book']

class BookStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'weight')
    ordering = ['-weight']
    list_filter = ['book']

class BookTocAdmin(admin.ModelAdmin):
    list_display = ('name', 'weight')
    ordering = ['-weight']
    list_filter = ['book']
    search_fields = ['name']
    
class BookiGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created')

class BookNotesAdmin(admin.ModelAdmin):
    list_filter = ['book']

class BookVersionAdmin(admin.ModelAdmin):
    list_filter = ['book']

# unregister old user admin
admin.site.unregister(User)
# register new user admin
admin.site.register(User, UserAdmin)

admin.site.register(models.License)
admin.site.register(models.Book, BookAdmin)
admin.site.register(models.Info, InfoAdmin)
admin.site.register(models.Chapter, ChapterAdmin)
admin.site.register(models.Attachment, AttachmentAdmin)
admin.site.register(models.Language)
admin.site.register(models.BookStatus, BookStatusAdmin)
admin.site.register(models.BookToc, BookTocAdmin)
admin.site.register(models.BookiGroup, BookiGroupAdmin)
admin.site.register(models.BookNotes, BookNotesAdmin)
admin.site.register(models.BookVersion, BookVersionAdmin)

