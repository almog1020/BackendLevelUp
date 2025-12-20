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



@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_engine(postgresql_url, echo=True)
    create_db_and_tables(engine)
    yield {"engine": engine}
    engine.dispose()
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

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






