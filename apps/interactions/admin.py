from django.contrib import admin

from apps.interactions.models import (
    Enrollment,
    LessonAnswer,
    LessonFavorite,
    LessonProgress,
    LessonQuestion,
    LessonRate,
    LessonResource,
    ModuleProgress,
    UserHomeworkAttempt,
)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["user", "course", "started_at", "finished_at"]
    list_filter = ["started_at"]
    search_fields = ["user__phone", "course__name"]
    raw_id_fields = ["user", "course"]


@admin.register(LessonQuestion)
class LessonQuestionAdmin(admin.ModelAdmin):
    list_display = ["lesson", "user", "created_at"]
    search_fields = ["text", "user__phone", "lesson__name"]
    raw_id_fields = ["user", "lesson"]


@admin.register(LessonAnswer)
class LessonAnswerAdmin(admin.ModelAdmin):
    list_display = ["question", "user", "is_deleted", "created_at"]
    list_filter = ["is_deleted"]
    search_fields = ["text", "user__phone"]
    raw_id_fields = ["user", "lesson", "question"]


@admin.register(LessonResource)
class LessonResourceAdmin(admin.ModelAdmin):
    list_display = ["lesson", "media", "caption"]
    search_fields = ["caption", "lesson__name"]
    raw_id_fields = ["lesson", "media"]


@admin.register(LessonRate)
class LessonRateAdmin(admin.ModelAdmin):
    list_display = ["lesson", "user", "star_count"]
    list_filter = ["star_count"]
    search_fields = ["user__phone", "lesson__name"]
    raw_id_fields = ["user", "lesson"]


@admin.register(LessonFavorite)
class LessonFavoriteAdmin(admin.ModelAdmin):
    list_display = ["lesson", "user", "created_at"]
    search_fields = ["user__phone", "lesson__name"]
    raw_id_fields = ["user", "lesson"]


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ["lesson", "enrollment", "watch_percent", "is_completed", "rewarded_stars"]
    list_filter = ["is_completed", "reward_granted"]
    raw_id_fields = ["lesson", "enrollment"]


@admin.register(ModuleProgress)
class ModuleProgressAdmin(admin.ModelAdmin):
    list_display = ["module", "enrollment", "progress_percentage", "completed_lessons", "total_lessons"]
    raw_id_fields = ["module", "enrollment"]


@admin.register(UserHomeworkAttempt)
class UserHomeworkAttemptAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "lesson", "created_at"]
    search_fields = ["title", "user__phone", "lesson__name"]
    raw_id_fields = ["user", "lesson", "work_file"]
