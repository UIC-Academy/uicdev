from django.urls import path

from apps.payments.views import CheckoutCreateAPIView, PaymentCallbackAPIView, PaymentOrderStatusAPIView

urlpatterns = [
    path("checkout/", CheckoutCreateAPIView.as_view(), name="payment-checkout"),
    path("callback/", PaymentCallbackAPIView.as_view(), name="payment-callback"),
    path("orders/<int:order_id>/status/", PaymentOrderStatusAPIView.as_view(), name="payment-order-status"),
]
