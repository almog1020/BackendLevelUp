"""
ETL Pipeline for extracting game data from external APIs.

Extract: Pull raw data from external game store APIs
Transform: Normalize and clean data into standard format
Load: Store processed data in database
"""

import httpx
from typing import Optional
from datetime import datetime

from app.schemas import Game, GamePrice


# ============== EXTRACT ==============

async def extract_from_cheapshark(search: Optional[str] = None) -> list[dict]:
    """
    Extract game deals from CheapShark API (free, no API key needed).
    https://apidocs.cheapshark.com/
    """
    async with httpx.AsyncClient() as client:
        # Get deals from CheapShark
        url = "https://www.cheapshark.com/api/1.0/deals"
        params = {"pageSize": 20}
        if search:
            params["title"] = search
        
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def extract_from_rawg(search: Optional[str] = None, api_key: Optional[str] = None) -> list[dict]:
    """
    Extract game info from RAWG API (free tier available).
    https://rawg.io/apidocs
    
    Note: Requires API key from https://rawg.io/apidocs
    """
    if not api_key:
        return []  # Skip if no API key
    
    async with httpx.AsyncClient() as client:
        url = "https://api.rawg.io/api/games"
        params = {"key": api_key, "page_size": 20}
        if search:
            params["search"] = search
        
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])


# ============== TRANSFORM ==============

def transform_cheapshark_deal(raw_deal: dict) -> tuple[Game, GamePrice]:
    """Transform CheapShark deal data into our schema."""
    game = Game(
        id=f"cs_{raw_deal.get('gameID', '')}",
        title=raw_deal.get("title", "Unknown"),
        genre=None,  # CheapShark doesn't provide genre
        image_url=raw_deal.get("thumb"),
    )
    
    price = GamePrice(
        game_id=game.id,
        store=_get_store_name(raw_deal.get("storeID", "0")),
        price=float(raw_deal.get("salePrice", 0)),
        currency="USD",
        url=f"https://www.cheapshark.com/redirect?dealID={raw_deal.get('dealID', '')}",
    )
    
    return game, price


def transform_rawg_game(raw_game: dict) -> Game:
    """Transform RAWG game data into our schema."""
    genres = raw_game.get("genres", [])
    genre = genres[0]["name"] if genres else None
    
    return Game(
        id=f"rawg_{raw_game.get('id', '')}",
        title=raw_game.get("name", "Unknown"),
        genre=genre,
        image_url=raw_game.get("background_image"),
    )


def _get_store_name(store_id: str) -> str:
    """Map CheapShark store IDs to names."""
    stores = {
        "1": "Steam",
        "2": "GamersGate",
        "3": "GreenManGaming",
        "7": "GOG",
        "8": "Origin",
        "11": "Humble Store",
        "13": "Uplay",
        "25": "Epic Games",
    }
    return stores.get(store_id, f"Store {store_id}")


# ============== LOAD ==============

def load_game(game: Game, games_db: dict) -> None:
    """Load a game into the database."""
    games_db[game.id] = game.model_dump()


def load_price(price: GamePrice, prices_db: list) -> None:
    """Load a price into the database."""
    # Remove old price for same game+store combo
    prices_db[:] = [
        p for p in prices_db 
        if not (p["game_id"] == price.game_id and p["store"] == price.store)
    ]
    prices_db.append(price.model_dump())


# ============== PIPELINE ==============

async def run_etl_pipeline(search: Optional[str] = None, rawg_api_key: Optional[str] = None) -> dict:
    """
    Run the full ETL pipeline.
    
    Returns summary of extracted data.
    """
    from database import games_db, prices_db
    
    games_added = 0
    prices_added = 0
    
    # Extract and process CheapShark deals
    try:
        cheapshark_deals = await extract_from_cheapshark(search)
        for deal in cheapshark_deals:
            game, price = transform_cheapshark_deal(deal)
            load_game(game, games_db)
            load_price(price, prices_db)
            games_added += 1
            prices_added += 1
    except Exception as e:
        print(f"CheapShark ETL error: {e}")
    
    # Extract and process RAWG games (if API key provided)
    if rawg_api_key:
        try:
            rawg_games = await extract_from_rawg(search, rawg_api_key)
            for raw_game in rawg_games:
                game = transform_rawg_game(raw_game)
                load_game(game, games_db)
                games_added += 1
        except Exception as e:
            print(f"RAWG ETL error: {e}")
    
    return {
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "games_processed": games_added,
        "prices_processed": prices_added,
    }



