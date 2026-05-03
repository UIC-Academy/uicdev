from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.courses.models import Course
from apps.payments.choices import (
    CurrencyEnum,
    OrderStatusEnum,
    PaymentVendorEnum,
    TransactionStatusEnum,
    TransactionTypeEnum,
)


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
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="unique_user_course_order"),
        ]

    def __str__(self):
        return f"{self.user}: {self.amount} {self.currency} ({self.status})"


class Transaction(BaseModel):
    wallet = models.ForeignKey(
        "accounts.Wallet",
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("wallet"),
        blank=True,
        null=True,
    )
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
    type = models.CharField(
        _("type"),
        max_length=20,
        choices=TransactionTypeEnum.choices,
        default=TransactionTypeEnum.TOP_UP,
    )
    vendor = models.CharField(_("vendor"), max_length=20, choices=PaymentVendorEnum.choices)
    status = models.CharField(_("status"), max_length=20, choices=TransactionStatusEnum.choices)
    currency = models.CharField(_("currency"), max_length=20, choices=CurrencyEnum.choices)
    remote_id = models.CharField(_("remote id"), max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _("transaction")
        verbose_name_plural = _("transactions")

    def __str__(self):
        return f"{self.id}: {self.amount} {self.currency} ({self.status})"
