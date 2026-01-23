from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Query
from app.dependencies import ActiveEngine, get_current_user
from app.logic.purchases import get_user_purchases, create_purchase
from app.models.purchases import PurchaseResponse, PurchaseCreate
from app.models.users import User

router = APIRouter(
    prefix="/purchases",
    tags=["purchases"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get("/me", response_model=list[PurchaseResponse], status_code=status.HTTP_200_OK)
async def get_my_purchases(
    engine: ActiveEngine,
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of purchases to return")
):
    """Get the current user's last purchases"""
    purchases = get_user_purchases(engine, current_user.id, limit=limit)
    return [
        PurchaseResponse(
            id=purchase.id,
            user_id=purchase.user_id,
            game_id=purchase.game_id,
            game_title=purchase.game_title,
            game_image_url=purchase.game_image_url,
            game_genre=purchase.game_genre,
            purchase_date=purchase.purchase_date,
            price=purchase.price,
            store=purchase.store
        )
        for purchase in purchases
    ]


@router.post("/", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def create_user_purchase(
    engine: ActiveEngine,
    purchase_data: PurchaseCreate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Create a new purchase for the current user"""
    try:
        purchase = create_purchase(engine, current_user.id, purchase_data)
        return PurchaseResponse(
            id=purchase.id,
            user_id=purchase.user_id,
            game_id=purchase.game_id,
            game_title=purchase.game_title,
            game_image_url=purchase.game_image_url,
            game_genre=purchase.game_genre,
            purchase_date=purchase.purchase_date,
            price=purchase.price,
            store=purchase.store
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
