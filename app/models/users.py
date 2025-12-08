from sqlmodel import SQLModel, Field
from pydantic import EmailStr


class UserBase(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr
    password: str = Field(min_length=3, max_length=64)


class User(UserBase, table=True):
    __tablename__ = "users"








