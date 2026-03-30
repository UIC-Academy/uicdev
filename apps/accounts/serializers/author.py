from rest_framework.serializers import ModelSerializer

from apps.accounts.models import Author


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
