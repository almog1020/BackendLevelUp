from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy import Engine
from sqlmodel import Session, select
from typing import Sequence, Annotated, TYPE_CHECKING

from app.models.users import User, UserBase, UserRegister, UserRole, UserStatus
from app.utilities.passwords import get_password_hash

if TYPE_CHECKING:
    from app.dependencies import ActiveEngine, get_current_user


def require_admin(engine: "ActiveEngine", user: "User"):
    """
    Admin-only guard.

    Uses get_current_user() to authenticate the request, then checks the user's role.
    Supports role stored as:
      - Enum (e.g., UserRole.ADMIN)   -> role.value or role.name
      - String (e.g., "admin")
    
    Usage:
        from app.dependencies import get_current_user, ActiveEngine
        from app.logic.users import require_admin
        
        @router.get("/admin/endpoint")
        async def admin_endpoint(
            engine: ActiveEngine,
            user: User = Depends(get_current_user)
        ):
            admin_user = require_admin(engine, user)
            ...
    """
    # Lazy import to avoid circular dependency
    from app.dependencies import get_current_user

    role_value = getattr(user, "role", None)

    # If role is missing, block access
    if role_value is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access only",
        )

    # Convert role to a comparable lowercase string
    # If enum: role.value (preferred), else role.name; if string: itself
    if hasattr(role_value, "value"):
        role_str = str(role_value.value).lower()
    elif hasattr(role_value, "name"):
        role_str = str(role_value.name).lower()
    else:
        role_str = str(role_value).lower()

    # Accept only admin
    if role_str != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access only",
        )

    return user

def update_user(*, engine: Engine, edit_user: UserBase, email: EmailStr):
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).one()

        user.email = email
        user.role = edit_user.role
        user.status = edit_user.status
        user.purchase = edit_user.purchase

        session.add(user)
        session.commit()

def update_user_status(*, engine: Engine, disable: UserStatus, email: EmailStr):
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).one()

        user.status = disable

        session.add(user)
        session.commit()

def delete_user_by_email(engine: Engine, email: EmailStr):
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        session.delete(user)
        session.commit()


def select_users(engine: Engine) -> Sequence[User]:
    with Session(engine) as session:
        return session.exec(select(User).order_by(User.id)).all()

def select_user(engine: Engine,user:Annotated[OAuth2PasswordRequestForm, Depends()]) -> User | None:
    """Pull out the user from the database and verify password"""
    with Session(engine) as session:
        statement = select(User).where(User.email == user.username)
        return session.exec(statement).first()


def get_user_by_username(engine: Engine, name: str) -> User | None:
    """Get user by name"""
    with Session(engine) as session:
        statement = select(User).where(User.name == name)
        return session.exec(statement).first()


def get_user_by_email(engine: Engine, email: EmailStr) -> User | None:
    """Get user by email"""
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()


def get_user_by_google_id(engine: Engine, google_id: str) -> User | None:
    """Get user by Google ID"""
    with Session(engine) as session:
        statement = select(User).where(User.google_id == google_id)
        return session.exec(statement).first()


def create_user(engine: Engine, user_data: UserRegister) -> User:
    """Create a new user with hashed password"""
    with Session(engine) as session:
        # Check if email already exists
        existing_user = get_user_by_email(engine, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Create new user
        new_user = User(
            email=user_data.email,
            password=hashed_password,
            name=user_data.name,
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return new_user


def create_user_from_google(engine: Engine, email: EmailStr, name: str | None, google_id: str) -> User:
    """Create a new user from Google OAuth data"""
    with Session(engine) as session:
        # Check if user already exists by email or google_id
        existing_user = get_user_by_email(engine, email)
        if existing_user:
            # Update google_id if not set
            if not existing_user.google_id:
                existing_user.google_id = google_id
                session.add(existing_user)
                session.commit()
                session.refresh(existing_user)
            return existing_user

        existing_google_user = get_user_by_google_id(engine, google_id)
        if existing_google_user:
            return existing_google_user

        # Create new user
        new_user = User(
            email=email,
            name=name,
            google_id=google_id,
            password=None,  # No password for OAuth users
            status=UserStatus.ACTIVE,
            purchase=0,
            role=UserRole.USER
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return new_user
