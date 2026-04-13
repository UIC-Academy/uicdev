from celery import shared_task

from apps.accounts.utils import send_sms


@shared_task
def send_sms_to_phone_task(phone: str, message: str):
    return send_sms(phone, message)
