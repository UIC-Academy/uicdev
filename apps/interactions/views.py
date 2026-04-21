from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.courses.models import Lesson
from apps.interactions.models import Enrollment, LessonFavorite, LessonProgress, LessonRate, ModuleProgress
from apps.interactions.serializers import LessonFavoriteSerializer, LessonProgressUpdateSerializer, LessonRateSerializer


def _completion_threshold() -> int:
    return int(getattr(settings, "LESSON_COMPLETION_THRESHOLD_PERCENT", 80))


def _recalculate_module_progress(enrollment: Enrollment, lesson: Lesson) -> ModuleProgress:
    module = lesson.module
    total_lessons = module.lessons.filter(is_active=True).count()
    completed_lessons = LessonProgress.objects.filter(
        enrollment=enrollment,
        lesson__module=module,
        lesson__is_active=True,
        is_completed=True,
    ).count()
    if total_lessons == 0:
        percentage = Decimal("0.00")
    else:
        percentage = (Decimal(completed_lessons) * Decimal("100.00") / Decimal(total_lessons)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    module_progress, _ = ModuleProgress.objects.get_or_create(
        enrollment=enrollment,
        module=module,
        defaults={
            "progress_percentage": percentage,
            "completed_lessons": completed_lessons,
            "total_lessons": total_lessons,
        },
    )
    module_progress.progress_percentage = percentage
    module_progress.completed_lessons = completed_lessons
    module_progress.total_lessons = total_lessons
    module_progress.save(update_fields=["progress_percentage", "completed_lessons", "total_lessons", "updated_at"])
    return module_progress


def _calculate_lesson_reward(enrollment: Enrollment, lesson: Lesson) -> int:
    course = lesson.module.course
    total_lessons = Lesson.objects.filter(module__course=course, is_active=True).count()
    if total_lessons == 0 or course.reward_stars == 0:
        return 0

    base = course.reward_stars // total_lessons
    remainder = course.reward_stars % total_lessons

    completed_in_course = LessonProgress.objects.filter(
        enrollment=enrollment,
        lesson__module__course=course,
        lesson__is_active=True,
        is_completed=True,
    ).count()
    reward = base
    if remainder > 0 and completed_in_course == total_lessons:
        reward += remainder
    return reward


class LessonProgressAPIView(GenericAPIView):
    serializer_class = LessonProgressUpdateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        watch_percent = serializer.validated_data["watch_percent"]

        lesson = Lesson.objects.select_related("module__course").filter(id=lesson_id, is_active=True).first()
        if not lesson:
            raise ValidationError("Lesson not found")

        enrollment = Enrollment.objects.filter(user=request.user, course=lesson.module.course).first()
        if not enrollment:
            raise ValidationError("User is not enrolled in this course")

        threshold = _completion_threshold()
        stars_awarded_now = 0

        with transaction.atomic():
            progress, _ = LessonProgress.objects.select_for_update().get_or_create(
                enrollment=enrollment,
                lesson=lesson,
            )
            progress.watch_percent = max(progress.watch_percent, watch_percent)

            if progress.watch_percent >= threshold and not progress.is_completed:
                progress.is_completed = True
                progress.completed_at = timezone.now()

            if progress.is_completed and not progress.reward_granted:
                stars_awarded_now = _calculate_lesson_reward(enrollment=enrollment, lesson=lesson)
                progress.rewarded_stars = stars_awarded_now
                progress.reward_granted = True
                if stars_awarded_now > 0:
                    request.user.stars_balance += stars_awarded_now
                    request.user.save(update_fields=["stars_balance", "updated_at"])

            progress.save(
                update_fields=[
                    "watch_percent",
                    "is_completed",
                    "completed_at",
                    "reward_granted",
                    "rewarded_stars",
                    "updated_at",
                ]
            )

            module_progress = _recalculate_module_progress(enrollment=enrollment, lesson=lesson)

        return Response(
            {
                "lesson_id": lesson.id,
                "watch_percent": progress.watch_percent,
                "is_completed": progress.is_completed,
                "completion_threshold": threshold,
                "stars_awarded_now": stars_awarded_now,
                "lesson_rewarded_stars": progress.rewarded_stars,
                "user_stars_balance": request.user.stars_balance,
                "module_id": lesson.module_id,
                "module_progress_percentage": str(module_progress.progress_percentage),
                "module_completed_lessons": module_progress.completed_lessons,
                "module_total_lessons": module_progress.total_lessons,
            },
            status=status.HTTP_200_OK,
        )


class LessonFavoriteAPIView(GenericAPIView):
    serializer_class = LessonFavoriteSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_favorite = serializer.validated_data["is_favorite"]

        lesson = Lesson.objects.select_related("module__course").filter(id=lesson_id, is_active=True).first()
        if not lesson:
            raise ValidationError("Lesson not found")

        if not Enrollment.objects.filter(user=request.user, course=lesson.module.course).exists():
            raise ValidationError("User is not enrolled in this course")

        if is_favorite:
            LessonFavorite.objects.get_or_create(user=request.user, lesson=lesson)
        else:
            LessonFavorite.objects.filter(user=request.user, lesson=lesson).delete()

        return Response(
            {
                "lesson_id": lesson.id,
                "is_favorite": is_favorite,
            }
        )


class LessonRateAPIView(GenericAPIView):
    serializer_class = LessonRateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lesson = Lesson.objects.select_related("module__course").filter(id=lesson_id, is_active=True).first()
        if not lesson:
            raise ValidationError("Lesson not found")

        if not Enrollment.objects.filter(user=request.user, course=lesson.module.course).exists():
            raise ValidationError("User is not enrolled in this course")

        star_count = serializer.validated_data["star_count"]
        comment = serializer.validated_data.get("comment", "")

        LessonRate.objects.update_or_create(
            lesson=lesson,
            user=request.user,
            defaults={
                "star_count": star_count,
                "comment": comment,
            },
        )

        avg = LessonRate.objects.filter(lesson=lesson).aggregate(avg_rating=Avg("star_count"))["avg_rating"] or 0
        lesson.current_rating = round(avg, 2)
        lesson.save(update_fields=["current_rating", "updated_at"])

        return Response(
            {
                "lesson_id": lesson.id,
                "current_rating": lesson.current_rating,
                "star_count": star_count,
                "comment": comment,
            },
            status=status.HTTP_200_OK,
        )
