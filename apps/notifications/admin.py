from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "course", "is_send_to_all", "created_at"]
    list_filter = ["is_send_to_all", "created_at"]
    search_fields = ["title", "message", "user__phone"]
    raw_id_fields = ["user", "course", "module", "category", "image"]
