from rest_framework.serializers import ModelSerializer

from apps.accounts.models import Education


class EducationSerializer(ModelSerializer):
    class Meta:
        model = Education
        fields = ["id", "name", "type", "website_url", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
