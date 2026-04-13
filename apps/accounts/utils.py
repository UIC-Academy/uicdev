import requests
from django.conf import settings

BASE_URL = "https://devsms.uz/api"

headers = {"Authorization": f"Bearer {settings.DEVSMS_TOKEN}", "Content-Type": "application/json"}


# SMS Yuborish
def send_sms(phone: str, message: str) -> dict:
    response = requests.post(f"{BASE_URL}/send_sms.php", headers=headers, json={"phone": phone, "message": message})
    return response.json()


# Balansni olish
def get_balance() -> dict:
    response = requests.get(f"{BASE_URL}/get_balance.php", headers=headers)
    return response.json()


# Ishlatish
# result = send_sms("998901234567", "Assalomu alaykum, tizimimizga xush kelibsiz!")
# print(result)


def generate_code():
    import random

    d1 = random.randint(0, 9)
    d2 = random.randint(0, 9)
    d3 = random.randint(0, 9)
    d4 = random.randint(0, 9)

    return f"{d1}{d2}{d3}{d4}"
