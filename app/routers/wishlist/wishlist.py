from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from app.dependencies import ActiveEngine
from app.logic.wishlist import (
    get_user_wishlist,
    get_wishlist_game_ids,
    add_to_wishlist,
    remove_from_wishlist,
)
from app.logic.users import get_current_user
from app.models.wishlist import WishlistResponse, WishlistCreate
from app.models.users import User

router = APIRouter(
    prefix="/wishlist",
    tags=["wishlist"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get("/", response_model=list[WishlistResponse], status_code=status.HTTP_200_OK)
async def get_my_wishlist(
    engine: ActiveEngine,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get the current user's wishlist"""
    items = get_user_wishlist(engine, current_user.id)
    return [
        WishlistResponse(
            id=item.id,
            user_id=item.user_id,
            game_id=item.game_id,
            game_title=item.game_title,
            game_image_url=item.game_image_url,
            game_price=item.game_price,
            game_original_price=item.game_original_price,
            game_discount=item.game_discount,
            store_id=item.store_id,
            deal_id=item.deal_id,
            added_date=item.added_date,
        )
        for item in items
    ]


@router.get("/ids", response_model=list[str], status_code=status.HTTP_200_OK)
async def get_my_wishlist_ids(
    engine: ActiveEngine,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get just the game IDs in the current user's wishlist"""
    return get_wishlist_game_ids(engine, current_user.id)


@router.post("/", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED)
async def add_game_to_wishlist(
    engine: ActiveEngine,
    data: WishlistCreate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Add a game to the current user's wishlist"""
    try:
        item = add_to_wishlist(engine, current_user.id, data)
        return WishlistResponse(
            id=item.id,
            user_id=item.user_id,
            game_id=item.game_id,
            game_title=item.game_title,
            game_image_url=item.game_image_url,
            game_price=item.game_price,
            game_original_price=item.game_original_price,
            game_discount=item.game_discount,
            store_id=item.store_id,
            deal_id=item.deal_id,
            added_date=item.added_date,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_game_from_wishlist(
    engine: ActiveEngine,
    game_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Remove a game from the current user's wishlist"""
    removed = remove_from_wishlist(engine, current_user.id, game_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found in wishlist"
        )
