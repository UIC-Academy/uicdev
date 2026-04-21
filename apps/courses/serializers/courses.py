from rest_framework.serializers import ModelSerializer, SerializerMethodField

from apps.accounts.models import Author
from apps.common.models import Media
from apps.courses.models import Category, Course, Lesson, Module


class AuthorCourseSerializer(ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "first_name", "last_name"]


class BannerCourseSerializer(ModelSerializer):
    class Meta:
        model = Media
        fields = ["id", "file"]


class CategoryCourseSerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class LessonCourseSerializer(ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "name", "description", "type", "lesson_order", "is_active"]


class ModuleCourseSerializer(ModelSerializer):
    lessons = SerializerMethodField()

    class Meta:
        model = Module
        fields = ["id", "name", "course_order", "lessons"]

    def get_lessons(self, obj):
        lessons = [lesson for lesson in obj.lessons.all() if lesson.is_active]
        return LessonCourseSerializer(lessons, many=True).data


class CourseSerializer(ModelSerializer):
    author = AuthorCourseSerializer(read_only=True)
    banner = BannerCourseSerializer(read_only=True)
    category = CategoryCourseSerializer(read_only=True)
    tags = SerializerMethodField()
    modules = SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "author",
            "banner",
            "name",
            "description",
            "category",
            "tags",
            "modules",
            "reward_stars",
            "is_active",
            "is_published",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "category",
            "tags",
            "reward_stars",
            "created_at",
            "updated_at",
        ]

    def get_tags(self, obj):
        return [{"id": tag.id, "name": tag.name} for tag in obj.tags.all()]

    def get_modules(self, obj):
        return ModuleCourseSerializer(obj.modules.all(), many=True).data
