from django.contrib import admin

from apps.payments.models import Order, Transaction


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "amount")
    list_display_links = ("id", "course")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "wallet", "order", "amount", "type", "status", "vendor")
    list_display_links = ("id", "wallet")
