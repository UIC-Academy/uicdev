from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class Enrollment(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name=_("user"),
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name=_("course"),
    )
    started_at = models.DateTimeField(_("started at"), auto_now_add=True)
    finished_at = models.DateTimeField(_("finished at"), null=True, blank=True)

    class Meta:
        verbose_name = _("enrollment")
        verbose_name_plural = _("enrollments")
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user} - {self.course}"


class LessonQuestion(BaseModel):
    lesson = models.ForeignKey(
        "courses.Lesson",
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name=_("lesson"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_questions",
        verbose_name=_("user"),
    )
    text = models.TextField(_("text"))

    class Meta:
        verbose_name = _("lesson question")
        verbose_name_plural = _("lesson questions")

    def __str__(self):
        return f"Q: {self.text[:50]}"


class LessonAnswer(BaseModel):
    lesson = models.ForeignKey(
        "courses.Lesson",
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("lesson"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_answers",
        verbose_name=_("user"),
    )
    question = models.ForeignKey(
        LessonQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("question"),
    )
    text = models.TextField(_("text"))
    is_deleted = models.BooleanField(_("is deleted"), default=False)

    class Meta:
        verbose_name = _("lesson answer")
        verbose_name_plural = _("lesson answers")

    def __str__(self):
        return f"A: {self.text[:50]}"


class LessonResource(BaseModel):
    lesson = models.ForeignKey(
        "courses.Lesson",
        on_delete=models.CASCADE,
        related_name="resources",
        verbose_name=_("lesson"),
    )
    media = models.ForeignKey(
        "common.Media",
        on_delete=models.CASCADE,
        related_name="lesson_resources",
        verbose_name=_("media"),
    )
    caption = models.CharField(_("caption"), max_length=500, blank=True)

    class Meta:
        verbose_name = _("lesson resource")
        verbose_name_plural = _("lesson resources")

    def __str__(self):
        return f"{self.lesson} - {self.caption}"


class LessonRate(BaseModel):
    lesson = models.ForeignKey(
        "courses.Lesson",
        on_delete=models.CASCADE,
        related_name="rates",
        verbose_name=_("lesson"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_rates",
        verbose_name=_("user"),
    )
    star_count = models.PositiveSmallIntegerField(_("star count"))
    comment = models.TextField(_("comment"), blank=True)

    class Meta:
        verbose_name = _("lesson rate")
        verbose_name_plural = _("lesson rates")
        unique_together = ("lesson", "user")

    def __str__(self):
        return f"{self.lesson} - {self.star_count} stars"


class UserHomeworkAttempt(BaseModel):
    lesson = models.ForeignKey(
        "courses.Lesson",
        on_delete=models.CASCADE,
        related_name="homework_attempts",
        verbose_name=_("lesson"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="homework_attempts",
        verbose_name=_("user"),
    )
    work_file = models.ForeignKey(
        "common.Media",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="homework_files",
        verbose_name=_("work file"),
    )
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)

    class Meta:
        verbose_name = _("user homework attempt")
        verbose_name_plural = _("user homework attempts")

    def __str__(self):
        return f"{self.user} - {self.title}"
