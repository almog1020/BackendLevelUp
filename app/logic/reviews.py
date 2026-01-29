import json
from typing import Any

from sqlmodel import Session, select
from sqlalchemy import Engine, delete

from app.models.reviews import Review, ReviewBase
from app.models.users import User


def create_review(*, engine: Engine, review_data: ReviewBase) -> None:
    with Session(engine) as session:
        # Check if user already has a review for this game
        if review_data.user_id is not None:
            existing = session.exec(
                select(Review).where(
                    Review.user_id == review_data.user_id,
                    Review.game == review_data.game
                )
            ).first()
            
            if existing:
                # Update existing review instead of creating duplicate
                existing.star = review_data.star
                existing.comment = review_data.comment
                session.add(existing)
                session.commit()
                return
        
        # Create new review
        review = Review(comment=review_data.comment, star=review_data.star, user_id=review_data.user_id,
                        game=review_data.game)
        session.add(review)
        session.commit()


def select_reviews(*, engine: Engine) -> list[tuple[Review, User]]:
    with Session(engine) as session:
        statement = select(Review, User).join(User,isouter=True)
        results = session.exec(statement)
        return list(results)

def get_game_reviews(*, engine: Engine, game: str) -> list[dict[str, Any | None]]:
    with Session(engine) as session:
        statement = select(Review, User).join(User,isouter=True).where(Review.game == game)
        results = session.exec(statement)
        return [
                {"review": review, "user": user}
                if user else
                {"review": review, "user": None}
                for review, user in list(results)
            ]


def delete_review(*, engine: Engine, review_id: int) -> None:
    with Session(engine) as session:
        statement = delete(Review).where(Review.id == review_id)
        session.exec(statement)
        session.commit()


def get_review(*, engine: Engine, review_id: int) -> Review | None:
    with Session(engine) as session:
        statement = select(Review).where(Review.id == review_id)
        results = session.exec(statement)
        return results.first()


def get_user_reviews(*, engine: Engine, user_id: int) -> list[Review]:
    """Get all reviews written by a specific user."""
    with Session(engine) as session:
        statement = select(Review).where(Review.user_id == user_id)
        results = session.exec(statement)
        return list(results)
