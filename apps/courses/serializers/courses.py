from rest_framework.serializers import ModelSerializer, SerializerMethodField

from apps.accounts.models import Author
from apps.common.models import Media
from apps.courses.models import Category, Course


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


class CourseSerializer(ModelSerializer):
    author = AuthorCourseSerializer(read_only=True)
    banner = BannerCourseSerializer(read_only=True)
    category = CategoryCourseSerializer(read_only=True)
    tags = SerializerMethodField()

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
