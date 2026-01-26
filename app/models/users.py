import datetime
from enum import  auto, StrEnum

from sqlmodel import SQLModel, Field
from pydantic import EmailStr, BaseModel
from typing import Optional


class UserRole(StrEnum):
    """User permission tiers."""
    USER = auto()
    ADMIN = auto()


class UserStatus(StrEnum):
    """User status tiers."""
    ACTIVE = auto()
    SUSPENDED = auto()
    INACTIVE = auto()


class UserBase(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr
    password:str | None = Field(default=None,min_length=3, max_length=1000)
    name:str = Field(max_length=255)
    google_id: Optional[str] = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.USER)
    status: UserStatus = Field(default=UserStatus.INACTIVE)
    purchase:int = Field(default=0)
    joined: datetime.datetime = Field(default_factory=datetime.datetime.now)
    last_active: Optional[datetime.datetime] = Field(default=None)
    favorite_genre: Optional[str] = Field(default=None, max_length=100)
    preferred_store: Optional[str] = Field(default=None, max_length=100)

class User(UserBase, table=True):
    __tablename__ = "users"


class UserRegister(SQLModel):
    email: EmailStr
    password: str | None = Field(default=None,min_length=3, max_length=1000)
    name: str = Field(min_length=1, max_length=255)


class UserResponse(BaseModel):
    """User response model without password"""
    id: int
    email: EmailStr
    name: str
    google_id: Optional[str] = None
    role: UserRole
    status: UserStatus
    joined: datetime.datetime
    lastActive: Optional[datetime.datetime] = None
    purchase: int
    avatar: Optional[str] = None


class ProfileUpdate(BaseModel):
    """Model for updating user profile"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=3, max_length=1000)
    avatar: Optional[str] = Field(default=None, max_length=500)


class PreferencesUpdate(BaseModel):
    """Model for updating user preferences"""
    favoriteGenre: Optional[str] = Field(default=None, max_length=100)
    preferredStore: Optional[str] = Field(default=None, max_length=100)


class ProfileData(BaseModel):
    """Complete profile data model"""
    id: int
    name: str
    email: EmailStr
    role: UserRole
    avatar: Optional[str] = None
    memberSince: datetime.datetime
    lastLogin: Optional[datetime.datetime] = None


class StatisticsData(BaseModel):
    """User statistics model"""
    wishlistItems: int = 0
    totalSaved: float = 0.0
    gamesTracked: int = 0
    priceAlerts: int = 0
    reviewsWritten: int = 0


class PreferencesData(BaseModel):
    """User preferences model"""
    favoriteGenre: Optional[str] = None
    preferredStore: Optional[str] = None


class ActivityData(BaseModel):
    """Activity model"""
    id: int
    type: str
    description: str
    gameName: str
    timestamp: datetime.datetime


class ProfileResponse(BaseModel):
    """Complete profile response model"""
    profile: ProfileData
    statistics: StatisticsData
    preferences: PreferencesData
    activities: list[ActivityData]









