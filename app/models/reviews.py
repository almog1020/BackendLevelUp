from sqlmodel import Field, SQLModel


class ReviewBase(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    comment: str = Field(min_length=1, max_length=200)
    star : int
    game : str
    user_id: int | None = Field(default=None, foreign_key="users.id")

class Review(ReviewBase, table=True):
    __tablename__ = "reviews"