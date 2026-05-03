import base64
import logging
import urllib.parse
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Wallet
from apps.courses.models import Course
from apps.interactions.models import Enrollment
from apps.payments.choices import (
    CurrencyEnum,
    OrderStatusEnum,
    PaymentVendorEnum,
    TransactionStatusEnum,
    TransactionTypeEnum,
)
from apps.payments.models import Order, Transaction
from apps.payments.serializers import CheckoutCreateSerializer, CoursePurchaseSerializer, PaymentStatusUpdateSerializer

logger = logging.getLogger(__name__)

PAYMENT_STATUS_SUCCESS = "0"
PAYMENT_STATUS_INVALID_AMOUNT = "5"
PAYMENT_STATUS_ORDER_NOT_FOUND = "303"
PAYMENT_STATUS_CUSTOM = "+1"
TOP_UP_CURRENCY = CurrencyEnum.UZS


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

        wallet_id = serializer.validated_data["wallet_id"]
        amount = serializer.validated_data["amount"]
        return_url = serializer.validated_data.get("return_url") or settings.FAKEPAY_DEFAULT_RETURN_URL

        wallet = Wallet.objects.filter(id=wallet_id, user=request.user, is_deleted=False).first()
        if not wallet:
            raise ValidationError("Wallet not found")

        with transaction.atomic():
            transaction_obj = Transaction.objects.create(
                wallet=wallet,
                order=None,
                amount=amount,
                type=TransactionTypeEnum.TOP_UP,
                vendor=PaymentVendorEnum.OTHER,
                status=TransactionStatusEnum.PENDING,
                currency=TOP_UP_CURRENCY,
            )

        query = {
            "merchant_id": settings.FAKEPAY_MERCHANT_ID,
            "amount": str(transaction_obj.amount),
            "currency_id": "860",
            "return_url": return_url,
            "account.transaction_id": str(transaction_obj.id),
            "account.wallet_id": str(wallet.id),
            "account.user_id": str(request.user.id),
        }
        encoded = base64.b64encode(urllib.parse.urlencode(query).encode()).decode()
        checkout_url = f"{settings.FAKEPAY_BASE_URL}/checkout/create/{encoded}"

        return Response(
            {
                "transaction_id": transaction_obj.id,
                "wallet_id": wallet.id,
                "amount": str(transaction_obj.amount),
                "currency": transaction_obj.currency,
                "checkout_url": checkout_url,
                "status": transaction_obj.status,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentCallbackAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        expected_username = settings.FAKEPAY_CALLBACK_AUTH_USERNAME
        expected_password = settings.FAKEPAY_CALLBACK_AUTH_PASSWORD
        username, password = _decode_basic_auth_header(request)
        if username != expected_username or password != expected_password:
            logger.warning("payment_callback_unauthorized")
            return Response({"detail": "Unauthorized callback"}, status=status.HTTP_401_UNAUTHORIZED)

        request_id = request.data.get("id")
        method = request.data.get("method")
        params = request.data.get("params") or {}
        account = params.get("account") or {}
        transaction_id = account.get("transaction_id")
        print(">>>", transaction_id)

        if not transaction_id:
            logger.warning("payment_callback_missing_transaction", extra={"request_id": request_id, "method": method})
            return _status_result(PAYMENT_STATUS_ORDER_NOT_FOUND, "transaction_not_found", request_id)

        try:
            transaction_obj = Transaction.objects.select_related("wallet__user").get(
                id=int(transaction_id),
                order__isnull=True,
                type=TransactionTypeEnum.TOP_UP,
            )
        except Transaction.DoesNotExist:
            logger.warning(
                "payment_callback_unknown_transaction",
                extra={"request_id": request_id, "method": method, "transaction_id": transaction_id},
            )
            return _status_result(PAYMENT_STATUS_ORDER_NOT_FOUND, "transaction_not_found", request_id)

        if method == "transaction.check":
            return self._handle_check(transaction_obj=transaction_obj, params=params, request_id=request_id)
        if method == "transaction.perform":
            return self._handle_perform(transaction_obj=transaction_obj, request_id=request_id)

        return _status_result(PAYMENT_STATUS_CUSTOM, "unsupported_method", request_id)

    def _handle_check(self, transaction_obj: Transaction, params: dict, request_id):
        try:
            incoming_amount = Decimal(str(params.get("amount", "0")))
            incoming_currency = int(params.get("currency", 0))
        except Exception:  # noqa: BLE001
            return _status_result(PAYMENT_STATUS_INVALID_AMOUNT, "invalid_amount_or_currency", request_id)
        expected_currency = 860 if transaction_obj.currency == CurrencyEnum.UZS else 840

        if incoming_amount != transaction_obj.amount or incoming_currency != expected_currency:
            logger.warning(
                "payment_callback_invalid_amount",
                extra={
                    "transaction_id": transaction_obj.id,
                    "incoming_amount": str(incoming_amount),
                    "expected_amount": str(transaction_obj.amount),
                    "incoming_currency": incoming_currency,
                    "expected_currency": expected_currency,
                },
            )
            return _status_result(PAYMENT_STATUS_INVALID_AMOUNT, "invalid_amount_or_currency", request_id)

        return _status_result(PAYMENT_STATUS_SUCCESS, "OK", request_id)

    def _handle_perform(self, transaction_obj: Transaction, request_id):
        with transaction.atomic():
            transaction_obj = Transaction.objects.select_for_update().get(id=transaction_obj.id)
            wallet = Wallet.objects.select_for_update().get(id=transaction_obj.wallet_id)

            if transaction_obj.status == TransactionStatusEnum.SUCCESS:
                return _status_result(PAYMENT_STATUS_SUCCESS, "OK", request_id)

            if transaction_obj.status != TransactionStatusEnum.PENDING:
                return _status_result(PAYMENT_STATUS_CUSTOM, "invalid_transaction_status", request_id)

            wallet.balance += transaction_obj.amount
            wallet.save(update_fields=["balance", "updated_at"])
            transaction_obj.status = TransactionStatusEnum.SUCCESS
            transaction_obj.save(update_fields=["status", "updated_at"])
            logger.info(
                "wallet_top_up_performed",
                extra={
                    "transaction_id": transaction_obj.id,
                    "wallet_id": wallet.id,
                    "user_id": wallet.user_id,
                    "amount": str(transaction_obj.amount),
                },
            )

        return _status_result(PAYMENT_STATUS_SUCCESS, "OK", request_id)


class CoursePurchaseAPIView(GenericAPIView):
    serializer_class = CoursePurchaseSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wallet_id = serializer.validated_data["wallet_id"]
        course: Course = serializer.validated_data["course_id"]

        if Enrollment.objects.filter(user=request.user, course=course).exists():
            raise ValidationError("Course is already purchased by this user")

        with transaction.atomic():
            wallet = (
                Wallet.objects.select_for_update()
                .filter(
                    id=wallet_id,
                    user=request.user,
                    is_deleted=False,
                )
                .first()
            )
            if not wallet:
                raise ValidationError("Wallet not found")

            if wallet.balance < course.price:
                raise ValidationError("Insufficient wallet balance")

            order, created = Order.objects.select_for_update().get_or_create(
                user=request.user,
                course=course,
                defaults={
                    "amount": course.price,
                    "currency": course.currency,
                    "status": OrderStatusEnum.CREATED,
                },
            )
            if not created and order.status == OrderStatusEnum.SUCCESS:
                raise ValidationError("Course is already purchased by this user")

            wallet.balance -= course.price
            wallet.save(update_fields=["balance", "updated_at"])

            order.amount = course.price
            order.currency = course.currency
            order.status = OrderStatusEnum.SUCCESS
            order.save(update_fields=["amount", "currency", "status", "updated_at"])

            transaction_obj = Transaction.objects.create(
                wallet=wallet,
                order=order,
                amount=course.price,
                type=TransactionTypeEnum.PURCHASE,
                vendor=PaymentVendorEnum.OTHER,
                status=TransactionStatusEnum.SUCCESS,
                currency=course.currency,
            )
            Enrollment.objects.get_or_create(user=request.user, course=course)

        logger.info(
            "course_purchased_from_wallet",
            extra={
                "order_id": order.id,
                "transaction_id": transaction_obj.id,
                "wallet_id": wallet.id,
                "user_id": request.user.id,
                "course_id": course.id,
            },
        )

        return Response(
            {
                "order_id": order.id,
                "transaction_id": transaction_obj.id,
                "wallet_id": wallet.id,
                "course_id": course.id,
                "amount": str(order.amount),
                "currency": order.currency,
                "wallet_balance": str(wallet.balance),
                "status": order.status,
                "enrolled": True,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentTransactionStatusAPIView(GenericAPIView):
    serializer_class = PaymentStatusUpdateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, transaction_id, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]

        transaction_obj = (
            Transaction.objects.filter(
                id=transaction_id,
                wallet__user=request.user,
                order__isnull=True,
                type=TransactionTypeEnum.TOP_UP,
            )
            .select_related("wallet")
            .first()
        )
        if not transaction_obj:
            raise ValidationError("Transaction not found")

        with transaction.atomic():
            transaction_obj = Transaction.objects.select_for_update().get(id=transaction_obj.id)
            wallet = Wallet.objects.select_for_update().get(id=transaction_obj.wallet_id)

            if action == "failed":
                transaction_obj.status = TransactionStatusEnum.FAILED
            elif action == "canceled":
                transaction_obj.status = TransactionStatusEnum.CANCELED
            elif action == "refunded":
                if transaction_obj.status == TransactionStatusEnum.SUCCESS:
                    if wallet.balance < transaction_obj.amount:
                        raise ValidationError("Wallet balance is lower than refund amount")
                    wallet.balance -= transaction_obj.amount
                    wallet.save(update_fields=["balance", "updated_at"])
                transaction_obj.status = TransactionStatusEnum.FAILED
                logger.info(
                    "wallet_top_up_refunded",
                    extra={"transaction_id": transaction_obj.id, "wallet_id": wallet.id, "user_id": request.user.id},
                )

            transaction_obj.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "transaction_id": transaction_obj.id,
                "status": transaction_obj.status,
                "action": action,
                "wallet_balance": str(wallet.balance),
            }
        )
