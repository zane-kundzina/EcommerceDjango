import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
NOTIFY_ADMIN_EMAIL = os.getenv("NOTIFY_ADMIN_EMAIL")

def send_registration_email(username: str, user_email: str):
    subject = "New User Registered"
    body = f"A new user has registered:\n\nUsername: {username}\nEmail: {user_email}"

    msg = MIMEMultipart()
    msg["From"] = EMAIL_HOST_USER
    msg["To"] = NOTIFY_ADMIN_EMAIL
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.send_message(msg)

    return True
