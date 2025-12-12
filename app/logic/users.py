from fastapi import HTTPException,status
from sqlmodel import Session, select
from app.db import engine
from app.logic.auth import verify_password, hash_password
from app.models.users import User, UserBase, UserRegister
from typing import Dict, List


# Games: {game_id: {id, title, genre, image_url}}
games_db: Dict[str, dict] = {}

# Prices: [{game_id, store, price, currency, url}]
prices_db: List[dict] = []


def select_user(user: UserBase) -> User | None:
    """Pull out the user from the database and verify password"""
    with Session(engine) as session:
        statement = select(User).where(User.email == user.email)
        db_user = session.exec(statement).first()

        if db_user and user.password:
            if db_user.password and verify_password(user.password, db_user.password):
                return db_user
        elif db_user and not user.password:
            # For OAuth users without password
            return db_user

        return None


def get_user_by_email(email: str) -> User | None:
    """Get user by email"""
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()


def get_user_by_google_id(google_id: str) -> User | None:
    """Get user by Google ID"""
    with Session(engine) as session:
        statement = select(User).where(User.google_id == google_id)
        return session.exec(statement).first()


def create_user(user_data: UserRegister) -> User:
    """Create a new user with hashed password"""
    with Session(engine) as session:
        # Check if email already exists
        existing_user = get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create new user
        new_user = User(
            email=user_data.email,
            password=hashed_password,
            name=user_data.name
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return new_user


def create_user_from_google(email: str, name: str | None, google_id: str, picture: str | None = None) -> User:
    """Create a new user from Google OAuth data"""
    with Session(engine) as session:
        # Check if user already exists by email or google_id
        existing_user = get_user_by_email(email)
        if existing_user:
            # Update google_id if not set
            if not existing_user.google_id:
                existing_user.google_id = google_id
                session.add(existing_user)
                session.commit()
                session.refresh(existing_user)
            return existing_user

        existing_google_user = get_user_by_google_id(google_id)
        if existing_google_user:
            return existing_google_user

        # Create new user
        new_user = User(
            email=email,
            name=name,
            google_id=google_id,
            password=None  # No password for OAuth users
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return new_user



