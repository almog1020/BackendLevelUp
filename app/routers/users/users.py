from typing import Annotated
from fastapi import APIRouter, status, Path
from pydantic import EmailStr
from app.dependencies import ActiveEngine
from app.logic.users import create_user, select_users, delete_user_by_email, update_user
from app.models.users import UserBase, UserRegister, UserResponse


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(engine: ActiveEngine, user_data: UserRegister) -> UserResponse:
    """Register a new user"""
    new_user = create_user(engine,user_data)
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        google_id=new_user.google_id,
        role=new_user.role
    )


@router.get('/',status_code=status.HTTP_200_OK)
async def get_users(engine: ActiveEngine):
    return select_users(engine)


@router.delete('/{email}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(engine: ActiveEngine, email: EmailStr):
    delete_user_by_email(engine,email)



@router.put('/{email}', status_code=status.HTTP_202_ACCEPTED)
async def edit_user(engine: ActiveEngine, email: Annotated[EmailStr, Path()], user: UserBase):
    update_user(
        engine=engine,
        edit_user=user,
        email=email
    )

