from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User permission tiers."""
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"


# Request schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


# Response schemas
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None

