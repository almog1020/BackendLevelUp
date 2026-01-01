import os
from sqlalchemy import Engine
from sqlmodel import SQLModel

#db localhost
postgresql_url = "postgresql://Almog:1999@127.0.0.1:5432/levelup"

# Override with Docker environment variable if present
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Docker mode: Use environment variable
    # Remove +psycopg2 from URL if present (SQLModel doesn't need it)
    if database_url.startswith("postgresql+psycopg2://"):
        postgresql_url = database_url.replace("postgresql+psycopg2://", "postgresql://")
    else:
        postgresql_url = database_url

def create_db_and_tables(engine: Engine):
    SQLModel.metadata.create_all(engine)


# ============== In-memory database stores ==============
# These dictionaries and lists act as the data storage for the ETL pipeline.

# In-memory game storage: {game_id: game_dict}
games_db: dict[str, dict] = {}

# In-memory price storage: list of price dicts
prices_db: list[dict] = []
