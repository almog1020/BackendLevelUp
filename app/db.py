import os

from sqlalchemy import Engine, text
from sqlmodel import SQLModel

# Use DATABASE_URL if set (e.g. PostgreSQL); otherwise SQLite for local dev (no DB setup needed)
postgresql_url = os.getenv("DATABASE_URL") or "sqlite:///./levelup.db"


def _add_last_login_if_missing(engine: Engine) -> None:
    """Add last_login column to users if it doesn't exist (for existing DBs)."""
    dialect = engine.url.get_backend_name()
    with engine.begin() as conn:
        if dialect == "sqlite":
            cursor = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in cursor.fetchall()]
            if "last_login" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))
        else:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP"))


def create_db_and_tables(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)
    try:
        _add_last_login_if_missing(engine)
    except Exception:
        pass
