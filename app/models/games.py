<<<<<<< HEAD
from sqlmodel import SQLModel, Field
from typing import Optional


class GameBase(SQLModel):
    id: str = Field(primary_key=True)
=======
from pydantic import BaseModel
from typing import Optional

class Game(BaseModel):
    id: str
>>>>>>> main
    title: str
    genre: Optional[str] = None
    image_url: Optional[str] = None


<<<<<<< HEAD
class Game(GameBase, table=True):
    __tablename__ = "games"

=======
class GamePrice(BaseModel):
    game_id: str
    store: str
    price: float
    currency: str = "USD"
    url: Optional[str] = None


class GameWithPrices(BaseModel):
    game: Game
    prices: list[GamePrice]
>>>>>>> main
