from django.core.validators import RegexValidator
from rest_framework import serializers

from apps.accounts.models import User, Wallet
from apps.accounts.serializers.profile import (
    UserCertificateSerializer,
    UserEducationSerializer,
    UserExperienceSerializer,
)
from apps.common.models import Country, Region


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


class CountryInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name"]


class RegionInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "name"]


class WalletInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["id", "balance", "is_deleted"]


class UserProfileSerializer(serializers.ModelSerializer):
    educations = UserEducationSerializer(many=True, read_only=True)
    experiences = UserExperienceSerializer(many=True, read_only=True)
    certificates = UserCertificateSerializer(many=True, read_only=True)
    country = CountryInlineSerializer(read_only=True)
    region = RegionInlineSerializer(read_only=True)
    wallet = WalletInlineSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "wallet",
            "first_name",
            "last_name",
            "avatar",
            "bio",
            "age",
            "gender",
            "stars_balance",
            "country",
            "region",
            "educations",
            "experiences",
            "certificates",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "phone",
            "stars_balance",
            "educations",
            "experiences",
            "certificates",
            "created_at",
            "updated_at",
        ]
