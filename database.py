from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from app import settings


Base = declarative_base()


SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Security: Connection pool settings for PostgreSQL reliability
# pool_pre_ping: Validates connections before use
# pool_recycle: Recycles connections after 1 hour
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("SQL_ECHO", "False").lower() == "true"
)

# For production: Enable SSL connection
# connect_args = {
#     "sslmode": "require"
# }


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
