from rest_framework.serializers import ModelSerializer

from apps.accounts.models import Author, Education


class EducationSerializer(ModelSerializer):
    class Meta:
        model = Education
        fields = ["id", "name", "type", "website_url", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class AuthorSerializer(ModelSerializer):
    class Meta:
        model = Author
        fields = [
            "id",
            "first_name",
            "last_name",
            "description",
            "avatar",
            "experience_years",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
