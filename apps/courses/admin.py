from django.contrib import admin

from apps.courses.models import Category, Course, CourseTag, Lesson, Module, Tag


class CourseTagInline(admin.TabularInline):
    model = CourseTag
    extra = 1


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    ordering = ["course_order"]


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    ordering = ["lesson_order"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["name", "author", "category", "is_active", "is_published", "reward_stars"]
    list_filter = ["is_active", "is_published", "category"]
    search_fields = ["name", "author__first_name", "author__last_name"]
    raw_id_fields = ["author", "banner"]
    inlines = [CourseTagInline, ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ["name", "course", "course_order"]
    list_filter = ["course"]
    search_fields = ["name", "course__name"]
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["name", "module", "type", "lesson_order", "is_active", "current_rating"]
    list_filter = ["type", "is_active"]
    search_fields = ["name", "module__name"]
    raw_id_fields = ["video"]
