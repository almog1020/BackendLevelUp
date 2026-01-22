from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import create_engine
from app.db import create_db_and_tables, postgresql_url
from app.routers.auth import auth
from app.routers.reviews import reviews
from app.routers.users import users
from app.routers.games import games


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_engine(postgresql_url, echo=True)
    create_db_and_tables(engine)
    yield {"engine": engine}
    engine.dispose()
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173','https://frontend-level-up-delta.vercel.app'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(games.router)

app.include_router(reviews.router)






