import logging
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import Avg, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.courses.models import Lesson
from apps.interactions.models import Enrollment, LessonFavorite, LessonProgress, LessonRate, ModuleProgress
from apps.interactions.serializers import LessonFavoriteSerializer, LessonProgressUpdateSerializer, LessonRateSerializer

logger = logging.getLogger(__name__)


def _completion_threshold() -> int:
    return int(getattr(settings, "LESSON_COMPLETION_THRESHOLD_PERCENT", 80))


def _leaderboard_version() -> int:
    return int(cache.get("leaderboard:version", 1))


def _bump_leaderboard_version() -> None:
    cache.set("leaderboard:version", _leaderboard_version() + 1, timeout=None)


def _leaderboard_cache_key(limit: int, offset: int) -> str:
    return f"leaderboard:v{_leaderboard_version()}:limit:{limit}:offset:{offset}"


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
                    _bump_leaderboard_version()
                    logger.info(
                        "lesson_stars_awarded",
                        extra={
                            "user_id": request.user.id,
                            "lesson_id": lesson.id,
                            "course_id": lesson.module.course_id,
                            "stars_awarded": stars_awarded_now,
                        },
                    )

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


class LeaderboardAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            limit = int(request.query_params.get("limit", 10))
            offset = int(request.query_params.get("offset", 0))
        except ValueError as exc:
            raise ValidationError("limit and offset must be integers") from exc

        if limit < 1 or limit > 100:
            raise ValidationError("limit must be between 1 and 100")
        if offset < 0:
            raise ValidationError("offset must be >= 0")

        cache_key = _leaderboard_cache_key(limit=limit, offset=offset)
        cached_top = cache.get(cache_key)
        if cached_top is None:
            ranked_qs = User.objects.filter(is_active=True, is_deleted=False).order_by(
                "-stars_balance",
                "updated_at",
                "id",
            )
            top_users = ranked_qs[offset : offset + limit]
            cached_top = [
                {
                    "id": user.id,
                    "phone": user.phone,
                    "stars_balance": user.stars_balance,
                }
                for user in top_users
            ]
            cache.set(cache_key, cached_top, timeout=60)
            logger.info("leaderboard_cache_refreshed", extra={"limit": limit, "offset": offset})

        top_payload = []
        for idx, item in enumerate(cached_top):
            top_payload.append(
                {
                    "id": item["id"],
                    "phone": item["phone"],
                    "stars_balance": item["stars_balance"],
                    "rank": offset + idx + 1,
                }
            )

        me = request.user
        users_ahead = User.objects.filter(is_active=True, is_deleted=False).filter(
            Q(stars_balance__gt=me.stars_balance)
            | Q(stars_balance=me.stars_balance, updated_at__lt=me.updated_at)
            | Q(stars_balance=me.stars_balance, updated_at=me.updated_at, id__lt=me.id)
        )
        my_rank = users_ahead.count() + 1

        return Response(
            {
                "me": {
                    "id": me.id,
                    "phone": me.phone,
                    "stars_balance": me.stars_balance,
                    "rank": my_rank,
                },
                "top": top_payload,
                "limit": limit,
                "offset": offset,
                "tie_breaker": "stars_balance desc, updated_at asc, id asc",
            },
            status=status.HTTP_200_OK,
        )
