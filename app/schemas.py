from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum, auto, StrEnum


class UserRole(StrEnum):
    """User permission tiers."""
    USER = auto()
    ADMIN = auto()

class UserStatus(StrEnum):
    """User status tiers."""
    ACTIVE = auto()
    SUSPENDED = auto()

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


# Game schemas
class Game(BaseModel):
    id: str
    title: str
    genre: Optional[str] = None
    image_url: Optional[str] = None


class GamePrice(BaseModel):
    game_id: str
    store: str
    price: float
    currency: str = "USD"
    url: Optional[str] = None


class GameWithPrices(BaseModel):
    game: Game
    prices: list[GamePrice]

