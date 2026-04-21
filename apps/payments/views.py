import base64
import urllib.parse
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.interactions.models import Enrollment
from apps.payments.choices import CurrencyEnum, OrderStatusEnum, PaymentVendorEnum, TransactionStatusEnum
from apps.payments.models import Order, Transaction
from apps.payments.serializers import CheckoutCreateSerializer, PaymentStatusUpdateSerializer

PAYMENT_STATUS_SUCCESS = "0"
PAYMENT_STATUS_INVALID_AMOUNT = "5"
PAYMENT_STATUS_ORDER_NOT_FOUND = "303"
PAYMENT_STATUS_CUSTOM = "+1"


def _status_result(status_code: str, status_text: str, request_id):
    return Response(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "status": status_code,
                "statusText": status_text,
            },
        }
    )


def _decode_basic_auth_header(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Basic "):
        return None, None
    token = auth_header.split(" ", 1)[1].strip()
    try:
        decoded = base64.b64decode(token).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:  # noqa: BLE001
        return None, None
    return username, password


class CheckoutCreateAPIView(GenericAPIView):
    serializer_class = CheckoutCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course = serializer.validated_data["course_id"]
        return_url = serializer.validated_data.get("return_url") or settings.FAKEPAY_DEFAULT_RETURN_URL

        from apps.courses.models import Course

        course_obj = Course.objects.get(id=course)
        user = request.user

        if Enrollment.objects.filter(user=user, course=course_obj).exists():
            raise ValidationError("Course is already purchased by this user")

        with transaction.atomic():
            order, created = Order.objects.get_or_create(
                user=user,
                course=course_obj,
                defaults={
                    "amount": course_obj.price,
                    "currency": course_obj.currency,
                    "status": OrderStatusEnum.CREATED,
                },
            )

            if not created and order.status == OrderStatusEnum.SUCCESS:
                raise ValidationError("Course is already purchased by this user")

            if not created and order.status != OrderStatusEnum.CREATED:
                order.status = OrderStatusEnum.CREATED
                order.amount = course_obj.price
                order.currency = course_obj.currency
                order.save(update_fields=["status", "amount", "currency", "updated_at"])

            transaction_obj = Transaction.objects.filter(order=order).order_by("-created_at").first()
            if not transaction_obj:
                Transaction.objects.create(
                    order=order,
                    amount=order.amount,
                    vendor=PaymentVendorEnum.OTHER,
                    status=TransactionStatusEnum.PENDING,
                    currency=order.currency,
                )
            else:
                transaction_obj.status = TransactionStatusEnum.PENDING
                transaction_obj.amount = order.amount
                transaction_obj.currency = order.currency
                transaction_obj.vendor = PaymentVendorEnum.OTHER
                transaction_obj.save(update_fields=["status", "amount", "currency", "vendor", "updated_at"])

        query = {
            "merchant_id": settings.FAKEPAY_MERCHANT_ID,
            "amount": str(order.amount),
            "currency_id": "860" if order.currency == CurrencyEnum.UZS else "840",
            "return_url": return_url,
            "account.order_id": str(order.id),
            "account.user_id": str(user.id),
            "account.course_id": str(course_obj.id),
        }
        encoded = base64.b64encode(urllib.parse.urlencode(query).encode()).decode()
        checkout_url = f"{settings.FAKEPAY_BASE_URL}/checkout/create/{encoded}"

        return Response(
            {
                "order_id": order.id,
                "course_id": course_obj.id,
                "course_name": course_obj.name,
                "amount": str(order.amount),
                "currency": order.currency,
                "checkout_url": checkout_url,
                "status": order.status,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentCallbackAPIView(GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        expected_username = settings.FAKEPAY_CALLBACK_AUTH_USERNAME
        expected_password = settings.FAKEPAY_CALLBACK_AUTH_PASSWORD
        username, password = _decode_basic_auth_header(request)
        if username != expected_username or password != expected_password:
            return Response({"detail": "Unauthorized callback"}, status=status.HTTP_401_UNAUTHORIZED)

        request_id = request.data.get("id")
        method = request.data.get("method")
        params = request.data.get("params") or {}
        account = params.get("account") or {}
        order_id = account.get("order_id")

        if not order_id:
            return _status_result(PAYMENT_STATUS_ORDER_NOT_FOUND, "order_not_found", request_id)

        try:
            order = Order.objects.select_related("course", "user").get(id=order_id)
        except Order.DoesNotExist:
            return _status_result(PAYMENT_STATUS_ORDER_NOT_FOUND, "order_not_found", request_id)

        if method == "transaction.check":
            return self._handle_check(order=order, params=params, request_id=request_id)
        if method == "transaction.perform":
            return self._handle_perform(order=order, request_id=request_id)

        return _status_result(PAYMENT_STATUS_CUSTOM, "unsupported_method", request_id)

    def _handle_check(self, order: Order, params: dict, request_id):
        if Enrollment.objects.filter(user=order.user, course=order.course).exists():
            return _status_result(PAYMENT_STATUS_CUSTOM, "already_enrolled", request_id)

        try:
            incoming_amount = Decimal(str(params.get("amount", "0")))
            incoming_currency = int(params.get("currency", 0))
        except Exception:  # noqa: BLE001
            return _status_result(PAYMENT_STATUS_INVALID_AMOUNT, "invalid_amount_or_currency", request_id)
        expected_currency = 860 if order.currency == CurrencyEnum.UZS else 840

        if incoming_amount != order.amount or incoming_currency != expected_currency:
            return _status_result(PAYMENT_STATUS_INVALID_AMOUNT, "invalid_amount_or_currency", request_id)

        return _status_result(PAYMENT_STATUS_SUCCESS, "OK", request_id)

    def _handle_perform(self, order: Order, request_id):
        with transaction.atomic():
            order = Order.objects.select_for_update().select_related("course", "user").get(id=order.id)

            if Enrollment.objects.filter(user=order.user, course=order.course).exists():
                if order.status != OrderStatusEnum.SUCCESS:
                    order.status = OrderStatusEnum.SUCCESS
                    order.save(update_fields=["status", "updated_at"])
                txn = Transaction.objects.filter(order=order).order_by("-created_at").first()
                if txn:
                    txn.status = TransactionStatusEnum.SUCCESS
                    txn.save(update_fields=["status", "updated_at"])
                return _status_result(PAYMENT_STATUS_SUCCESS, "OK", request_id)

            order.status = OrderStatusEnum.SUCCESS
            order.save(update_fields=["status", "updated_at"])

            txn = Transaction.objects.filter(order=order).order_by("-created_at").first()
            if txn:
                txn.status = TransactionStatusEnum.SUCCESS
                txn.save(update_fields=["status", "updated_at"])
            else:
                Transaction.objects.create(
                    order=order,
                    amount=order.amount,
                    vendor=PaymentVendorEnum.OTHER,
                    status=TransactionStatusEnum.SUCCESS,
                    currency=order.currency,
                )

            Enrollment.objects.get_or_create(user=order.user, course=order.course)

        return _status_result(PAYMENT_STATUS_SUCCESS, "OK", request_id)


class PaymentOrderStatusAPIView(GenericAPIView):
    serializer_class = PaymentStatusUpdateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]

        order = Order.objects.filter(id=order_id, user=request.user).select_related("course").first()
        if not order:
            raise ValidationError("Order not found")

        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order.id)
            txn = Transaction.objects.filter(order=order).order_by("-created_at").first()

            if action == "failed":
                order.status = OrderStatusEnum.FAILED
                if txn:
                    txn.status = TransactionStatusEnum.FAILED
                    txn.save(update_fields=["status", "updated_at"])
            elif action == "canceled":
                order.status = OrderStatusEnum.FAILED
                if txn:
                    txn.status = TransactionStatusEnum.CANCELED
                    txn.save(update_fields=["status", "updated_at"])
            elif action == "refunded":
                order.status = OrderStatusEnum.FAILED
                if txn:
                    txn.status = TransactionStatusEnum.FAILED
                    txn.save(update_fields=["status", "updated_at"])
                Enrollment.objects.filter(user=order.user, course=order.course).delete()

            order.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "order_id": order.id,
                "status": order.status,
                "action": action,
            }
        )
