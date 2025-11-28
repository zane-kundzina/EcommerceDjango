from fastapi import FastAPI
from pydantic import BaseModel
from email_sender import send_review_notification

app = FastAPI()

class ReviewPayload(BaseModel):
    product_name: str
    username: str
    rating: int
    comment: str

@app.get("/")
def health_check():
    return {"status": "Review notification service is running"}

@app.post("/notify/review/")
async def notify_review(payload: ReviewPayload):
    try:
        await send_review_notification(
            product_name=payload.product_name,
            username=payload.username,
            rating=payload.rating,
            comment=payload.comment
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
