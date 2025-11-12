from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from django.conf import settings

class PayPalClient:
    def __init__(self):
        if settings.PAYPAL_MODE == 'live':
            environment = LiveEnvironment(
                client_id=settings.PAYPAL_CLIENT_ID,
                client_secret=settings.PAYPAL_CLIENT_SECRET
            )
        else:
            environment = SandboxEnvironment(
                client_id=settings.PAYPAL_CLIENT_ID,
                client_secret=settings.PAYPAL_CLIENT_SECRET
            )
        self.client = PayPalHttpClient(environment)
