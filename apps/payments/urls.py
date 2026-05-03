from django.urls import path

from apps.payments.views import (
    CheckoutCreateAPIView,
    CoursePurchaseAPIView,
    PaymentCallbackAPIView,
    PaymentTransactionStatusAPIView,
)

urlpatterns = [
    path("checkout/", CheckoutCreateAPIView.as_view(), name="payment-checkout"),
    path("purchase/", CoursePurchaseAPIView.as_view(), name="payment-purchase"),
    path("callback/", PaymentCallbackAPIView.as_view(), name="payment-callback"),
    path(
        "transactions/<int:transaction_id>/status/",
        PaymentTransactionStatusAPIView.as_view(),
        name="payment-transaction-status",
    ),
]
