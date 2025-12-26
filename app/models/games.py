from pydantic import BaseModel
from typing import Optional

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
