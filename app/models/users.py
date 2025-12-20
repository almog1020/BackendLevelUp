import datetime

from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from typing import Optional

from app.schemas import UserRole, UserStatus


class UserBase(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr
    password: Optional[str] = Field(default=None, min_length=3, max_length=64)
    name: Optional[str] = Field(default=None, max_length=255)
    google_id: Optional[str] = Field(default=None, max_length=255)
    role:UserRole
    status:UserStatus
    purchase:int
    joined: datetime.datetime = Field(default_factory=datetime.datetime.now)

class User(UserBase, table=True):
    __tablename__ = "users"


class UserRegister(SQLModel):
    email: EmailStr
    password: str = Field(min_length=3, max_length=64)
    name: str = Field(min_length=1, max_length=255)


class UserResponse(SQLModel):
    """User response model without password"""
    id: int
    email: EmailStr
    name: Optional[str] = None
    google_id: Optional[str] = None
    role: UserRole








