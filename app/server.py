from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import create_engine
from app.db import create_db_and_tables, postgresql_url
from app.routers.auth import auth
from app.routers.reviews import reviews
from app.routers.users import users
from app.routers.profile import profile
from app.routers.purchases import purchases
from app.routers.games import games


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_engine(postgresql_url, echo=True)
    create_db_and_tables(engine)
    app.state.engine = engine
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

@app.middleware("http")
async def add_engine_to_request(request, call_next):
    """Add engine to request state for dependency injection"""
    request.state.engine = app.state.engine
    response = await call_next(request)
    return response

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(purchases.router)
app.include_router(games.router)

app.include_router(reviews.router)






