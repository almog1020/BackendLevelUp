import os
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pydantic import EmailStr

from sqlalchemy import Engine
from starlette import status
from starlette.requests import HTTPConnection

from app.logic.users import get_user_by_email
from app.models.token import TokenData
from app.models.users import User, UserStatus


async def get_engine(request: HTTPConnection) -> Engine:
    return request.state.engine

ActiveEngine = Annotated[Engine, Depends(get_engine)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(engine: ActiveEngine, token: Annotated[EmailStr, Depends(oauth2_scheme)]) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.environ["SECRET_KEY"], algorithms=[os.environ["ALGORITHM"]])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token = TokenData(username=username)
        user = get_user_by_email(engine, token.username)
        if user is None:
            raise credentials_exception
        return user
    except InvalidTokenError:
        raise credentials_exception

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user



