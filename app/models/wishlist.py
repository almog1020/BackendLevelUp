from datetime import datetime

from sqlalchemy import Column, DateTime, Index, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class WishlistCreate(SQLModel):
    game_id: str | None = Field(default=None)
    title: str | None = Field(default=None)
    thumb: str | None = Field(default=None)


class WishlistRead(SQLModel):
    id: int
    external_game_id: str
    title: str | None = None
    thumb: str | None = None
    created_at: datetime


class WishlistItem(SQLModel, table=True):
    __tablename__ = "wishlist"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "external_game_id",
            name="uq_wishlist_user_game",
        ),
        Index("ix_wishlist_user_id", "user_id"),
        Index("ix_wishlist_external_game_id", "external_game_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    external_game_id: str = Field(nullable=False, max_length=255)
    title: str | None = Field(default=None, max_length=255)
    thumb: str | None = Field(default=None, max_length=1024)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
