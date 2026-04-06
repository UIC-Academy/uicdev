from celery import shared_task
from django.db.models import Avg

from apps.courses.models import Lesson
from apps.interactions.models import LessonRate


@shared_task
def recalculate_lesson_ratings():
    """Recalculate current_rating for all lessons based on LessonRate entries."""

    lessons = Lesson.objects.filter(is_active=True)
    updated_count = 0

    for lesson in lessons:
        avg = LessonRate.objects.filter(lesson=lesson).aggregate(avg_rating=Avg("star_count"))["avg_rating"]

        new_rating = round(avg, 2) if avg else 0.0

        if lesson.current_rating != new_rating:
            lesson.current_rating = new_rating
            lesson.save(update_fields=["current_rating"])
            updated_count += 1

    return f"Updated ratings for {updated_count} lessons"
