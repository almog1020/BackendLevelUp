import os
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.logic.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from database import get_user_by_username, get_user_by_email, create_user
from app.schemas import UserCreate, UserResponse, Token
from dotenv import load_dotenv
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests

from sqlmodel import Session, select

from app.logic.users import create_user_from_google, get_user_by_email, get_user_by_google_id
from app.models.users import UserResponse, User
from app.db import engine

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

load_dotenv()

class TokenRequest(BaseModel):
    token: str

@router.post("/google", response_model=UserResponse)
async def google_auth(data: TokenRequest):
    """Login or signup with Google authentication"""
    try:
        id_info = id_token.verify_oauth2_token(
            data.token,
            requests.Request(),
            os.environ["GOOGLE_CLIENT_ID"],
        )
        
        email = id_info["email"]
        name = id_info.get("name")
        google_id = id_info["sub"]
        picture = id_info.get("picture")
        
        # Check if user exists by email or google_id
        user = get_user_by_email(email) or get_user_by_google_id(google_id)
        
        if user:
            # Existing user - login flow
            # Update google_id if not set
            if not user.google_id:
                with Session(engine) as session:
                    # Get fresh user instance in this session
                    statement = select(User).where(User.id == user.id)
                    db_user = session.exec(statement).first()
                    if db_user:
                        db_user.google_id = google_id
                        session.add(db_user)
                        session.commit()
                        session.refresh(db_user)
                        user = db_user
        else:
            # New user - signup flow
            user = create_user_from_google(email, name, google_id, picture)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            google_id=user.google_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Google token")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    # Check if username exists
    if get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email exists
    if get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user with hashed password
    hashed_password = hash_password(user_data.password)
    user = create_user(user_data.username, user_data.email, hashed_password)

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["role"]
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token."""
    user = get_user_by_username(form_data.username)

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user."""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"]
    )

