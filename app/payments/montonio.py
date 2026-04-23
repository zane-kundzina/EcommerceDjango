import jwt
import time
import requests
from django.conf import settings
import uuid

def create_montonio_payment(payment):

    url = f"{settings.MONTONIO_BASE_URL}/orders"

    payload = {
        "accessKey": settings.MONTONIO_ACCESS_KEY,
        "merchantReference": f"{payment.id}-{uuid.uuid4().hex[:8]}",
        "returnUrl": settings.MONTONIO_RETURN_URL,
        "notificationUrl": settings.MONTONIO_NOTIFICATION_URL,
        "currency": "EUR",
        "grandTotal": float(payment.amount),
        "locale": "lv",
        "payment": {
            "amount": float(payment.amount),
            "currency": "EUR",
            "method": "paymentInitiation"
        },
        "exp": int(time.time()) + 600
    }   

    token = jwt.encode(
        payload,
        settings.MONTONIO_SECRET_KEY,
        algorithm="HS256"
    )

    #  FIX: ja token ir bytes → pārvērš string
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