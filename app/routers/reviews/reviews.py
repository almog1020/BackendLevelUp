import asyncio
import json

from fastapi import APIRouter, HTTPException
from sqlalchemy import null
from starlette import status
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.dependencies import ActiveEngine
from app.logic.reviews import create_review, select_reviews, get_game_reviews, delete_review, get_review, get_user_reviews
from app.models.reviews import Review
from app.models.users import User

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_review(engine: ActiveEngine, review_data: Review) -> None:
    create_review(engine=engine, review_data=review_data)


@router.get("/", status_code=status.HTTP_200_OK)
async def read_reviews(engine: ActiveEngine):
    return select_reviews(engine=engine)


@router.get("/user/{user_id}", status_code=status.HTTP_200_OK)
async def read_user_reviews(user_id: int, engine: ActiveEngine):
    """Get all reviews written by a specific user."""
    return get_user_reviews(engine=engine, user_id=user_id)


@router.get("/{game}", status_code=status.HTTP_200_OK)
async def read_game_reviews(game: str, engine: ActiveEngine):
    return get_game_reviews(game=game, engine=engine)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_review(engine: ActiveEngine, id: int) -> None:
    review = get_review(engine=engine, review_id=id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review not found"
        )
    delete_review(engine=engine, review_id=id)

@router.websocket("/ws")
async def get_reviews(engine: ActiveEngine, ws: WebSocket):
    await ws.accept()
    while True:
        try:
            reviews = select_reviews(engine=engine)
            await ws.send_json([
                {"review": review.model_dump(mode='json'), "user": user.model_dump(mode="json")}
                if user else
                {"review": review.model_dump(mode='json'), "user": None}
                for review, user in reviews
            ])
            await asyncio.sleep(5)
        except WebSocketDisconnect:
            print("Client disconnected")



