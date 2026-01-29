from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from app.models.users import User


class ReviewBase(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    comment: str = Field(min_length=1, max_length=200)
    star : int
    game : str
    user_id: int | None = Field(default=None, foreign_key="users.id")

class Review(ReviewBase, table=True):
    __tablename__ = "reviews"


class GameReview(BaseModel):
    user: User | None
    review: Review