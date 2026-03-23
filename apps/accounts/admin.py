from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import (
    Author,
    Education,
    User,
    UserCertificate,
    UserEducation,
    UserExperience,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["phone", "first_name", "last_name", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_active", "is_deleted", "gender"]
    search_fields = ["phone", "first_name", "last_name"]

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "avatar", "bio", "age", "gender")},
        ),
        ("Location", {"fields": ("country", "region")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_deleted",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "password1", "password2"),
            },
        ),
    )
    ordering = ["-created_at"]
    list_per_page = 50


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "is_active"]
    list_filter = ["type", "is_active"]
    search_fields = ["name"]


@admin.register(UserEducation)
class UserEducationAdmin(admin.ModelAdmin):
    list_display = ["user", "education", "start_date", "end_date"]
    list_filter = ["start_date"]
    search_fields = ["user__phone", "education__name"]
    raw_id_fields = ["user", "education"]


@admin.register(UserExperience)
class UserExperienceAdmin(admin.ModelAdmin):
    list_display = ["user", "name", "position", "start_date", "end_date"]
    search_fields = ["user__phone", "name", "position"]
    raw_id_fields = ["user"]


@admin.register(UserCertificate)
class UserCertificateAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "course"]
    search_fields = ["name", "user__phone"]
    raw_id_fields = ["user", "course", "attachment"]


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "experience_years"]
    search_fields = ["first_name", "last_name"]
