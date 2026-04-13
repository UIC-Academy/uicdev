from django.core.cache import cache
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    GenericAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.serializers import UserProfileSerializer, UserRegisterConfirmSerializer, UserRegisterSerializer
from apps.accounts.tasks import send_sms_to_phone_task
from apps.accounts.utils import generate_code


class UserRegisterAPIView(GenericAPIView):
    queryset = User.objects.filter(is_active=True, is_deleted=False)
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        existing_user = User.objects.filter(phone=serializer.validated_data["phone"])
        if not existing_user.exists():
            user = serializer.save()

        if existing_user.filter(is_active=True):
            raise ValidationError("User already exists and is active")

        user = existing_user.first()
        code = generate_code()
        phone = user.phone.replace("+", "")
        send_sms_to_phone_task.delay(phone=phone, message=f"UICdev platformasiga kirish uchun kod: {code}")
        cache.set(f"sms_code:{user.phone}", code, 60 * 2)
        return Response({"message": "SMS sent to the phone."})


class UserRegisterConfirmAPIView(GenericAPIView):
    queryset = User.objects.filter(is_active=True, is_deleted=False)
    serializer_class = UserRegisterConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        phone = request.data.get("phone")
        code = request.data.get("code")
        user = User.objects.filter(phone=phone).first()
        if not user:
            raise ValidationError("User not found")
        if not cache.get(f"sms_code:{phone}"):
            raise ValidationError("Code expired")
        if code != cache.get(f"sms_code:{phone}"):
            raise ValidationError("Invalid code")
        user.is_active = True
        user.save()
        return Response(UserProfileSerializer(user).data)


class UserProfileAPIView(RetrieveAPIView):
    queryset = User.objects.filter(is_active=True, is_deleted=False).select_related("avatar")
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get_object(self):
        return self.request.user
