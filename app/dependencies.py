from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import Engine
from starlette.requests import HTTPConnection


async def get_engine(request: HTTPConnection) -> Engine:
    return request.state.engine


ActiveEngine = Annotated[Engine, Depends(get_engine)]

ActiveUser = Annotated[OAuth2PasswordRequestForm, Depends()]