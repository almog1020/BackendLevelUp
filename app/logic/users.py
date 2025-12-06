from sqlmodel import Session, select

from app.db import engine
from app.models.users import User, UserBase


def select_user(user: UserBase) -> User | None:
    with Session(engine) as session:
        statement = select(User).where(User.email == user.email).where(User.password == user.password)
        results = session.exec(statement)
        return results.first()
