from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Wallet
from apps.common.models import BaseModel
from apps.courses.models import Course
from apps.payments.choices import CurrencyEnum, PaymentVendorEnum, TransactionStatusEnum


class Transaction(BaseModel):
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("wallet"),
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("course"),
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
