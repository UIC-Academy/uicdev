from decimal import Decimal

from rest_framework import serializers

from apps.courses.models import Course


class CheckoutCreateSerializer(serializers.Serializer):
    wallet_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("500.00"), max_value=10000000)
    return_url = serializers.URLField(required=False, allow_blank=True)


class CoursePurchaseSerializer(serializers.Serializer):
    wallet_id = serializers.IntegerField()
    course_id = serializers.PrimaryKeyRelatedField(queryset=Course.objects.filter(is_active=True, is_published=True))


class PaymentStatusUpdateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["failed", "canceled", "refunded"])
