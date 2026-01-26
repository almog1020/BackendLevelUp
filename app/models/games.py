from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from typing import Optional


class GameBase(SQLModel):
    id: str = Field(primary_key=True)
    title: str
    genre: Optional[str] = None
    image_url: Optional[str] = None


class Game(GameBase, table=True):
    __tablename__ = "games"


class GamePrice(BaseModel):
    game_id: str
    store: str
    price: float
    currency: str = "USD"
    url: Optional[str] = None


class GameWithPrices(BaseModel):
    game: Game
    prices: list[GamePrice]


class PriceComparison(BaseModel):
    store: str
    price: float
    url: Optional[str] = None


class GameResponse(BaseModel):
    id: str
    title: str
    description: str
    image: str
    originalPrice: float
    currentPrice: float
    discount: float
    genres: list[str]
    isTrending: bool
    isDealOfDay: bool
    priceComparison: Optional[list[PriceComparison]] = None
