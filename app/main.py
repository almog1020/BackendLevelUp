import uvicorn


def main():
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000,reload=True)

if __name__ == '__main__':
    main()
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import Base, engine, SessionLocal
from app.models import User
from app.core.security import hash_password, verify_password, sanitize_input
from app.schemas import UserRegister, UserLogin, UserResponse, LoginResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Level Up API",
    description="Secure user authentication API",
    version="1.0.0"
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    email = sanitize_input(user_data.email)
    username = sanitize_input(user_data.username)
    
    existing = db.query(User).filter(
        or_(User.email == email, User.username == username)
    ).first()
    
    if existing:
        if existing.email == email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(user_data.password),
        role="user",
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user. Please try again.",
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
    )


@app.post("/login", response_model=LoginResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    email = sanitize_input(credentials.email)
    
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Security: Don't reveal if user exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return LoginResponse(
        message=f"Welcome {user.username}",
        role=user.role
    )


# Entry point for running the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

