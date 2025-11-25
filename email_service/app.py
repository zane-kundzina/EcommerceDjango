from fastapi import FastAPI
from models.user_event import UserRegisteredEvent
from services.email_sender import send_registration_email

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "Email service is running"}

@app.post("/send-user-registered/")
def notify_new_user(event: UserRegisteredEvent):
    send_registration_email(event.username, event.email)
    return {"message": "Notification email sent successfully"}
