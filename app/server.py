import asyncio
from contextlib import asynccontextmanager
from time import sleep

from fastapi import FastAPI,WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from sqlmodel import create_engine
from app.db import create_db_and_tables, postgresql_url
from app.dependencies import ActiveEngine
from app.logic.users import select_users
from app.routers.auth import auth
from app.routers.users import users
from app.routers.games import games



@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_engine(postgresql_url, echo=True)
    create_db_and_tables(engine)
    yield {"engine": engine}
    engine.dispose()
app = FastAPI(lifespan=lifespan)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5179",
        "http://127.0.0.1:5179",
        "http://host.docker.internal:5173",
        "http://host.docker.internal:5179",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(games.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(engine: ActiveEngine ,ws: WebSocket):
    await ws.accept()
    while True:
        try:
            users_list = select_users(engine)
            await ws.send_json([user.model_dump(mode="json") for user in users_list])
            await asyncio.sleep(5)
        except WebSocketDisconnect:
            print("Client disconnected")






