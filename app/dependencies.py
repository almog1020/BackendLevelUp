from typing import Annotated

from fastapi import Depends

from sqlalchemy import Engine
from starlette.requests import HTTPConnection


async def get_engine(request: HTTPConnection) -> Engine:
    return request.state.engine


ActiveEngine = Annotated[Engine, Depends(get_engine)]