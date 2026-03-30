from rest_framework.serializers import ModelSerializer

from apps.common.models import Country, Region


class CountrySerializer(ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RegionSerializer(ModelSerializer):
    class Meta:
        model = Region
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
