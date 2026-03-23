from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class Notification(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name=_("user"),
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name=_("course"),
    )
    module = models.ForeignKey(
        "courses.Module",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name=_("module"),
    )
    category = models.ForeignKey(
        "courses.Category",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name=_("category"),
    )
    title = models.CharField(_("title"), max_length=255)
    message = models.TextField(_("message"))
    is_send_to_all = models.BooleanField(_("is send to all"), default=False)
    image = models.ForeignKey(
        "common.Media",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_images",
        verbose_name=_("image"),
    )

    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")

    def __str__(self):
        return self.title
