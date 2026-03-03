from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.dependencies import ActiveEngine, get_current_user
from app.models.users import User
from app.models.wishlist import WishlistCreate, WishlistItem, WishlistRead

router = APIRouter(
    prefix="/wishlist",
    tags=["wishlist"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.post(
    "",
    response_model=WishlistRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {"description": "Already exists"},
        201: {"description": "Created"},
    },
)
async def add_to_wishlist(
    user: Annotated[User, Depends(get_current_user)],
    engine: ActiveEngine,
    response: Response,
    payload: WishlistCreate = Body(...),
):
    """Add a game to the current user's wishlist."""
    if not payload.game_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="game_id is required",
        )
    title = payload.title

    with Session(engine) as session:
        existing = session.exec(
            select(WishlistItem).where(
                WishlistItem.user_id == user.id,
                WishlistItem.external_game_id == payload.game_id,
            )
        ).first()
        if existing:
            response.status_code = status.HTTP_200_OK
            return WishlistRead(
                id=existing.id,
                external_game_id=existing.external_game_id,
                title=existing.title,
                thumb=existing.thumb,
                created_at=existing.created_at,
            )

        wishlist = WishlistItem(
            user_id=user.id,
            external_game_id=payload.game_id,
            title=title,
            thumb=payload.thumb,
        )
        session.add(wishlist)
        session.commit()
        session.refresh(wishlist)

        return WishlistRead(
            id=wishlist.id,
            external_game_id=wishlist.external_game_id,
            title=wishlist.title,
            thumb=wishlist.thumb,
            created_at=wishlist.created_at,
        )


@router.get(
    "",
    response_model=list[WishlistRead],
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Wishlist",
            "content": {"application/json": {"example": []}},
        }
    },
)
async def get_my_wishlist(
    user: Annotated[User, Depends(get_current_user)],
    engine: ActiveEngine,
):
    """Get the current user's wishlist items."""
    with Session(engine) as session:
        items = session.exec(
            select(WishlistItem)
            .where(WishlistItem.user_id == user.id)
            .order_by(WishlistItem.created_at.desc())
        ).all()
        return list(items)


@router.delete(
    "/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_from_wishlist(
    game_id: str,
    user: Annotated[User, Depends(get_current_user)],
    engine: ActiveEngine,
):
    """Remove a game from the current user's wishlist."""
    with Session(engine) as session:
        item = session.exec(
            select(WishlistItem).where(
                WishlistItem.user_id == user.id,
                WishlistItem.external_game_id == game_id,
            )
        ).first()

        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")
        session.delete(item)
        session.commit()
