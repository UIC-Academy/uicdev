from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.courses.models import Course
from apps.payments.choices import CurrencyEnum, OrderStatusEnum, PaymentVendorEnum, TransactionStatusEnum


class Order(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=_("user"),
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=_("course"),
    )
    amount = models.DecimalField(_("amount"), max_digits=10, decimal_places=2)
    status = models.CharField(
        _("status"), max_length=20, choices=OrderStatusEnum.choices, default=OrderStatusEnum.CREATED
    )
    currency = models.CharField(_("currency"), max_length=20, choices=CurrencyEnum.choices)

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")

    def __str__(self):
        return f"{self.user}: {self.amount} {self.currency} by {self.vendor} ({self.status})"


class Transaction(BaseModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("order"),
        blank=True,
        null=True,
        # null=True qachonki Transaction walletni toldirish uchun bolsa
    )
    amount = models.DecimalField(_("amount"), max_digits=10, decimal_places=2)
    vendor = models.CharField(_("vendor"), max_length=20, choices=PaymentVendorEnum.choices)
    status = models.CharField(_("status"), max_length=20, choices=TransactionStatusEnum.choices)
    currency = models.CharField(_("currency"), max_length=20, choices=CurrencyEnum.choices)

    class Meta:
        verbose_name = _("transaction")
        verbose_name_plural = _("transactions")

    def __str__(self):
        return f"{self.amount}: {self.course} by {self.wallet}"
