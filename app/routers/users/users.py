import asyncio
from typing import Annotated
from fastapi import APIRouter, status, Path, HTTPException
from fastapi.params import Depends
from pydantic import EmailStr
from sqlmodel import Session, select
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.dependencies import ActiveEngine, get_current_active_user, get_current_user
from app.logic.users import create_user, select_users, delete_user_by_email, update_user, update_user_status
from app.models.users import UserBase, UserRegister, UserResponse, User, UserStatus, PreferencesUpdate

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)
@router.put("/preferences", status_code=status.HTTP_200_OK)
async def update_preferences(
    engine: ActiveEngine,
    preferences_data: PreferencesUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Update user's gaming preferences (favoriteGenre, preferredStore).
    """
    with Session(engine) as db_session:
        statement = select(User).where(User.id == current_user.id)
        user = db_session.exec(statement).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update preferences if provided
        if preferences_data.favoriteGenre is not None:
            user.favorite_genre = preferences_data.favoriteGenre
        
        if preferences_data.preferredStore is not None:
            user.preferred_store = preferences_data.preferredStore
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        return {
            "message": "Preferences updated successfully",
            "favoriteGenre": user.favorite_genre,
            "preferredStore": user.preferred_store
        }

@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(engine: ActiveEngine, user_data: UserRegister) -> UserResponse:
    """Register a new user"""
    new_user = create_user(engine,user_data)
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        google_id=new_user.google_id,
        role=new_user.role,
        status=new_user.status,
        joined=new_user.joined,
        lastActive=new_user.last_active,
        purchase=new_user.purchase,
        avatar=new_user.avatar
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
@router.get('/me',status_code=status.HTTP_200_OK, response_model=UserResponse)
async def get_me(current_user:Annotated[User, Depends(get_current_active_user)]):
    """Get current authenticated user's basic information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        google_id=current_user.google_id,
        role=current_user.role,
        status=current_user.status,
        joined=current_user.joined,
        lastActive=current_user.last_active,
        purchase=current_user.purchase,
        avatar=current_user.avatar
    )

@router.put('/{email}/logout', status_code=status.HTTP_202_ACCEPTED)
async def logout_user(engine: ActiveEngine,email: Annotated[EmailStr, Path()],disable:UserStatus):
    update_user_status(
        engine=engine,
        email=email,
        disable=disable
    )
@router.websocket("/ws")
async def get_users(engine: ActiveEngine ,ws: WebSocket):
    await ws.accept()
    while True:
        try:
            users_list = select_users(engine)
            await ws.send_json([user.model_dump(mode="json") for user in users_list])
            await asyncio.sleep(5)
        except WebSocketDisconnect:
            print("Client disconnected")


@router.get('/me', response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        google_id=current_user.google_id,
        role=current_user.role,
        status=current_user.status
    )

