import os

from sqlalchemy import Engine
from sqlmodel import SQLModel

# postgresql_url = os.getenv("DATABASE_URL", default="postgresql://Almog:1999@127.0.0.1:5432/levelup")
postgresql_url = "postgresql://Almog:1999@127.0.0.1:5432/levelup"
def create_db_and_tables(engine: Engine):
    SQLModel.metadata.create_all(engine)

