from typing import Optional, Dict, List
from schemas import UserRole

# In-memory database (replace with Postgres later)
# Users: {username: {id, username, email, hashed_password, role}}
fake_users_db: Dict[str, dict] = {}
user_id_counter = 1

# Games: {game_id: {id, title, genre, image_url}}
games_db: Dict[str, dict] = {}

# Prices: [{game_id, store, price, currency, url}]
prices_db: List[dict] = []


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

