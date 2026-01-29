from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import create_engine
from app.db import create_db_and_tables, postgresql_url
from app.routers.auth import auth
from app.routers.reviews import reviews
from app.routers.users import users
from app.routers.purchases import purchases
from app.routers.games import games
from app.routers.admin.games import router as admin_games_router
from app.routers.admin.genres import router as admin_genres_router
from app.routers.admin.topdeals import router as admin_topdeals_router


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
app.include_router(purchases.router)
app.include_router(games.router)
app.include_router(admin_games_router)
app.include_router(admin_genres_router)
app.include_router(admin_topdeals_router)
app.include_router(reviews.router)





