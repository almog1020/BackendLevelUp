from sqlmodel import SQLModel, Field
from typing import Optional


class GameBase(SQLModel):
    id: str = Field(primary_key=True)
    title: str
    genre: Optional[str] = None
    image_url: Optional[str] = None


class Game(GameBase, table=True):
    __tablename__ = "games"

