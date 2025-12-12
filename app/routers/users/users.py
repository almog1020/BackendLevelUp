from fastapi import APIRouter, HTTPException, status
from app.logic.users import select_user, create_user
from app.models.users import User, UserBase, UserRegister, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

@router.post('/login', response_model=UserResponse)
async def login(user: UserBase) -> UserResponse:
    """Login with email and password"""
    db_user = select_user(user)
    if db_user:
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            name=db_user.name,
            google_id=db_user.google_id
        )
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect email or password")


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister) -> UserResponse:
    """Register a new user"""
    try:
        new_user = create_user(user_data)
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            name=new_user.name,
            google_id=new_user.google_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )