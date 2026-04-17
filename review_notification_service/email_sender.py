import aiosmtplib
from email.message import EmailMessage
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, TO_EMAIL


async def send_email(subject: str, content: str):
    message = EmailMessage()
    message["From"] = SMTP_USER
    message["To"] = TO_EMAIL
    message["Subject"] = subject
    message.set_content(content)

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=True,
        username=SMTP_USER,
        password=SMTP_PASSWORD
    )


async def handle_event(event_type: str, data: dict):
    
    if event_type == "review":
        await send_email(
            subject=f"New Review for {data['product_name']}",
            content=f"""
Product: {data['product_name']}
User: {data['username']}
Rating: {data['rating']}
Comment: {data['comment']}
"""
        )

    elif event_type == "payment":
        await send_email(
            subject=f"Payment received for order {data['order_id']}",
            content=f"""
Order ID: {data['order_id']}
User: {data['username']}
Amount: {data['amount']} EUR
"""
        )

    elif event_type == "stock":
        if data["quantity"] < 5:
            await send_email(
                subject=f"Low stock alert: {data['product_name']}",
                content=f"""
Product: {data['product_name']}
Remaining: {data['quantity']}
"""
            )

    else:
        raise ValueError(f"Unknown event type: {event_type}")