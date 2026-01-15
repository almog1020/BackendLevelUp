from typing import Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
import httpx
import asyncio
import re
from app.logic.etl import run_etl_pipeline
from app.dependencies import get_current_user
from app.models.games import GameResponse

router = APIRouter(prefix="/games", tags=["Games"])

# RAWG API Key
RAWG_API_KEY = "1aae403692eb4b459afc2cb34f6d4eaf"

# Cache for store names (store_id -> store_name)
_store_cache: dict[str, str] = {}
_store_cache_fetched: bool = False


# ============== EXTRACT FUNCTIONS ==============

async def fetch_cheapshark_stores(force_refresh: bool = False) -> dict[str, str]:
    """Fetch store names from CheapShark API and cache them."""
    global _store_cache, _store_cache_fetched
    
    # Return cached data if available and not forcing refresh
    if _store_cache and not force_refresh and _store_cache_fetched:
        return _store_cache
    
    # Clear cache if forcing refresh
    if force_refresh:
        _store_cache.clear()
        _store_cache_fetched = False
    
    try:
        async with httpx.AsyncClient() as client:
            url = "https://www.cheapshark.com/api/1.0/stores"
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            stores_data = response.json()
            
            # Debug: log what we received
            if not isinstance(stores_data, list):
                print(f"Warning: Expected list but got {type(stores_data)}")
                stores_data = []
            
            # Build mapping: storeID -> storeName
            # Handle both string and integer store IDs
            for store in stores_data:
                if not isinstance(store, dict):
                    continue
                    
                # Try different possible field names
                store_id_raw = store.get("storeID") or store.get("store_id") or store.get("id")
                store_name = store.get("storeName") or store.get("store_name") or store.get("name") or ""
                
                # Convert store ID to string, handling both int and str
                if store_id_raw is not None:
                    store_id = str(store_id_raw)
                    if store_id and store_name:
                        _store_cache[store_id] = store_name
            
            # If we got stores, return them
            if _store_cache:
                _store_cache_fetched = True
                print(f"Successfully fetched {len(_store_cache)} stores from CheapShark")
                # Debug: print first few stores
                sample_stores = list(_store_cache.items())[:5]
                print(f"Sample stores: {sample_stores}")
                return _store_cache
            else:
                print("Warning: No stores were parsed from CheapShark API response")
            
    except httpx.HTTPError as e:
        print(f"HTTP error fetching stores from CheapShark: {e}")
    except Exception as e:
        print(f"Error fetching stores from CheapShark: {type(e).__name__}: {e}")
    
    # Fallback mapping if API fails or returns no data
    # Also store it in cache so we don't keep trying
    fallback_stores = {
        "1": "Steam",
        "2": "GamersGate",
        "3": "GreenManGaming",
        "7": "GOG",
        "8": "Origin",
        "11": "Humble Store",
        "13": "Uplay",
        "25": "Epic Games",
    }
    _store_cache.update(fallback_stores)
    print(f"Using fallback stores: {len(_store_cache)} stores available")
    return _store_cache

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


async def fetch_price_comparison(game_id: str) -> list[dict]:
    """Fetch all deals for a game from different stores to compare prices."""
    try:
        # Fetch store names first (will use cache if already fetched)
        stores_map = await fetch_cheapshark_stores()
        
        # Fetch a large number of deals to find all stores selling this game
        async with httpx.AsyncClient() as client:
            url = "https://www.cheapshark.com/api/1.0/deals"
            # Fetch more deals to increase chances of finding all stores
            params = {"pageSize": 200}
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            all_deals = response.json()
            
            # Filter deals for this specific game
            game_deals = [
                deal for deal in all_deals 
                if str(deal.get("gameID", "")) == game_id
            ]
            
            # Extract unique store prices (keep the best price per store)
            store_prices = {}
            for deal in game_deals:
                store_id_raw = deal.get("storeID")
                sale_price = float(deal.get("salePrice", 0))
                deal_id = deal.get("dealID", "")
                
                # Only include deals with valid prices
                if sale_price > 0 and store_id_raw is not None:
                    # Convert store ID to string (handle both int and str)
                    store_id = str(store_id_raw)
                    
                    # Get store name from the fetched stores map
                    store_name = stores_map.get(store_id, f"Store {store_id}")
                    
                    # Debug: log if we're still getting "Store X" names
                    if store_name.startswith("Store "):
                        print(f"Warning: Store ID {store_id} not found in stores map. Available stores: {list(stores_map.keys())[:10]}...")
                    
                    # Create deal URL using CheapShark redirect
                    deal_url = None
                    if deal_id:
                        deal_url = f"https://www.cheapshark.com/redirect?dealID={deal_id}"
                    
                    # Keep the lowest price if multiple deals from same store
                    if store_name not in store_prices or sale_price < store_prices[store_name]["price"]:
                        store_prices[store_name] = {
                            "store": store_name,
                            "price": sale_price,
                            "url": deal_url
                        }
            
            # Convert to list and sort by price
            price_comparison = sorted(
                list(store_prices.values()),
                key=lambda x: x["price"]
            )
            
            return price_comparison
    except Exception as e:
        print(f"Error fetching price comparison for game {game_id}: {e}")
        return []


async def fetch_rawg_game_info(title: str) -> Optional[dict]:
    """Fetch game info from RAWG API for description and genres."""
    try:
        async with httpx.AsyncClient() as client:
            search_url = "https://api.rawg.io/api/games"
            search_params = {"key": RAWG_API_KEY, "search": title, "page_size": 1}
            search_response = await client.get(search_url, params=search_params, timeout=2.0)
            search_response.raise_for_status()
            search_data = search_response.json()
            results = search_data.get("results", [])
            
            if not results:
                return None
            
            game_data = results[0]
            game_id = game_data.get("id")
            
            if game_id:
                try:
                    detail_url = f"https://api.rawg.io/api/games/{game_id}"
                    detail_params = {"key": RAWG_API_KEY}
                    detail_response = await client.get(detail_url, params=detail_params, timeout=2.0)
                    detail_response.raise_for_status()
                    full_game_data = detail_response.json()
                    return full_game_data
                except Exception:
                    return game_data
            
            return game_data
    except Exception:
        pass
    return None


async def fetch_rawg_image_only(title: str) -> Optional[str]:
    """Fetch only the image URL from RAWG API with timeout."""
    try:
        rawg_info = await asyncio.wait_for(fetch_rawg_game_info(title), timeout=2.0)
        if rawg_info:
            return rawg_info.get("background_image")
    except (asyncio.TimeoutError, Exception):
        pass
    return None


async def fetch_rawg_images_parallel(titles: list[str], max_concurrent: int = 5) -> dict[str, Optional[str]]:
    """Fetch RAWG images in parallel with concurrency limit."""
    results = {}
    
    # Process in batches to limit concurrent requests
    for i in range(0, len(titles), max_concurrent):
        batch = titles[i:i + max_concurrent]
        tasks = [fetch_rawg_image_only(title) for title in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for title, result in zip(batch, batch_results):
            if isinstance(result, Exception) or result is None:
                results[title] = None
            else:
                results[title] = result
    
    return results


# ============== TRANSFORM FUNCTIONS ==============

async def get_store_name(store_id: str) -> str:
    """Map CheapShark store IDs to names using dynamically fetched store list."""
    stores_map = await fetch_cheapshark_stores()
    return stores_map.get(str(store_id), f"Store {store_id}")


async def transform_deal_to_game_response(deal: dict, is_trending: bool = False, is_deal_of_day: bool = False, fetch_rawg: bool = False, fetch_rawg_image: bool = False, price_comparison: Optional[list[dict]] = None) -> GameResponse:
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
    
    # Initialize defaults
    description = f"Experience {title} - Available now at great prices!"
    genres = ["Action"]  # Default genre
    image = thumb  # Default to CheapShark thumbnail
    
    # Fetch RAWG info if requested (for full metadata or just images)
    if fetch_rawg or fetch_rawg_image:
        rawg_info = await fetch_rawg_game_info(title)
        if rawg_info:
            # Use RAWG background_image if available (higher quality than thumb)
            rawg_image = rawg_info.get("background_image")
            if rawg_image:
                image = rawg_image
            
            if fetch_rawg:
                rawg_description = (
                    rawg_info.get("description_raw") or 
                    rawg_info.get("description") or
                    rawg_info.get("summary") or
                    rawg_info.get("about") or
                    rawg_info.get("overview")
                )
                
                if rawg_description and rawg_description.strip():
                    clean_description = re.sub(r'<[^>]+>', '', str(rawg_description))
                    clean_description = clean_description.replace('&nbsp;', ' ').replace('&amp;', '&')
                    clean_description = clean_description.replace('&lt;', '<').replace('&gt;', '>')
                    clean_description = clean_description.replace('&quot;', '"').replace('&#39;', "'")
                    
                    if clean_description.strip():
                        description = clean_description[:1000]
                
                genres_list = rawg_info.get("genres", [])
                genres = [g.get("name", "") for g in genres_list if g.get("name")] or ["Action"]
    
    # Convert price comparison dicts to PriceComparison objects if provided
    price_comparison_list = None
    if price_comparison:
        from app.models.games import PriceComparison
        price_comparison_list = [PriceComparison(**pc) for pc in price_comparison]
    
    return GameResponse(
        id=game_id,
        title=title,
        description=description,
        image=image,
        originalPrice=normal_price,
        currentPrice=sale_price,
        discount=round(discount, 1),
        genres=genres,
        isTrending=is_trending,
        isDealOfDay=is_deal_of_day,
        priceComparison=price_comparison_list,
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
    
    # Default values
    description = f"Experience {title} - Available now at great prices!"
    genres = ["Action"]
    image = thumb  # Default to CheapShark thumbnail
    
    # Fetch RAWG info for higher quality images
    rawg_info = await fetch_rawg_game_info(title)
    if rawg_info:
        # Use RAWG background_image if available (higher quality than thumb)
        rawg_image = rawg_info.get("background_image")
        if rawg_image:
            image = rawg_image
    
    return GameResponse(
        id=game_id,
        title=title,
        description=description,
        image=image,
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


@router.get("/debug/stores", status_code=status.HTTP_200_OK)
async def debug_stores(force_refresh: bool = Query(False, description="Force refresh stores cache")):
    """Debug endpoint to check store mappings."""
    global _store_cache
    stores_map = await fetch_cheapshark_stores(force_refresh=force_refresh)
    return {
        "cached_stores_count": len(_store_cache),
        "stores": stores_map,
        "sample": dict(list(stores_map.items())[:10]) if stores_map else {},
        "all_store_ids": list(stores_map.keys())[:20]  # First 20 store IDs for debugging
    }


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
        # Skip RAWG images for bulk endpoint to avoid timeout - use CheapShark thumbnails
        for deal in deals:
            game = await transform_deal_to_game_response(deal, fetch_rawg=False, fetch_rawg_image=False)
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
        
        # Return games immediately with CheapShark thumbnails (no RAWG delay)
        games = []
        for deal in deals:
            title = deal.get("title", "")
            game_id = f"cs_{deal.get('gameID', '')}"
            thumb = deal.get("thumb", "")
            
            sale_price = float(deal.get("salePrice", 0))
            normal_price = float(deal.get("normalPrice", sale_price))
            savings_str = deal.get("savings", "0")
            try:
                discount = float(savings_str)
            except (ValueError, TypeError):
                discount = ((normal_price - sale_price) / normal_price * 100) if normal_price > 0 else 0
            
            game = GameResponse(
                id=game_id,
                title=title,
                description=f"Experience {title} - Available now at great prices!",
                image=thumb,  # Use CheapShark thumb immediately
                originalPrice=normal_price,
                currentPrice=sale_price,
                discount=round(discount, 1),
                genres=["Action"],
                isTrending=True,
                isDealOfDay=False,
            )
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
        games_data = games_data[:20]  # Limit to 20 results
        
        # Return games immediately with CheapShark thumbnails (no RAWG delay)
        games = []
        for game_data in games_data:
            game_id = f"cs_{game_data.get('gameID', '')}"
            title = game_data.get("external", "Unknown")
            thumb = game_data.get("thumb", "")
            cheapest = float(game_data.get("cheapest", 0))
            
            estimated_original = cheapest / 0.8 if cheapest > 0 else 0
            discount = 20.0  # Placeholder
            
            game = GameResponse(
                id=game_id,
                title=title,
                description=f"Experience {title} - Available now at great prices!",
                image=thumb,  # Use CheapShark thumb immediately
                originalPrice=estimated_original,
                currentPrice=cheapest,
                discount=discount,
                genres=["Action"],
                isTrending=False,
                isDealOfDay=False,
            )
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
            
            # Fetch price comparison data from different stores
            price_comparison = await fetch_price_comparison(cheapshark_game_id)
            
            # Fetch RAWG info for detailed game page (with full description and genres)
            game = await transform_deal_to_game_response(matching_deal, fetch_rawg=True, price_comparison=price_comparison)
            return game
        else:
            raise HTTPException(status_code=404, detail=f"Invalid game ID format: {game_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch game: {str(e)}")


