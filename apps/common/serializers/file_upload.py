from rest_framework.serializers import ModelSerializer

from apps.common.models import Media


class FileUploadSerializer(ModelSerializer):
    class Meta:
        model = Media
        fields = ["id", "file", "created_at"]
        read_only_fields = ["id", "created_at"]
