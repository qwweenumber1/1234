from pydantic import BaseModel
from typing import Optional, Any

class User(BaseModel):
    email: str
    role: str
    is_verified: bool

class RegisterResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: Optional[str] = None
    verification_token: Optional[str] = None
    email: str

class LoginResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    user: User

class AiChatResponse(BaseModel):
    response: str
