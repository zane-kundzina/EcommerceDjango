import jwt
import time
import requests
from django.conf import settings

def create_montonio_payment(order):

    url = f"{settings.MONTONIO_BASE_URL}/orders"

    payload = {
        "accessKey": settings.MONTONIO_ACCESS_KEY,
        "merchantReference": str(order.id),
        "returnUrl": settings.MONTONIO_RETURN_URL,
        "notificationUrl": settings.MONTONIO_NOTIFICATION_URL,
        "currency": "EUR",
        "grandTotal": float(order.total_amount),
        "locale": "lv",
        "payment": {
            "amount": float(order.total_amount),
            "currency": "EUR",
            "method": "paymentInitiation"
        },
        "exp": int(time.time()) + 600
    }

    print("ACCESS:", settings.MONTONIO_ACCESS_KEY)
    print("SECRET:", settings.MONTONIO_SECRET_KEY)

    token = jwt.encode(
        payload,
        settings.MONTONIO_SECRET_KEY,
        algorithm="HS256"
    )

    # ⚠️ FIX: ja token ir bytes → pārvērš string
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    response = requests.post(
        url,
        json={"data": token},
        headers={"Content-Type": "application/json"},
        timeout=10
    )

    # DEBUG: izdrukā statusu un atbildi, lai redzētu, kas notiek ar Montonio API
    print("MONTONIO STATUS:", response.status_code)
    print("MONTONIO RESPONSE:", response.text)

    return response.json()