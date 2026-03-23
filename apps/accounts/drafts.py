# from django.conf import settings
# from django.db import models
# from django.utils.translation import gettext_lazy as _

# from apps.common.models import BaseModel


# class Profile(BaseModel):
#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.RESTRICT,
#         related_name="profile",
#         verbose_name=_("User"),
#     )
#     avatar = models.ForeignKey(
#         "common.Media",
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="user_avatars",
#         verbose_name=_("avatar"),
#     )
#     bio = models.TextField(_("bio"), blank=True)
#     phone = models.CharField(_("phone"), max_length=20, blank=True)

#     def __str__(self):
#         return f"{self.user.username} - {self.bio}"

#     class Meta:
#         verbose_name = _("profile")
#         verbose_name_plural = _("profiles")


# class User(AbstractUser):
#     avatar = models.ForeignKey(
#         "common.Media",
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="user_avatars",
#         verbose_name=_("avatar"),
#     )
#     bio = models.TextField(_("bio"), blank=True)
#     phone = models.CharField(_("phone"), max_length=20, blank=True)

#     def __str__(self):
#         return f"{self.username}"

#     class Meta:
#         verbose_name = _("user")
#         verbose_name_plural = _("users")
