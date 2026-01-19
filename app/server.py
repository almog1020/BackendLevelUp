import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI,WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from sqlmodel import create_engine
from app.db import create_db_and_tables, postgresql_url
from app.dependencies import ActiveEngine
from app.logic.users import select_users
from app.routers.auth import auth
from app.routers.users import users
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

# DEV ONLY — CORS configuration (restrict origins in production)
app.add_middleware(
    CORSMiddleware,
<<<<<<< HEAD
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when allow_origins=["*"]
=======
    allow_origins=['http://localhost:5173','https://frontend-level-up-delta.vercel.app'],
    allow_credentials=True,
>>>>>>> main
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(admin_games_router)
app.include_router(admin_genres_router)
app.include_router(admin_topdeals_router)

<<<<<<< HEAD
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

=======
>>>>>>> main
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






