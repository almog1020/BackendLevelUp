from sqlalchemy import Engine, desc
from sqlmodel import Session, select
from typing import Sequence
from app.models.wishlist import Wishlist, WishlistCreate
from app.models.users import User


def get_user_wishlist(engine: Engine, user_id: int) -> Sequence[Wishlist]:
    """Get all wishlist items for a user"""
    with Session(engine) as session:
        statement = (
            select(Wishlist)
            .where(Wishlist.user_id == user_id)
            .order_by(desc(Wishlist.added_date))
        )
        return session.exec(statement).all()


def get_wishlist_game_ids(engine: Engine, user_id: int) -> list[str]:
    """Get just the game IDs in user's wishlist (for quick checks)"""
    with Session(engine) as session:
        statement = select(Wishlist.game_id).where(Wishlist.user_id == user_id)
        return list(session.exec(statement).all())


def add_to_wishlist(engine: Engine, user_id: int, data: WishlistCreate) -> Wishlist:
    """Add a game to user's wishlist"""
    with Session(engine) as session:
        # Check if already in wishlist
        existing = session.exec(
            select(Wishlist)
            .where(Wishlist.user_id == user_id)
            .where(Wishlist.game_id == data.game_id)
        ).first()

        if existing:
            raise ValueError("Game already in wishlist")

        item = Wishlist(
            user_id=user_id,
            game_id=data.game_id,
            game_title=data.game_title,
            game_image_url=data.game_image_url,
            game_price=data.game_price,
            game_original_price=data.game_original_price,
            game_discount=data.game_discount,
            store_id=data.store_id,
            deal_id=data.deal_id,
        )

        session.add(item)
        session.commit()
        session.refresh(item)
        return item


def remove_from_wishlist(engine: Engine, user_id: int, game_id: str) -> bool:
    """Remove a game from user's wishlist"""
    with Session(engine) as session:
        item = session.exec(
            select(Wishlist)
            .where(Wishlist.user_id == user_id)
            .where(Wishlist.game_id == game_id)
        ).first()

        if not item:
            return False

        session.delete(item)
        session.commit()
        return True


def is_in_wishlist(engine: Engine, user_id: int, game_id: str) -> bool:
    """Check if a game is in user's wishlist"""
    with Session(engine) as session:
        item = session.exec(
            select(Wishlist)
            .where(Wishlist.user_id == user_id)
            .where(Wishlist.game_id == game_id)
        ).first()
        return item is not None
