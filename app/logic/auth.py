import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from google.auth.transport import requests
from google.oauth2 import id_token
from jose import jwt
from sqlalchemy import Engine
from starlette import status

from app.logic.users import get_user_by_email
from app.models.token import TokenRequest
from app.models.users import User


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, os.environ["SECRET_KEY"], os.environ["ALGORITHM"])


def get_google_current_user(engine: Engine, google_token: TokenRequest)-> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    id_info = id_token.verify_oauth2_token(
        google_token.token,
        requests.Request(),
        os.environ["GOOGLE_CLIENT_ID"],
    )
    email = id_info["email"]
    if email is None:
        raise credentials_exception
    user = get_user_by_email(engine, email)
    if user is None:
        raise credentials_exception
    return user
