from typing import Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
import logging
from app.dependencies import get_current_user
from app.models.games import GameResponse
from app.logic.games import (
    fetch_cheapshark_deals,
    fetch_cheapshark_games_search,
    fetch_cheapshark_game_lookup,
    fetch_price_comparison,
    transform_deal_to_game_response,
)
from app.logic.etl import run_etl_pipeline
import asyncio

router = APIRouter(
    prefix="/games",
    tags=["Games"],
    responses={
        404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


# ============== ENDPOINTS ==============

@router.post("/etl", status_code=status.HTTP_200_OK)
async def trigger_etl(
    search: Optional[str] = Query(None, description="Search term to filter games"),
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger ETL pipeline to fetch game data from external APIs.
    Requires authentication.
    """
    result = await run_etl_pipeline(search=search)
    return result


@router.get("/", response_model=list[GameResponse], status_code=status.HTTP_200_OK)
async def get_all_games():
    """Fetch all games from external APIs."""
    try:
        deals = await fetch_cheapshark_deals(page_size=60)
        games = []
        for deal in deals:
            game = await transform_deal_to_game_response(deal, fetch_rawg=False, fetch_rawg_image=False)
            games.append(game)
        return games
    except Exception as e:
        logger.error(f"Error fetching games: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch games: {str(e)}")


@router.get("/trending", response_model=list[GameResponse], status_code=status.HTTP_200_OK)
async def get_trending_games():
    """Fetch trending games (sorted by deal rating)."""
    try:
        deals = await fetch_cheapshark_deals(sort_by="Deal Rating", page_size=10)
        # Process all games concurrently to avoid timeout issues

        game_tasks = [
            transform_deal_to_game_response(deal, is_trending=True, fetch_rawg=True)
            for deal in deals
        ]
        games = await asyncio.gather(*game_tasks, return_exceptions=True)
        # Filter out any exceptions and convert to list
        valid_games = []
        for game in games:
            if isinstance(game, Exception):
                logger.warning(f"Error processing game: {game}")
                continue
            valid_games.append(game)
        return valid_games
    except Exception as e:
        logger.error(f"Error fetching trending games: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trending games: {str(e)}")


@router.get("/deal-of-the-day", response_model=GameResponse, status_code=status.HTTP_200_OK)
async def get_deal_of_the_day():
    """Fetch the deal of the day (highest discount)."""
    try:
        deals = await fetch_cheapshark_deals(sort_by="Savings", page_size=1)
        if not deals:
            raise HTTPException(status_code=404, detail="No deals found")
        
        deal = deals[0]
        game = await transform_deal_to_game_response(deal, is_deal_of_day=True, fetch_rawg=True)
        return game
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching deal of the day: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch deal of the day: {str(e)}")


@router.get("/search", response_model=list[GameResponse], status_code=status.HTTP_200_OK)
async def search_games(q: str = Query(..., description="Search query")):
    """Search games by query term."""
    if not q or not q.strip():
        return []
    
    try:
        games_data = await fetch_cheapshark_games_search(q.strip())
        games_data = games_data[:20]
        
        games = []
        for game_data in games_data:
            cheapest = float(game_data.get("cheapest", 0))
            estimated_original = cheapest / 0.8 if cheapest > 0 else 0
            
            deal_like = {
                "gameID": game_data.get("gameID", ""),
                "title": game_data.get("external", "Unknown"),
                "thumb": game_data.get("thumb", ""),
                "salePrice": cheapest,
                "normalPrice": estimated_original,
                "savings": "20.0",
            }
            game = await transform_deal_to_game_response(deal_like, fetch_rawg=False, fetch_rawg_image=False)
            games.append(game)
        
        return games
    except Exception as e:
        logger.error(f"Error searching games: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search games: {str(e)}")


@router.get("/{game_id}", response_model=GameResponse, status_code=status.HTTP_200_OK)
async def get_game_by_id(game_id: str):
    """Fetch a single game by ID."""
    try:
        # Extract CheapShark gameID from our ID format (cs_123 -> 123)
        if game_id.startswith("cs_"):
            cheapshark_game_id = game_id.replace("cs_", "")
            matching_deal = None
            
            # First, try the CheapShark lookup API (works for search results)
            game_lookup = await fetch_cheapshark_game_lookup(cheapshark_game_id)
            if game_lookup:
                cheapest = float(game_lookup.get("cheapest", 0))
                estimated_original = cheapest / 0.8 if cheapest > 0 else 0
                matching_deal = {
                    "gameID": cheapshark_game_id,
                    "title": game_lookup.get("external", "Unknown"),
                    "thumb": game_lookup.get("thumb", ""),
                    "salePrice": cheapest,
                    "normalPrice": estimated_original,
                    "savings": "20.0",
                    "dealID": game_lookup.get("cheapestDealID", ""),
                }
            
            # If lookup didn't work, try to find in current deals
            if not matching_deal:
                deals = await fetch_cheapshark_deals(page_size=200)
                for deal in deals:
                    if str(deal.get("gameID", "")) == cheapshark_game_id:
                        matching_deal = deal
                        break
            
            # If still not found, raise 404
            if not matching_deal:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Game with ID {game_id} not found. The game may no longer be available."
                )
            
            price_comparison = await fetch_price_comparison(cheapshark_game_id)
            game = await transform_deal_to_game_response(matching_deal, fetch_rawg=True, price_comparison=price_comparison)
            return game
        else:
            raise HTTPException(status_code=404, detail=f"Invalid game ID format: {game_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch game: {str(e)}")
