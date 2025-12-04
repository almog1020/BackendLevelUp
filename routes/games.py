from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from auth import get_current_user
from database import games_db, prices_db
from schemas import Game, GamePrice, GameWithPrices
from etl import run_etl_pipeline

router = APIRouter(prefix="/games", tags=["Games"])


@router.post("/etl", status_code=status.HTTP_200_OK)
async def trigger_etl(
    search: Optional[str] = Query(None, description="Search term to filter games"),
    rawg_api_key: Optional[str] = Query(None, description="Optional RAWG API key"),
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger ETL pipeline to fetch game data from external APIs.
    Requires authentication.
    """
    result = await run_etl_pipeline(search=search, rawg_api_key=rawg_api_key)
    return result


@router.get("/", response_model=list[Game])
async def list_games(
    genre: Optional[str] = Query(None, description="Filter by genre"),
):
    """Get all games, optionally filtered by genre."""
    games = list(games_db.values())
    
    if genre:
        games = [g for g in games if g.get("genre", "").lower() == genre.lower()]
    
    return games


@router.get("/{game_id}", response_model=GameWithPrices)
async def get_game(game_id: str):
    """Get a game with all its prices across stores."""
    if game_id not in games_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    
    game = games_db[game_id]
    game_prices = [p for p in prices_db if p["game_id"] == game_id]
    
    return GameWithPrices(
        game=Game(**game),
        prices=[GamePrice(**p) for p in game_prices]
    )


@router.get("/{game_id}/prices", response_model=list[GamePrice])
async def get_game_prices(game_id: str):
    """Get all prices for a specific game."""
    if game_id not in games_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    
    return [p for p in prices_db if p["game_id"] == game_id]

