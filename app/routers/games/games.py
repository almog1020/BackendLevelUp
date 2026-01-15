from typing import Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
import httpx
from app.logic.etl import run_etl_pipeline
from app.dependencies import get_current_user
from app.models.games import GameResponse

router = APIRouter(prefix="/games", tags=["Games"])

# RAWG API Key
RAWG_API_KEY = "1aae403692eb4b459afc2cb34f6d4eaf"


# ============== EXTRACT FUNCTIONS ==============

async def fetch_cheapshark_deals(sort_by: Optional[str] = None, page_size: int = 60) -> list[dict]:
    """Fetch deals from CheapShark API."""
    async with httpx.AsyncClient() as client:
        url = "https://www.cheapshark.com/api/1.0/deals"
        params = {"pageSize": page_size}
        if sort_by:
            params["sortBy"] = sort_by
        # Reduced timeout to fail faster if API is slow
        response = await client.get(url, params=params, timeout=5.0)
        response.raise_for_status()
        return response.json()


async def fetch_cheapshark_games_search(query: str) -> list[dict]:
    """Search games from CheapShark API."""
    async with httpx.AsyncClient() as client:
        url = "https://www.cheapshark.com/api/1.0/games"
        params = {"title": query}
        response = await client.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        return response.json()


async def fetch_cheapshark_game_lookup(game_id: str) -> Optional[dict]:
    """Lookup game info from CheapShark API by gameID using lookup endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            # Use the lookup endpoint - format: /games?id={gameID}
            # According to CheapShark docs, this should return game info
            url = f"https://www.cheapshark.com/api/1.0/games"
            params = {"id": game_id}
            response = await client.get(url, params=params, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            # The lookup endpoint returns a dict with gameID as key
            if isinstance(data, dict):
                # Check if gameID is in the response
                if game_id in data:
                    return data[game_id]
                # Sometimes the response has the game data directly
                if "gameID" in data and str(data.get("gameID")) == game_id:
                    return data
            return None
    except Exception as e:
        print(f"Lookup error for game {game_id}: {e}")
        return None


async def fetch_rawg_game_info(title: str) -> Optional[dict]:
    """Fetch game info from RAWG API for description and genres."""
    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.rawg.io/api/games"
            params = {"key": RAWG_API_KEY, "search": title, "page_size": 1}
            # Shorter timeout for RAWG calls
            response = await client.get(url, params=params, timeout=3.0)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if results:
                return results[0]
    except Exception:
        pass
    return None


# ============== TRANSFORM FUNCTIONS ==============

def get_store_name(store_id: str) -> str:
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
    return stores.get(str(store_id), f"Store {store_id}")


async def transform_deal_to_game_response(deal: dict, is_trending: bool = False, is_deal_of_day: bool = False, fetch_rawg: bool = False) -> GameResponse:
    """Transform CheapShark deal to GameResponse format."""
    game_id = f"cs_{deal.get('gameID', '')}"
    title = deal.get("title", "Unknown")
    thumb = deal.get("thumb", "")
    
    # Get prices
    sale_price = float(deal.get("salePrice", 0))
    normal_price = float(deal.get("normalPrice", sale_price))
    
    # Calculate discount
    savings_str = deal.get("savings", "0")
    try:
        discount = float(savings_str)
    except (ValueError, TypeError):
        discount = ((normal_price - sale_price) / normal_price * 100) if normal_price > 0 else 0
    
    # Only fetch RAWG info if explicitly requested (for deal of the day)
    description = f"Experience {title} - Available now at great prices!"
    genres = ["Action"]  # Default genre
    
    if fetch_rawg:
        rawg_info = await fetch_rawg_game_info(title)
        if rawg_info:
            description = rawg_info.get("description_raw", "") or rawg_info.get("description", "")
            if description:
                description = description[:500]  # Limit description length
            genres_list = rawg_info.get("genres", [])
            genres = [g.get("name", "") for g in genres_list if g.get("name")] or ["Action"]
    
    return GameResponse(
        id=game_id,
        title=title,
        description=description,
        image=thumb,
        originalPrice=normal_price,
        currentPrice=sale_price,
        discount=round(discount, 1),
        genres=genres,
        isTrending=is_trending,
        isDealOfDay=is_deal_of_day,
    )


async def transform_game_search_to_response(game: dict) -> GameResponse:
    """Transform CheapShark game search result to GameResponse format."""
    game_id = f"cs_{game.get('gameID', '')}"
    title = game.get("external", "Unknown")
    thumb = game.get("thumb", "")
    cheapest = float(game.get("cheapest", 0))
    
    # For search results, we don't have normalPrice, so estimate discount
    # Assume 20% discount as placeholder (could fetch deal details for accuracy)
    estimated_original = cheapest / 0.8 if cheapest > 0 else 0
    discount = 20.0  # Placeholder
    
    # Skip RAWG calls for search results to speed up response
    description = f"Experience {title} - Available now at great prices!"
    genres = ["Action"]
    
    return GameResponse(
        id=game_id,
        title=title,
        description=description,
        image=thumb,
        originalPrice=estimated_original,
        currentPrice=cheapest,
        discount=discount,
        genres=genres,
        isTrending=False,
        isDealOfDay=False,
    )


# ============== ENDPOINTS ==============

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Games API is working"}


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
            game = await transform_deal_to_game_response(deal)
            games.append(game)
        return games
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch games: {str(e)}")


@router.get("/trending", response_model=list[GameResponse], status_code=status.HTTP_200_OK)
async def get_trending_games():
    """Fetch trending games (sorted by deal rating)."""
    try:
        # Reduce page size to speed up response
        deals = await fetch_cheapshark_deals(sort_by="Deal Rating", page_size=10)
        games = []
        # Skip RAWG calls for trending games to speed up response
        for deal in deals:
            game = await transform_deal_to_game_response(deal, is_trending=True, fetch_rawg=False)
            games.append(game)
        return games
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trending games: {str(e)}")


@router.get("/deal-of-the-day", response_model=GameResponse, status_code=status.HTTP_200_OK)
async def get_deal_of_the_day():
    """Fetch the deal of the day (highest discount)."""
    try:
        deals = await fetch_cheapshark_deals(sort_by="Savings", page_size=1)
        if not deals:
            raise HTTPException(status_code=404, detail="No deals found")
        
        deal = deals[0]
        # Fetch RAWG info only for deal of the day (single game, so it's fast)
        game = await transform_deal_to_game_response(deal, is_deal_of_day=True, fetch_rawg=True)
        return game
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch deal of the day: {str(e)}")


@router.get("/search", response_model=list[GameResponse], status_code=status.HTTP_200_OK)
async def search_games(q: str = Query(..., description="Search query")):
    """Search games by query term."""
    if not q or not q.strip():
        return []
    
    try:
        games_data = await fetch_cheapshark_games_search(q.strip())
        games = []
        for game_data in games_data[:20]:  # Limit to 20 results
            game = await transform_game_search_to_response(game_data)
            games.append(game)
        return games
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search games: {str(e)}")


@router.get("/{game_id}", response_model=GameResponse, status_code=status.HTTP_200_OK)
async def get_game_by_id(game_id: str):
    """Fetch a single game by ID."""
    try:
        # Extract CheapShark gameID from our ID format (cs_123 -> 123)
        if game_id.startswith("cs_"):
            cheapshark_game_id = game_id.replace("cs_", "")
            
            # First, try to find in current deals
            deals = await fetch_cheapshark_deals(page_size=100)
            matching_deal = None
            for deal in deals:
                if str(deal.get("gameID", "")) == cheapshark_game_id:
                    matching_deal = deal
                    break
            
            # If not found in deals, try to get game info from lookup endpoint
            if not matching_deal:
                game_lookup = await fetch_cheapshark_game_lookup(cheapshark_game_id)
                if game_lookup:
                    # Create a deal-like structure from game lookup
                    # The lookup returns game info with cheapest price
                    cheapest = float(game_lookup.get("cheapest", 0))
                    estimated_original = cheapest / 0.8 if cheapest > 0 else 0
                    matching_deal = {
                        "gameID": cheapshark_game_id,
                        "title": game_lookup.get("external", "Unknown"),
                        "thumb": game_lookup.get("thumb", ""),
                        "salePrice": cheapest,
                        "normalPrice": estimated_original,
                        "savings": "20.0",  # Estimate
                        "dealID": game_lookup.get("cheapestDealID", ""),
                    }
                else:
                    # Last resort: try searching through more deals (up to 200)
                    # Also try fetching without sort to get different results
                    more_deals = await fetch_cheapshark_deals(page_size=200)
                    for deal in more_deals:
                        if str(deal.get("gameID", "")) == cheapshark_game_id:
                            matching_deal = deal
                            break
                    
                    if not matching_deal:
                        # Try one more time with a different approach - search all deals
                        # by fetching multiple pages
                        for page in range(0, 3):  # Try first 3 pages
                            try:
                                page_deals = await fetch_cheapshark_deals(page_size=60)
                                for deal in page_deals:
                                    if str(deal.get("gameID", "")) == cheapshark_game_id:
                                        matching_deal = deal
                                        break
                                if matching_deal:
                                    break
                            except:
                                continue
                    
                    if not matching_deal:
                        raise HTTPException(status_code=404, detail=f"Game with ID {game_id} not found. The game may no longer be available in current deals.")
            
            # Fetch RAWG info for detailed game page (with full description and genres)
            game = await transform_deal_to_game_response(matching_deal, fetch_rawg=True)
            return game
        else:
            raise HTTPException(status_code=404, detail=f"Invalid game ID format: {game_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch game: {str(e)}")


