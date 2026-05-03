import base64
from decimal import Decimal

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Author, User, Wallet
from apps.courses.models import Category, Course
from apps.interactions.models import Enrollment
from apps.payments.choices import CurrencyEnum, OrderStatusEnum, TransactionStatusEnum, TransactionTypeEnum
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
    purchase_url = "/api/v1/payments/purchase/"
    callback_url = "/api/v1/payments/callback/"

    def setUp(self):
        self.user = User.objects.create_user(phone="+998907777771", password="password", is_active=True)
        self.other_user = User.objects.create_user(phone="+998907777772", password="password", is_active=True)
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal("0.00"))
        self.other_wallet = Wallet.objects.create(user=self.other_user, balance=Decimal("0.00"))
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

    def test_checkout_creates_wallet_top_up_transaction_without_order(self):
        response = self.client.post(
            self.checkout_url,
            {"wallet_id": self.wallet.id, "amount": "200000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("/checkout/create/", response.data["checkout_url"])
        self.assertNotIn("order_id", response.data)

        txn = Transaction.objects.get(id=response.data["transaction_id"])
        self.assertEqual(txn.wallet_id, self.wallet.id)
        self.assertIsNone(txn.order_id)
        self.assertEqual(txn.amount, Decimal("200000.00"))
        self.assertEqual(txn.type, TransactionTypeEnum.TOP_UP)
        self.assertEqual(txn.status, TransactionStatusEnum.PENDING)

    def test_checkout_rejects_foreign_wallet(self):
        response = self.client.post(
            self.checkout_url,
            {"wallet_id": self.other_wallet.id, "amount": "200000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("wallet not found", str(response.data).lower())

    def test_callback_requires_basic_auth(self):
        self.client.force_authenticate(user=None)
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "transaction.check",
            "params": {"account": {"transaction_id": 1}},
        }
        response = self.client.post(self.callback_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_callback_check_and_perform_success_credits_wallet_idempotently(self):
        txn = Transaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("200000.00"),
            currency=CurrencyEnum.UZS,
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
                "account": {"transaction_id": txn.id},
                "amount": 200000,
                "amount_tiyin": 20000000,
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
                "account": {"transaction_id": txn.id},
                "amount": 200000,
                "amount_tiyin": 20000000,
                "currency": 860,
            },
        }
        perform_response = self.client.post(self.callback_url, perform_payload, format="json", **headers)
        self.assertEqual(perform_response.status_code, status.HTTP_200_OK)
        self.assertEqual(perform_response.data["result"]["status"], "0")

        txn.refresh_from_db()
        self.wallet.refresh_from_db()
        self.assertEqual(txn.status, TransactionStatusEnum.SUCCESS)
        self.assertEqual(self.wallet.balance, Decimal("200000.00"))

        perform_response_2 = self.client.post(self.callback_url, perform_payload, format="json", **headers)
        self.assertEqual(perform_response_2.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("200000.00"))

    def test_callback_check_invalid_amount_returns_status_5(self):
        txn = Transaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("200000.00"),
            currency=CurrencyEnum.UZS,
            vendor="other",
            status=TransactionStatusEnum.PENDING,
        )
        self.client.force_authenticate(user=None)
        headers = {"HTTP_AUTHORIZATION": self._basic_auth_header("uic_callback", "uic_callback_pass")}
        payload = {
            "jsonrpc": "2.0",
            "id": 2001,
            "method": "transaction.check",
            "params": {
                "account": {"transaction_id": txn.id},
                "amount": 200001,
                "amount_tiyin": 20000100,
                "currency": 860,
            },
        }
        response = self.client.post(self.callback_url, payload, format="json", **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"]["status"], "5")

    def test_purchase_course_debits_wallet_creates_order_transaction_and_enrollment(self):
        self.wallet.balance = Decimal("200000.00")
        self.wallet.save(update_fields=["balance", "updated_at"])

        response = self.client.post(
            self.purchase_url,
            {"wallet_id": self.wallet.id, "course_id": self.course.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], OrderStatusEnum.SUCCESS)
        self.assertEqual(response.data["wallet_balance"], "50000.00")

        self.wallet.refresh_from_db()
        order = Order.objects.get(id=response.data["order_id"])
        txn = Transaction.objects.get(id=response.data["transaction_id"])
        self.assertEqual(self.wallet.balance, Decimal("50000.00"))
        self.assertEqual(order.user_id, self.user.id)
        self.assertEqual(order.course_id, self.course.id)
        self.assertEqual(order.amount, Decimal("150000.00"))
        self.assertEqual(order.status, OrderStatusEnum.SUCCESS)
        self.assertEqual(txn.wallet_id, self.wallet.id)
        self.assertEqual(txn.order_id, order.id)
        self.assertEqual(txn.type, TransactionTypeEnum.PURCHASE)
        self.assertEqual(txn.status, TransactionStatusEnum.SUCCESS)
        self.assertTrue(Enrollment.objects.filter(user=self.user, course=self.course).exists())

    def test_purchase_course_rejects_insufficient_balance(self):
        response = self.client.post(
            self.purchase_url,
            {"wallet_id": self.wallet.id, "course_id": self.course.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("insufficient wallet balance", str(response.data).lower())
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Enrollment.objects.exists())

    def test_purchase_course_blocks_duplicate_purchase(self):
        self.wallet.balance = Decimal("300000.00")
        self.wallet.save(update_fields=["balance", "updated_at"])

        first_response = self.client.post(
            self.purchase_url,
            {"wallet_id": self.wallet.id, "course_id": self.course.id},
            format="json",
        )
        second_response = self.client.post(
            self.purchase_url,
            {"wallet_id": self.wallet.id, "course_id": self.course.id},
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.filter(user=self.user, course=self.course).count(), 1)
        self.assertEqual(Enrollment.objects.filter(user=self.user, course=self.course).count(), 1)

    def test_transaction_status_actions_failed_canceled_refunded(self):
        txn = Transaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("100000.00"),
            currency=CurrencyEnum.UZS,
            vendor="other",
            status=TransactionStatusEnum.PENDING,
        )

        failed_response = self.client.post(
            f"/api/v1/payments/transactions/{txn.id}/status/",
            {"action": "failed"},
            format="json",
        )
        self.assertEqual(failed_response.status_code, status.HTTP_200_OK)
        txn.refresh_from_db()
        self.assertEqual(txn.status, TransactionStatusEnum.FAILED)

        txn.status = TransactionStatusEnum.PENDING
        txn.save(update_fields=["status", "updated_at"])
        canceled_response = self.client.post(
            f"/api/v1/payments/transactions/{txn.id}/status/",
            {"action": "canceled"},
            format="json",
        )
        self.assertEqual(canceled_response.status_code, status.HTTP_200_OK)
        txn.refresh_from_db()
        self.assertEqual(txn.status, TransactionStatusEnum.CANCELED)

        txn.status = TransactionStatusEnum.SUCCESS
        txn.save(update_fields=["status", "updated_at"])
        self.wallet.balance = Decimal("100000.00")
        self.wallet.save(update_fields=["balance", "updated_at"])
        refunded_response = self.client.post(
            f"/api/v1/payments/transactions/{txn.id}/status/",
            {"action": "refunded"},
            format="json",
        )
        self.assertEqual(refunded_response.status_code, status.HTTP_200_OK)
        txn.refresh_from_db()
        self.wallet.refresh_from_db()
        self.assertEqual(txn.status, TransactionStatusEnum.FAILED)
        self.assertEqual(self.wallet.balance, Decimal("0.00"))

    def test_transaction_status_action_is_user_scoped(self):
        txn = Transaction.objects.create(
            wallet=self.other_wallet,
            amount=Decimal("100000.00"),
            currency=CurrencyEnum.UZS,
            vendor="other",
            status=TransactionStatusEnum.PENDING,
        )
        response = self.client.post(
            f"/api/v1/payments/transactions/{txn.id}/status/",
            {"action": "failed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
