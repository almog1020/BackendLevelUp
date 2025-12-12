import os

from dotenv import load_dotenv
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests

from sqlmodel import Session, select

from app.logic.users import create_user_from_google, get_user_by_email, get_user_by_google_id
from app.models.users import UserResponse, User
from app.db import engine

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

load_dotenv()

class TokenRequest(BaseModel):
    token: str

@router.post("/google", response_model=UserResponse)
async def google_auth(data: TokenRequest):
    """Login or signup with Google authentication"""
    try:
        id_info = id_token.verify_oauth2_token(
            data.token,
            requests.Request(),
            os.environ["GOOGLE_CLIENT_ID"],
        )
        
        email = id_info["email"]
        name = id_info.get("name")
        google_id = id_info["sub"]
        picture = id_info.get("picture")
        
        # Check if user exists by email or google_id
        user = get_user_by_email(email) or get_user_by_google_id(google_id)
        
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
                        session.add(db_user)
                        session.commit()
                        session.refresh(db_user)
                        user = db_user
        else:
            # New user - signup flow
            user = create_user_from_google(email, name, google_id, picture)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            google_id=user.google_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Google token")
