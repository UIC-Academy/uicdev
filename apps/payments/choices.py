from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class TransactionStatusEnum(TextChoices):
    PENDING = "pending", _("pending")
    SUCCESS = "success", _("success")
    FAILED = "failed", _("failed")
    CANCELED = "canceled", _("canceled")


class PaymentVendorEnum(TextChoices):
    CLICK = "click", _("click")
    PAYME = "payme", _("payme")
    UZUM = "uzum", _("uzum")
    OTHER = "other", _("other")


class CurrencyEnum(TextChoices):
    UZS = "uzs", _("uzs")
    USD = "usd", _("usd")
    EUR = "eur", _("eur")
    RUB = "rub", _("rub")
