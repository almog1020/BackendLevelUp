from sqlalchemy import Column, Integer, String, UniqueConstraint, Index
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")

    # Performance: Unique constraints and indexes for fast lookups
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
        Index("idx_users_role", "role"),
    )
