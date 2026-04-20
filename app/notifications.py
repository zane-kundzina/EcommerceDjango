import smtplib
from email.message import EmailMessage
from django.conf import settings


def send_email(subject: str, content: str):
    print("SENDING EMAIL:", subject)

    message = EmailMessage()
    message["From"] = settings.EMAIL_HOST_USER
    message["To"] = settings.ADMIN_EMAIL
    message["Subject"] = subject
    message.set_content(content)

    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
        server.starttls()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.send_message(message)


def handle_event(event_type: str, data: dict):

    if event_type == "review":
        send_email(
            subject=f"New Review for {data['product_name']}",
            content=f"""
Product: {data['product_name']}
User: {data['username']}
Rating: {data['rating']}
Comment: {data['comment']}
"""
        )

    elif event_type == "payment":
        send_email(
            subject=f"Payment received for order {data['order_id']}",
            content=f"""
Order ID: {data['order_id']}
User: {data['username']}
Amount: {data['amount']} EUR
"""
        )

    elif event_type == "stock":
        if data["quantity"] < 5:
            send_email(
                subject=f"Low stock alert: {data['product_name']}",
                content=f"""
Product: {data['product_name']}
Remaining: {data['quantity']}
"""
        )

    elif event_type == "user_registered":
        send_email(
            subject=f"New user registered: {data['username']}",
            content=f"""
New user has registered and activated account:

Username: {data['username']}
Email: {data['email']}
"""
    )

    else:
        raise ValueError(f"Unknown event type: {event_type}")