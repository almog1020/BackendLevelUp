from typing import Annotated
from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from sqlalchemy import Engine
from sqlmodel import Session, select

from app.dependencies import ActiveEngine, get_current_active_user
from app.logic.auth import get_password_hash
from app.logic.users import get_user_by_email
from app.models.users import (
    User,
    ProfileUpdate,
    PreferencesUpdate,
    ProfileResponse,
    ProfileData,
    StatisticsData,
    PreferencesData,
    ActivityData
)

router = APIRouter(
    prefix="/profile",
    tags=["profile"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get("", response_model=ProfileResponse, status_code=status.HTTP_200_OK)
async def get_profile(
    engine: ActiveEngine,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get complete profile data including statistics, preferences, and activities.
    Returns placeholder/default values for statistics and activities until those features are implemented.
    """
    with Session(engine) as db_session:
        # Get fresh user data from database
        statement = select(User).where(User.id == current_user.id)
        user = db_session.exec(statement).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Build profile data
        profile = ProfileData(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            avatar=user.avatar,
            memberSince=user.joined,
            lastLogin=user.last_active or user.joined
        )
        
        # Build preferences data
        preferences = PreferencesData(
            favoriteGenre=user.favorite_genre,
            preferredStore=user.preferred_store
        )
        
        # Statistics (placeholder values - will be implemented when those features are added)
        statistics = StatisticsData(
            wishlistItems=0,
            totalSaved=0.0,
            gamesTracked=0,
            priceAlerts=0,
            reviewsWritten=0
        )
        
        # Activities (empty list for now - will be implemented when activity tracking is added)
        activities: list[ActivityData] = []
        
        return ProfileResponse(
            profile=profile,
            statistics=statistics,
            preferences=preferences,
            activities=activities
        )


@router.put("", status_code=status.HTTP_200_OK)
async def update_profile(
    engine: ActiveEngine,
    update_data: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Update user's profile information (name, email, password, avatar).
    Password is hashed before storing.
    """
    with Session(engine) as db_session:
        statement = select(User).where(User.id == current_user.id)
        user = db_session.exec(statement).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if email is being updated and if it's already taken
        if update_data.email and update_data.email != user.email:
            existing_user = get_user_by_email(engine, update_data.email)
            if existing_user and existing_user.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists"
                )
            user.email = update_data.email
        
        # Update name if provided
        if update_data.name is not None:
            user.name = update_data.name
        
        # Update password if provided (hash it first)
        if update_data.password is not None:
            user.password = get_password_hash(update_data.password)
        
        # Update avatar if provided
        if update_data.avatar is not None:
            user.avatar = update_data.avatar
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        return {"message": "Profile updated successfully"}


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
