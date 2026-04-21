from rest_framework import serializers

from apps.interactions.models import LessonRate


class LessonProgressUpdateSerializer(serializers.Serializer):
    watch_percent = serializers.IntegerField(min_value=0, max_value=100)


class LessonFavoriteSerializer(serializers.Serializer):
    is_favorite = serializers.BooleanField()


class LessonRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonRate
        fields = ["star_count", "comment"]

    def validate_star_count(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("star_count must be between 1 and 5")
        return value
