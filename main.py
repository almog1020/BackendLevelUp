import uvicorn
from fastapi import FastAPI

from routes.auth import router as auth_router
from routes.games import router as games_router

app = FastAPI(
    title="LevelUp API",
    description="PC Game Price Comparison Platform",
    version="1.0.0"
)

# Include routers
app.include_router(auth_router)
app.include_router(games_router)


@app.get("/")
async def root():
    return {"message": "Welcome to LevelUp API"}


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == '__main__':
    main()
