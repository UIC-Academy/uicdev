from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Author, User
from apps.courses.choices import LessonTypeChoices
from apps.courses.models import Category, Course, Lesson, Module
from apps.payments.choices import CurrencyEnum


class CourseBrowseFlowTests(APITestCase):
    list_url = "/api/v1/courses/"

    def setUp(self):
        self.author = Author.objects.create(
            first_name="Test",
            last_name="Author",
            experience_years=5,
        )
        self.category = Category.objects.create(name="Backend")

    def test_course_list_returns_only_active_courses_for_anonymous_and_authenticated_user(self):
        active_course = Course.objects.create(
            author=self.author,
            name="Active Course",
            category=self.category,
            is_active=True,
            is_published=True,
            price=10000,
            currency=CurrencyEnum.UZS,
        )
        Course.objects.create(
            author=self.author,
            name="Inactive Course",
            category=self.category,
            is_active=False,
            is_published=True,
            price=10000,
            currency=CurrencyEnum.UZS,
        )

        anon_response = self.client.get(self.list_url)
        self.assertEqual(anon_response.status_code, status.HTTP_200_OK)
        anon_ids = [item["id"] for item in anon_response.data["results"]]
        self.assertEqual(anon_ids, [active_course.id])

        user = User.objects.create_user(phone="+998904444444", password="password", is_active=True)
        self.client.force_authenticate(user=user)

        auth_response = self.client.get(self.list_url)
        self.assertEqual(auth_response.status_code, status.HTTP_200_OK)
        auth_ids = [item["id"] for item in auth_response.data["results"]]
        self.assertEqual(auth_ids, [active_course.id])

    def test_course_retrieve_includes_modules_and_active_lessons_in_order(self):
        course = Course.objects.create(
            author=self.author,
            name="Detailed Course",
            category=self.category,
            is_active=True,
            is_published=True,
            price=12000,
            currency=CurrencyEnum.UZS,
        )
        module_second = Module.objects.create(course=course, name="Module 2", course_order=2)
        module_first = Module.objects.create(course=course, name="Module 1", course_order=1)

        Lesson.objects.create(
            module=module_first,
            name="Lesson 2",
            type=LessonTypeChoices.VIDEO,
            lesson_order=2,
            is_active=True,
        )
        Lesson.objects.create(
            module=module_first,
            name="Lesson 1",
            type=LessonTypeChoices.ARTICLE,
            lesson_order=1,
            is_active=True,
        )
        Lesson.objects.create(
            module=module_first,
            name="Lesson hidden",
            type=LessonTypeChoices.FILE,
            lesson_order=3,
            is_active=False,
        )
        Lesson.objects.create(
            module=module_second,
            name="Lesson 3",
            type=LessonTypeChoices.AUDIO,
            lesson_order=1,
            is_active=True,
        )

        response = self.client.get(f"/api/v1/courses/{course.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        modules = response.data["modules"]
        self.assertEqual([module["name"] for module in modules], ["Module 1", "Module 2"])
        self.assertEqual(
            [lesson["name"] for lesson in modules[0]["lessons"]],
            ["Lesson 1", "Lesson 2"],
        )
        self.assertEqual([lesson["name"] for lesson in modules[1]["lessons"]], ["Lesson 3"])
