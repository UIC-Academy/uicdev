import base64
from decimal import Decimal

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Author, User
from apps.courses.models import Category, Course
from apps.interactions.models import Enrollment
from apps.payments.choices import CurrencyEnum, OrderStatusEnum, TransactionStatusEnum
from apps.payments.models import Order, Transaction


@override_settings(
    FAKEPAY_BASE_URL="http://localhost:8001",
    FAKEPAY_MERCHANT_ID="571c06fb-6c61-4ef7-8567-5511abaf12b5",
    FAKEPAY_CALLBACK_AUTH_USERNAME="uic_callback",
    FAKEPAY_CALLBACK_AUTH_PASSWORD="uic_callback_pass",
    FAKEPAY_DEFAULT_RETURN_URL="http://localhost:3000/payment-result",
)
class PaymentIntegrationFlowTests(APITestCase):
    checkout_url = "/api/v1/payments/checkout/"
    callback_url = "/api/v1/payments/callback/"

    def setUp(self):
        self.user = User.objects.create_user(phone="+998907777771", password="password", is_active=True)
        self.other_user = User.objects.create_user(phone="+998907777772", password="password", is_active=True)
        self.client.force_authenticate(user=self.user)

        author = Author.objects.create(first_name="Pay", last_name="Author")
        category = Category.objects.create(name="Payments")
        self.course = Course.objects.create(
            author=author,
            category=category,
            name="Payment Course",
            price=Decimal("150000.00"),
            currency=CurrencyEnum.UZS,
            is_active=True,
            is_published=True,
        )

    def _basic_auth_header(self, username: str, password: str) -> str:
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        return f"Basic {token}"

    def test_checkout_creates_order_and_pending_transaction(self):
        response = self.client.post(self.checkout_url, {"course_id": self.course.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("/checkout/create/", response.data["checkout_url"])

        order = Order.objects.get(id=response.data["order_id"])
        self.assertEqual(order.user_id, self.user.id)
        self.assertEqual(order.course_id, self.course.id)
        self.assertEqual(order.amount, Decimal("150000.00"))
        self.assertEqual(order.status, OrderStatusEnum.CREATED)

        txn = Transaction.objects.get(order=order)
        self.assertEqual(txn.status, TransactionStatusEnum.PENDING)

    def test_checkout_blocks_duplicate_purchase_if_enrolled(self):
        Enrollment.objects.create(user=self.user, course=self.course)
        response = self.client.post(self.checkout_url, {"course_id": self.course.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already purchased", str(response.data).lower())

    def test_callback_requires_basic_auth(self):
        self.client.force_authenticate(user=None)
        payload = {"jsonrpc": "2.0", "id": 1, "method": "transaction.check", "params": {"account": {"order_id": 1}}}
        response = self.client.post(self.callback_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_callback_check_and_perform_success_creates_enrollment(self):
        order = Order.objects.create(
            user=self.user,
            course=self.course,
            amount=Decimal("150000.00"),
            currency=CurrencyEnum.UZS,
            status=OrderStatusEnum.CREATED,
        )
        Transaction.objects.create(
            order=order,
            amount=order.amount,
            currency=order.currency,
            vendor="other",
            status=TransactionStatusEnum.PENDING,
        )

        self.client.force_authenticate(user=None)
        headers = {"HTTP_AUTHORIZATION": self._basic_auth_header("uic_callback", "uic_callback_pass")}
        check_payload = {
            "jsonrpc": "2.0",
            "id": 1001,
            "method": "transaction.check",
            "params": {
                "account": {"order_id": order.id},
                "amount": 150000,
                "amount_tiyin": 15000000,
                "currency": 860,
            },
        }
        check_response = self.client.post(self.callback_url, check_payload, format="json", **headers)
        self.assertEqual(check_response.status_code, status.HTTP_200_OK)
        self.assertEqual(check_response.data["result"]["status"], "0")

        perform_payload = {
            "jsonrpc": "2.0",
            "id": 1002,
            "method": "transaction.perform",
            "params": {
                "transaction_id": "11111111-1111-1111-1111-111111111111",
                "account": {"order_id": order.id},
                "amount": 150000,
                "amount_tiyin": 15000000,
                "currency": 860,
            },
        }
        perform_response = self.client.post(self.callback_url, perform_payload, format="json", **headers)
        self.assertEqual(perform_response.status_code, status.HTTP_200_OK)
        self.assertEqual(perform_response.data["result"]["status"], "0")

        order.refresh_from_db()
        txn = Transaction.objects.get(order=order)
        self.assertEqual(order.status, OrderStatusEnum.SUCCESS)
        self.assertEqual(txn.status, TransactionStatusEnum.SUCCESS)
        self.assertTrue(Enrollment.objects.filter(user=self.user, course=self.course).exists())

        perform_response_2 = self.client.post(self.callback_url, perform_payload, format="json", **headers)
        self.assertEqual(perform_response_2.status_code, status.HTTP_200_OK)
        self.assertEqual(perform_response_2.data["result"]["status"], "0")
        self.assertEqual(Enrollment.objects.filter(user=self.user, course=self.course).count(), 1)

    def test_callback_check_invalid_amount_returns_status_5(self):
        order = Order.objects.create(
            user=self.user,
            course=self.course,
            amount=Decimal("150000.00"),
            currency=CurrencyEnum.UZS,
            status=OrderStatusEnum.CREATED,
        )
        self.client.force_authenticate(user=None)
        headers = {"HTTP_AUTHORIZATION": self._basic_auth_header("uic_callback", "uic_callback_pass")}
        payload = {
            "jsonrpc": "2.0",
            "id": 2001,
            "method": "transaction.check",
            "params": {
                "account": {"order_id": order.id},
                "amount": 150001,
                "amount_tiyin": 15000100,
                "currency": 860,
            },
        }
        response = self.client.post(self.callback_url, payload, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"]["status"], "5")

    def test_order_status_actions_failed_canceled_refunded(self):
        order = Order.objects.create(
            user=self.user,
            course=self.course,
            amount=Decimal("150000.00"),
            currency=CurrencyEnum.UZS,
            status=OrderStatusEnum.SUCCESS,
        )
        txn = Transaction.objects.create(
            order=order,
            amount=order.amount,
            currency=order.currency,
            vendor="other",
            status=TransactionStatusEnum.SUCCESS,
        )
        Enrollment.objects.create(user=self.user, course=self.course)

        failed_response = self.client.post(
            f"/api/v1/payments/orders/{order.id}/status/",
            {"action": "failed"},
            format="json",
        )
        self.assertEqual(failed_response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        txn.refresh_from_db()
        self.assertEqual(order.status, OrderStatusEnum.FAILED)
        self.assertEqual(txn.status, TransactionStatusEnum.FAILED)

        canceled_response = self.client.post(
            f"/api/v1/payments/orders/{order.id}/status/",
            {"action": "canceled"},
            format="json",
        )
        self.assertEqual(canceled_response.status_code, status.HTTP_200_OK)
        txn.refresh_from_db()
        self.assertEqual(txn.status, TransactionStatusEnum.CANCELED)

        refunded_response = self.client.post(
            f"/api/v1/payments/orders/{order.id}/status/",
            {"action": "refunded"},
            format="json",
        )
        self.assertEqual(refunded_response.status_code, status.HTTP_200_OK)
        self.assertFalse(Enrollment.objects.filter(user=self.user, course=self.course).exists())

    def test_order_status_action_is_user_scoped(self):
        order = Order.objects.create(
            user=self.other_user,
            course=self.course,
            amount=Decimal("150000.00"),
            currency=CurrencyEnum.UZS,
            status=OrderStatusEnum.CREATED,
        )
        response = self.client.post(
            f"/api/v1/payments/orders/{order.id}/status/",
            {"action": "failed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
