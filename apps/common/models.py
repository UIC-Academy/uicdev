from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True


class Media(BaseModel):
    file = models.FileField(_("File URL"), max_length=500, upload_to="media/")

    class Meta:
        verbose_name = _("media")
        verbose_name_plural = _("media")

    def __str__(self):

        return f"{self.file.url}"


class Country(BaseModel):
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        verbose_name = _("country")
        verbose_name_plural = _("countries")

    def __str__(self):
        return self.name


class Region(BaseModel):
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        verbose_name = _("region")
        verbose_name_plural = _("regions")

    def __str__(self):
        return self.name
