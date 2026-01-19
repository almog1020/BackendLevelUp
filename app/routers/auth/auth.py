import os
from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from app.dependencies import ActiveEngine
from app.logic.auth import (
    verify_password,
    create_access_token,
)
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests

from sqlmodel import Session, select

from app.logic.users import create_user_from_google, get_user_by_email, get_user_by_google_id, select_user,update_user_status
from app.models.token import Token, TokenRequest
from app.models.users import UserResponse, User, UserStatus

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={
        404: {"description": "Not found"}},
)

load_dotenv()

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
                    db_user.status = UserStatus.ACTIVE
                    session.add(db_user)
                    session.commit()
                    session.refresh(db_user)
                    user = db_user
    else:
        # New user - signup flow
        user = create_user_from_google(engine,email, name, google_id)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        google_id=user.google_id,
        status=UserStatus.ACTIVE,
    )


@router.post("/token", response_model=Token)
async def login(engine: ActiveEngine,form_data:Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Login and get access token."""
    user = select_user(engine,form_data)

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already suspended")

    update_user_status(engine=engine,email=user.email,disable=UserStatus.ACTIVE)

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=float(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"]))
    )

    return Token(access_token=access_token, token_type="bearer")


