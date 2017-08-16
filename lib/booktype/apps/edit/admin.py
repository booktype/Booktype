from django.contrib import admin
from .models import Comment, InviteCode, ChatThread, ChatMessage

admin.site.register(Comment)
admin.site.register(InviteCode)
admin.site.register(ChatThread)
admin.site.register(ChatMessage)
