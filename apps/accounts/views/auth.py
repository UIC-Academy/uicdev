from django.core.cache import cache
from django.db import transaction
from django.utils.crypto import get_random_string
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    GenericAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User, Wallet
from apps.accounts.serializers import UserProfileSerializer, UserRegisterConfirmSerializer, UserRegisterSerializer
from apps.accounts.tasks import send_sms_to_phone_task
from apps.accounts.utils import generate_code
from apps.notifications.models import Notification
from apps.payments.models import Transaction


def _generate_deleted_phone(user_id: int) -> str:
    for _ in range(10):
        candidate = f"d{user_id}{get_random_string(8, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyz')}"[:20]
        if not User.objects.filter(phone=candidate).exists():
            return candidate
    raise ValidationError("Could not generate a unique deleted phone value")


class UserRegisterAPIView(GenericAPIView):
    queryset = User.objects.filter(is_active=True, is_deleted=False)
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        password = serializer.validated_data["password"]
        with transaction.atomic():
            user = User.objects.select_for_update().filter(phone=phone).first()
            if user and user.is_active and not user.is_deleted:
                raise ValidationError("User already exists and is active")

            # agar user o'chirilgan bo'lsa, phone garbage qilinadi
            if user and user.is_deleted:
                user.phone = _generate_deleted_phone(user.pk)
                user.is_active = False
                user.save(update_fields=["phone", "is_active"])
                user = None

            if user is None:
                # bunday user yo'q: yangi user yaratiladi
                user = serializer.save()
            else:
                # bunday user bor, lekin active emas
                user.set_password(password)
                user.is_active = False
                user.save(update_fields=["password", "is_active"])

        code = generate_code()
        sms_phone = user.phone.replace("+", "")
        send_sms_to_phone_task.delay(phone=sms_phone, message=f"UICdev platformasiga kirish uchun kod: {code}")
        cache.set(f"sms_code:{user.phone}", code, 60 * 2)
        return Response({"message": "SMS sent to the phone."})


class UserRegisterConfirmAPIView(GenericAPIView):
    queryset = User.objects.filter(is_active=True, is_deleted=False)
    serializer_class = UserRegisterConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]
        user = User.objects.filter(phone=phone, is_deleted=False).first()

        if not user:
            raise ValidationError("User not found")
        cached_code = cache.get(f"sms_code:{phone}")
        if not cached_code:
            raise ValidationError("Code expired")
        if code != cached_code:
            raise ValidationError("Invalid code")

        with transaction.atomic():
            user.is_active = True
            user.save(update_fields=["is_active"])

            wallet = Wallet.objects.create(user=user)
            Transaction.objects.create(wallet=wallet, amount=10000)

            Notification.objects.create(
                user=user,
                title="Welcome",
                message="You are now registered on UICdev platform. Your wallet is filled with 10000 soums as a gift!",
            )

        cache.delete(f"sms_code:{phone}")

        return Response(UserProfileSerializer(user).data)


class UserProfileAPIView(RetrieveAPIView):
    queryset = User.objects.filter(is_active=True, is_deleted=False).select_related("avatar")
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get_object(self):
        return self.request.user


class UserDisableAPIView(GenericAPIView):
    queryset = User.objects.filter(is_active=True, is_deleted=False)
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def delete(self, request, *args, **kwargs):
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            if user.is_deleted:
                return Response({"message": "Account already disabled."})

            old_phone = user.phone
            user.phone = _generate_deleted_phone(user.pk)
            user.is_active = False
            user.is_deleted = True
            user.save(update_fields=["phone", "is_active", "is_deleted"])

        cache.delete(f"sms_code:{old_phone}")

        # TODO: account o'chganida hamyon ham is_deleted=True bolishi kk
        return Response({"message": "Account disabled successfully."})
