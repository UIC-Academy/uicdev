import logging

from django.db.models.signals import (
    post_delete,
    post_init,
    post_save,
    pre_delete,
    pre_init,
    pre_save,
)
from django.dispatch import receiver

from apps.accounts.models import User
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 1. pre_init — User(**kwargs) boshlanishidan OLDIN
#    instance hali yaratilmagan, faqat kwargs bor
# ──────────────────────────────────────────────
@receiver(pre_init, sender=User)
def user_pre_init(sender, args, kwargs, **extra):
    logger.info(f"[pre_init] User() chaqirilmoqda kwargs={kwargs}")


# ──────────────────────────────────────────────
# 2. post_init — User(**kwargs) tugagandan KEYIN
#    instance xotirada bor, lekin DB da hali yo'q
# ──────────────────────────────────────────────
@receiver(post_init, sender=User)
def user_post_init(sender, instance, **kwargs):
    logger.info(f"[post_init] User instance yaratildi: {instance.phone}")


# ──────────────────────────────────────────────
# 3. pre_save — .save() chaqirildi, DB ga yozishdan OLDIN
#    Bu yerda ma'lumotni o'zgartirish mumkin
# ──────────────────────────────────────────────
@receiver(pre_save, sender=User)
def user_pre_save(sender, instance, raw, using, update_fields, **kwargs):
    if not instance.pk:
        logger.info(f"[pre_save] Yangi user yaratilmoqda: {instance.phone}")
    else:
        # Eski qiymatni DB dan o'qib solishtiramiz
        try:
            old = User.objects.get(pk=instance.pk)
            if old.phone != instance.phone:
                logger.info(f"[pre_save] Phone o'zgardi: {old.phone} -> {instance.phone}")
        except User.DoesNotExist:
            pass


# ──────────────────────────────────────────────
# 4. post_save — .save() tugadi, DB ga yozildi
#    created=True bo'lsa yangi, False bo'lsa update
# ──────────────────────────────────────────────
@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        logger.info(f"[post_save] Yangi user yaratildi: {instance.phone}")
        Notification.objects.create(
            user=instance,
            title="Welcome",
            message="Welcome to our platform",
        )
    else:
        logger.info(f"[post_save] User yangilandi: {instance.phone}")


# ──────────────────────────────────────────────
# 5. pre_delete — .delete() chaqirildi, DB dan o'chirishdan OLDIN
#    instance hali DB da bor
# ──────────────────────────────────────────────
@receiver(pre_delete, sender=User)
def user_pre_delete(sender, instance, using, origin, **kwargs):
    logger.info(f"[pre_delete] User o'chirilmoqda: {instance.phone}")


# ──────────────────────────────────────────────
# 6. post_delete — DB dan o'chirildi
#    instance.pk hali xotirada bor, lekin DB da yo'q
# ──────────────────────────────────────────────
@receiver(post_delete, sender=User)
def user_post_delete(sender, instance, using, origin, **kwargs):
    logger.info(f"[post_delete] User o'chirildi: {instance.phone} (pk={instance.pk})")


# ──────────────────────────────────────────────
# LIFECYCLE TARTIBI:
#
# user = User(phone="+998901234567")   ->  pre_init -> post_init
# user.save()  (yangi)                 ->  pre_save -> post_save (created=True)
# user.phone = "+998907654321"
# user.save()  (update)                ->  pre_save -> post_save (created=False)
# user.delete()                        ->  pre_delete -> post_delete
#
# pre_migrate & post_migrate — migrate buyrug'i boshlanishi va tugashi
# Ular AppConfig.ready() ichida emas, balki alohida ishlatiladi
# ──────────────────────────────────────────────
