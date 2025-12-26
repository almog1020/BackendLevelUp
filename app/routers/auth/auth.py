import os
from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import ActiveEngine, ActiveUser
from app.logic.auth import (
    verify_password,
    create_access_token,
)
from dotenv import load_dotenv
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests

from sqlmodel import Session, select

from app.logic.users import create_user_from_google, get_user_by_email, get_user_by_google_id, get_current_user, select_user
from app.models.token import Token
from app.models.users import UserResponse, User

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

load_dotenv()

class TokenRequest(BaseModel):
    token: str

@router.post("/google", response_model=UserResponse)
async def google_auth(engine: ActiveEngine, data: TokenRequest):
    """Login or signup with Google authentication"""
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
    user = get_user_by_email(engine, email) or get_user_by_google_id(engine, google_id)

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
        role=user.role,
    )


@router.post("/token", response_model=Token)
async def login(engine: ActiveEngine,form_data:ActiveUser):

    """Login and get access token."""
    db_user = select_user(engine,form_data)

    if not db_user or not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": db_user.name},
        expires_delta=timedelta(minutes=float(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"]))
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[dict, Depends(get_current_user)]):
    """Get current authenticated user."""
    return UserResponse(
        id=current_user["id"],
        name=current_user["username"],
        email=current_user["email"],
        role=current_user["role"]
    )

