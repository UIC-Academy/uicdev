from django.core.cache import cache
from django.core.validators import RegexValidator
from rest_framework import serializers

from apps.accounts.models import User
from apps.common.utils import generate_sms_code


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "password", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def save(self, **kwargs):
        user = User(
            phone=self.validated_data["phone"],
            password=self.validated_data["password"],
            is_active=False,
            is_deleted=False,
        )
        user.save()
        code = generate_sms_code()
        cache.set(f"sms_code:{user.phone}", code, 60 * 2)
        return user


class UserRegisterConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True, max_length=20, validators=[RegexValidator(r"^\+?1?\d{9,15}$")])
    code = serializers.CharField(required=True, max_length=6)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "first_name", "last_name", "avatar", "bio", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
