from django.contrib import admin
from .models import Recipient, Message, Mailing, MailingAttempt


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "comment")
    search_fields = ("email", "full_name")
    list_filter = ("email",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "body")
    search_fields = ("subject", "body")


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "start_time", "end_time", "status", "message")
    list_filter = ("status", "start_time")
    search_fields = ("message__subject",)
    filter_horizontal = ("recipients",)


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ("mailing", "attempt_time", "status", "server_response")
    list_filter = ("status", "attempt_time")
    search_fields = ("mailing__message__subject", "server_response")
