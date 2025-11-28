import aiosmtplib
from email.message import EmailMessage
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, TO_EMAIL

async def send_review_notification(product_name, username, rating, comment):
    message = EmailMessage()
    message["From"] = SMTP_USER
    message["To"] = TO_EMAIL  # admin receives notifications
    message["Subject"] = f"New Review Added for {product_name}"

    message.set_content(f"""
A new review has been added.

Product: {product_name}
User: {username}
Rating: {rating} / 5
Comment: {comment}
    """)

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=True,
        username=SMTP_USER,
        password=SMTP_PASSWORD
    )
