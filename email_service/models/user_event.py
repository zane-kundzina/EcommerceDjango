from pydantic import BaseModel, EmailStr

class UserRegisteredEvent(BaseModel):
    username: str
    email: EmailStr
