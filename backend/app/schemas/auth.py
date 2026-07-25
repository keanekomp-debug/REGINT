"""Authentication schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    
    class Config:
        from_attributes = True
