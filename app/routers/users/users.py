from fastapi import APIRouter, HTTPException, status
from app.logic.users import select_user
from app.models.users import User, UserBase

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

@router.post('/login')
async def login(user: UserBase)-> None | User:
     user = select_user(user)
     if user:
         return user
     else:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect email or password")