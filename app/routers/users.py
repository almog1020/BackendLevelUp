from fastapi import APIRouter

from ..logic.users import select_user
from ..models.users import User, UserBase

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post('/login')
async def login(user: UserBase)-> None | User:
    return select_user(user)