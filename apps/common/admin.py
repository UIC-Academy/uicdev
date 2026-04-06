from django.contrib import admin

from apps.common.models import Country, Media, Region


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ["id", "file", "created_at"]
    search_fields = ["file"]


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
