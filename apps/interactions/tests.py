from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Author, User
from apps.courses.choices import LessonTypeChoices
from apps.courses.models import Category, Course, Lesson, Module
from apps.interactions.models import Enrollment, LessonFavorite, LessonProgress, LessonRate, ModuleProgress
from apps.payments.choices import CurrencyEnum


class LessonInteractionFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="+998908888881", password="password", is_active=True)
        self.other_user = User.objects.create_user(phone="+998908888882", password="password", is_active=True)
        self.client.force_authenticate(user=self.user)

        author = Author.objects.create(first_name="Interaction", last_name="Teacher")
        category = Category.objects.create(name="Interaction Category")
        self.course = Course.objects.create(
            author=author,
            category=category,
            name="Interaction Course",
            price=Decimal("100000.00"),
            currency=CurrencyEnum.UZS,
            reward_stars=10,
            is_active=True,
            is_published=True,
        )
        self.module = Module.objects.create(course=self.course, name="M1", course_order=1)
        self.lesson1 = Lesson.objects.create(
            module=self.module,
            name="L1",
            type=LessonTypeChoices.VIDEO,
            lesson_order=1,
            is_active=True,
        )
        self.lesson2 = Lesson.objects.create(
            module=self.module,
            name="L2",
            type=LessonTypeChoices.VIDEO,
            lesson_order=2,
            is_active=True,
        )
        self.enrollment = Enrollment.objects.create(user=self.user, course=self.course)

    def test_progress_completion_updates_module_percentage_and_awards_stars_idempotently(self):
        response1 = self.client.post(
            f"/api/v1/interactions/lessons/{self.lesson1.id}/progress/",
            {"watch_percent": 80},
            format="json",
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data["is_completed"], True)
        self.assertEqual(response1.data["stars_awarded_now"], 5)
        self.assertEqual(response1.data["module_progress_percentage"], "50.00")

        self.user.refresh_from_db()
        self.assertEqual(self.user.stars_balance, 5)

        response2 = self.client.post(
            f"/api/v1/interactions/lessons/{self.lesson1.id}/progress/",
            {"watch_percent": 100},
            format="json",
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data["stars_awarded_now"], 0)

        self.user.refresh_from_db()
        self.assertEqual(self.user.stars_balance, 5)

        lesson_progress = LessonProgress.objects.get(enrollment=self.enrollment, lesson=self.lesson1)
        self.assertTrue(lesson_progress.is_completed)
        self.assertEqual(lesson_progress.rewarded_stars, 5)

        module_progress = ModuleProgress.objects.get(enrollment=self.enrollment, module=self.module)
        self.assertEqual(str(module_progress.progress_percentage), "50.00")

    def test_progress_below_threshold_does_not_complete(self):
        response = self.client.post(
            f"/api/v1/interactions/lessons/{self.lesson1.id}/progress/",
            {"watch_percent": 60},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_completed"], False)
        self.assertEqual(response.data["stars_awarded_now"], 0)
        self.assertEqual(response.data["module_progress_percentage"], "0.00")

    def test_favorite_toggle_persists_state(self):
        add_response = self.client.post(
            f"/api/v1/interactions/lessons/{self.lesson1.id}/favorite/",
            {"is_favorite": True},
            format="json",
        )
        self.assertEqual(add_response.status_code, status.HTTP_200_OK)
        self.assertTrue(LessonFavorite.objects.filter(user=self.user, lesson=self.lesson1).exists())

        remove_response = self.client.post(
            f"/api/v1/interactions/lessons/{self.lesson1.id}/favorite/",
            {"is_favorite": False},
            format="json",
        )
        self.assertEqual(remove_response.status_code, status.HTTP_200_OK)
        self.assertFalse(LessonFavorite.objects.filter(user=self.user, lesson=self.lesson1).exists())

    def test_rate_comment_updates_existing_rate_and_lesson_rating(self):
        first_response = self.client.post(
            f"/api/v1/interactions/lessons/{self.lesson1.id}/rate/",
            {"star_count": 5, "comment": "Great lesson"},
            format="json",
        )
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(first_response.data["current_rating"], 5.0)

        second_response = self.client.post(
            f"/api/v1/interactions/lessons/{self.lesson1.id}/rate/",
            {"star_count": 3, "comment": "Actually average"},
            format="json",
        )
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.data["current_rating"], 3.0)
        self.assertEqual(LessonRate.objects.filter(user=self.user, lesson=self.lesson1).count(), 1)

    def test_non_enrolled_user_cannot_interact(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            f"/api/v1/interactions/lessons/{self.lesson1.id}/progress/",
            {"watch_percent": 90},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
