from rest_framework import serializers

from apps.courses.models import Course


class CheckoutCreateSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    return_url = serializers.URLField(required=False, allow_blank=True)

    def validate_course_id(self, value):
        if not Course.objects.filter(id=value, is_active=True, is_published=True).exists():
            raise serializers.ValidationError("Course not found or unavailable")
        return value


class PaymentStatusUpdateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["failed", "canceled", "refunded"])
