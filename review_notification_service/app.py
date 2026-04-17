from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
from email_sender import handle_event

app = FastAPI()

class NotificationPayload(BaseModel):
    event_type: str
    data: Dict[str, Any]

@app.get("/")
def health_check():
    return {"status": "Notification service is running"}

@app.post("/notify/")
async def notify(payload: NotificationPayload):
    try:
        await handle_event(payload.event_type, payload.data)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}