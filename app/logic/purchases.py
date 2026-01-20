from sqlalchemy import Engine, desc
from sqlmodel import Session, select
from typing import Sequence
from app.models.purchases import Purchase, PurchaseCreate, PurchaseResponse
from app.models.users import User


def create_purchase(engine: Engine, user_id: int, purchase_data: PurchaseCreate) -> Purchase:
    """Create a new purchase record for a user"""
    with Session(engine) as session:
        # Verify user exists
        user = session.get(User, user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        # Create purchase
        new_purchase = Purchase(
            user_id=user_id,
            game_id=purchase_data.game_id,
            game_title=purchase_data.game_title,
            game_image_url=purchase_data.game_image_url,
            game_genre=purchase_data.game_genre,
            price=purchase_data.price,
            store=purchase_data.store
        )
        
        session.add(new_purchase)
        session.commit()
        session.refresh(new_purchase)
        
        # Update user's purchase count
        user.purchase += 1
        session.add(user)
        session.commit()
        
        return new_purchase


def get_user_purchases(engine: Engine, user_id: int, limit: int = 10) -> Sequence[Purchase]:
    """Get the most recent purchases for a user, ordered by purchase_date descending"""
    with Session(engine) as session:
        statement = (
            select(Purchase)
            .where(Purchase.user_id == user_id)
            .order_by(desc(Purchase.purchase_date))
            .limit(limit)
        )
        return session.exec(statement).all()
