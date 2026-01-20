import datetime
from sqlmodel import SQLModel, Field
from typing import Optional
from pydantic import BaseModel


class WishlistBase(SQLModel):
    """Base wishlist model"""
    user_id: int = Field(foreign_key="users.id", index=True)
    game_id: str = Field(index=True)
    game_title: str
    game_image_url: Optional[str] = None
    game_price: Optional[float] = None
    game_original_price: Optional[float] = None
    game_discount: Optional[int] = None
    store_id: Optional[str] = None
    deal_id: Optional[str] = None
    added_date: datetime.datetime = Field(default_factory=datetime.datetime.now)


class Wishlist(WishlistBase, table=True):
    """Wishlist table model"""
    __tablename__ = "wishlist"
    id: int | None = Field(default=None, primary_key=True)


class WishlistResponse(BaseModel):
    """Wishlist response model for API"""
    id: int
    user_id: int
    game_id: str
    game_title: str
    game_image_url: Optional[str] = None
    game_price: Optional[float] = None
    game_original_price: Optional[float] = None
    game_discount: Optional[int] = None
    store_id: Optional[str] = None
    deal_id: Optional[str] = None
    added_date: datetime.datetime


class WishlistCreate(BaseModel):
    """Model for adding game to wishlist"""
    game_id: str
    game_title: str
    game_image_url: Optional[str] = None
    game_price: Optional[float] = None
    game_original_price: Optional[float] = None
    game_discount: Optional[int] = None
    store_id: Optional[str] = None
    deal_id: Optional[str] = None
