from sqlmodel import create_engine, SQLModel

#db localhost
postgresql_url = "postgresql://Almog:1999@127.0.0.1:5432/levelup"
engine = create_engine(postgresql_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

