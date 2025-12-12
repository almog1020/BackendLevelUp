from sqlmodel import Session, select

from app.db import engine
from app.models.users import User, UserBase
from typing import Optional, Dict, List
from app.schemas import UserRole

# In-memory database (replace with Postgres later)
# Users: {username: {id, username, email, hashed_password, role}}
fake_users_db: Dict[str, dict] = {}
user_id_counter = 1

# Games: {game_id: {id, title, genre, image_url}}
games_db: Dict[str, dict] = {}

# Prices: [{game_id, store, price, currency, url}]
prices_db: List[dict] = []


def select_user(user: UserBase) -> User | None:
    """Pull out the user from the database"""
    with Session(engine) as session:
        statement = select(User).where(User.email == user.email).where(User.password == user.password)
        results = session.exec(statement)
        return results.first()

def get_user_by_username(username: str) -> Optional[dict]:
    """Get a user by username."""
    return fake_users_db.get(username)


def get_user_by_email(email: str) -> Optional[dict]:
    """Get a user by email."""
    for user in fake_users_db.values():
        if user["email"] == email:
            return user
    return None


def create_user(username: str, email: str, hashed_password: str) -> dict:
    """Create a new user."""
    global user_id_counter

    user = {
        "id": user_id_counter,
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "role": UserRole.USER,  # Default role
    }
    fake_users_db[username] = user
    user_id_counter += 1
    return user