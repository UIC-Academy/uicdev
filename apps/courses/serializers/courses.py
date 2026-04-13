from rest_framework.serializers import ModelSerializer

from apps.courses.models import Course


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
