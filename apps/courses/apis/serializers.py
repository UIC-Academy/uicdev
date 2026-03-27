from rest_framework.serializers import ModelSerializer

from apps.courses.models import Category, Course, Tag


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CourseSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "author",
            "banner",
            "name",
            "description",
            "category",
            "reward_stars",
            "is_active",
            "is_published",
            "created_at",
            "updated_at",
        ]
        read_only_fieldds = [
            "id",
            "author",
            "category",
            "reward_stars",
            "created_at",
            "updated_at",
        ]
