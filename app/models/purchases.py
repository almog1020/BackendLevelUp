import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from pydantic import BaseModel


class PurchaseBase(SQLModel):
    """Base purchase model for database table"""
    user_id: int = Field(foreign_key="users.id", index=True)
    game_id: str = Field(index=True)
    game_title: str
    game_image_url: Optional[str] = None
    game_genre: Optional[str] = None  # Store as comma-separated string or JSON
    purchase_date: datetime.datetime = Field(default_factory=datetime.datetime.now, index=True)
    price: Optional[float] = None
    store: Optional[str] = None


class Purchase(PurchaseBase, table=True):
    """Purchase table model"""
    __tablename__ = "purchases"
    id: int | None = Field(default=None, primary_key=True)


class PurchaseResponse(BaseModel):
    """Purchase response model for API"""
    id: int
    user_id: int
    game_id: str
    game_title: str
    game_image_url: Optional[str] = None
    game_genre: Optional[str] = None
    purchase_date: datetime.datetime
    price: Optional[float] = None
    store: Optional[str] = None


class PurchaseCreate(BaseModel):
    """Model for creating a new purchase"""
    game_id: str
    game_title: str
    game_image_url: Optional[str] = None
    game_genre: Optional[str] = None
    price: Optional[float] = None
    store: Optional[str] = None
