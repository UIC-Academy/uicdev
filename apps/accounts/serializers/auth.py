from django.core.validators import RegexValidator
from rest_framework import serializers

from apps.accounts.models import User


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "password", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            # Register endpoint must allow existing inactive/deleted users to request SMS again.
            "phone": {"validators": []},
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        user = User(
            phone=validated_data["phone"],
            is_active=False,
            is_deleted=False,
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserRegisterConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True, max_length=20, validators=[RegexValidator(r"^\+?1?\d{9,15}$")])
    code = serializers.CharField(required=True, max_length=4)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "first_name", "last_name", "avatar", "bio", "created_at", "updated_at"]
        read_only_fields = ["id", "password", "created_at", "updated_at"]
