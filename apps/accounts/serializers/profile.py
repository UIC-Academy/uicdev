from rest_framework import serializers

from apps.accounts.models import UserCertificate, UserEducation, UserExperience
from apps.common.models import Media


class UserEducationSerializer(serializers.ModelSerializer):
    education_name = serializers.CharField(source="education.name", read_only=True)

    class Meta:
        model = UserEducation
        fields = [
            "id",
            "education",
            "education_name",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "education_name", "created_at", "updated_at"]

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "end_date cannot be earlier than start_date"})
        return attrs


class UserExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserExperience
        fields = [
            "id",
            "name",
            "position",
            "website_url",
            "skills",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "end_date cannot be earlier than start_date"})
        return attrs


class UserCertificateSerializer(serializers.ModelSerializer):
    attachment = serializers.PrimaryKeyRelatedField(
        queryset=Media.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = UserCertificate
        fields = [
            "id",
            "course",
            "name",
            "attachment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_attachment(self, value):
        if value is None:
            return value

        # Validate uploaded media as certificate-like file.
        file = value.file
        max_size = 10 * 1024 * 1024
        if file.size > max_size:
            raise serializers.ValidationError("Attachment size must be <= 10MB")

        allowed_suffixes = (".pdf", ".png", ".jpg", ".jpeg")
        if not file.name.lower().endswith(allowed_suffixes):
            raise serializers.ValidationError("Attachment type must be one of: pdf, png, jpg, jpeg")
        return value
