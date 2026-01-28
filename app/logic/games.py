from typing import Optional

import httpx
import asyncio
import re
import os
import logging
from app.models.games import GameResponse
from app.logic.stores import fetch_cheapshark_stores


def select_all_games_from_dict(games_db: dict) -> list[dict]:
    """
    Get all games from the in-memory dictionary.
    Returns a list of game dicts sorted by title (case-insensitive).
    If title is missing, treats it as empty string.
    """
    games = list(games_db.values())

    # Sort by title (case-insensitive), treating missing titles as empty string
    def get_sort_key(game: dict) -> str:
        title = game.get("title", "")
        if title is None:
            title = ""
        return title.lower()

    return sorted(games, key=get_sort_key)


def get_game_by_id_from_dict(games_db: dict, game_id: str) -> Optional[dict]:
    """
    Get a single game by ID from the in-memory dictionary.
    Returns the game dict if found, None otherwise.
    """
    return games_db.get(game_id)

logger = logging.getLogger(__name__)

RAWG_API_KEY = os.getenv("RAWG_API_KEY", "")
if not RAWG_API_KEY:
    logger.warning("RAWG_API_KEY environment variable not set. RAWG API features will be disabled.")


# ============== EXTRACT FUNCTIONS ==============

async def fetch_cheapshark_deals(sort_by: Optional[str] = None, page_size: int = 60) -> list[dict]:
    """Fetch deals from CheapShark API."""
    async with httpx.AsyncClient() as client:
        url = "https://www.cheapshark.com/api/1.0/deals"
        params = {"pageSize": page_size}
        if sort_by:
            params["sortBy"] = sort_by
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
            url = "https://www.cheapshark.com/api/1.0/games"
            params = {"id": game_id}
            response = await client.get(url, params=params, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict):
                if game_id in data:
                    return data[game_id]
                
                if "info" in data:
                    info = data.get("info", {})
                    deals = data.get("deals", [])
                    cheapest_price_ever = data.get("cheapestPriceEver", {})
                    
                    cheapest_price = 0.0
                    cheapest_deal_id = ""
                    if deals and len(deals) > 0:
                        cheapest_deal = min(deals, key=lambda d: float(d.get("price", "999999")))
                        cheapest_price = float(cheapest_deal.get("price", 0))
                        cheapest_deal_id = cheapest_deal.get("dealID", "")
                    elif cheapest_price_ever:
                        cheapest_price = float(cheapest_price_ever.get("price", 0))
                    
                    return {
                        "gameID": game_id,
                        "external": info.get("title", "Unknown"),
                        "thumb": info.get("thumb", ""),
                        "cheapest": cheapest_price,
                        "cheapestDealID": cheapest_deal_id,
                    }
                
                if "gameID" in data and str(data.get("gameID")) == game_id:
                    return data
                if "external" in data or "thumb" in data:
                    return data
            elif isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict) and str(item.get("gameID", "")) == game_id:
                        return item
                if isinstance(data[0], dict) and ("external" in data[0] or "thumb" in data[0]):
                    return data[0]
            
            logger.warning(f"Unexpected response format for game lookup {game_id}: {type(data)}")
            return None
    except httpx.HTTPError as e:
        logger.warning(f"HTTP error looking up game {game_id}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Lookup error for game {game_id}: {type(e).__name__}: {e}")
        return None


async def fetch_price_comparison(game_id: str) -> list[dict]:
    """Fetch all deals for a game from different stores to compare prices."""
    try:
        stores_map = await fetch_cheapshark_stores()
        
        async with httpx.AsyncClient() as client:
            url = "https://www.cheapshark.com/api/1.0/deals"
            params = {"pageSize": 200}
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            all_deals = response.json()
            
            game_deals = [
                deal for deal in all_deals 
                if str(deal.get("gameID", "")) == game_id
            ]
            
            store_prices = {}
            for deal in game_deals:
                store_id_raw = deal.get("storeID")
                sale_price = float(deal.get("salePrice", 0))
                deal_id = deal.get("dealID", "")
                
                if sale_price > 0 and store_id_raw is not None:
                    store_id = str(store_id_raw)
                    store_name = stores_map.get(store_id, f"Store {store_id}")
                    
                    if store_name.startswith("Store "):
                        logger.warning(f"Store ID {store_id} not found in stores map. Available stores: {list(stores_map.keys())[:10]}...")
                    
                    deal_url = None
                    if deal_id:
                        deal_url = f"https://www.cheapshark.com/redirect?dealID={deal_id}"
                    
                    if store_name not in store_prices or sale_price < store_prices[store_name]["price"]:
                        store_prices[store_name] = {
                            "store": store_name,
                            "price": sale_price,
                            "url": deal_url
                        }
            
            price_comparison = sorted(
                list(store_prices.values()),
                key=lambda x: x["price"]
            )
            
            return price_comparison
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching price comparison for game {game_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching price comparison for game {game_id}: {e}")
        return []


async def fetch_rawg_game_info(title: str) -> Optional[dict]:
    """Fetch game info from RAWG API for description and genres."""
    if not RAWG_API_KEY:
        return None
    
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
                    return detail_response.json()
                except (httpx.HTTPError, httpx.RequestError) as e:
                    logger.warning(f"Failed to fetch RAWG game details for {title}: {e}")
                    return game_data
            
            return game_data
    except (httpx.HTTPError, httpx.RequestError) as e:
        logger.warning(f"Failed to fetch RAWG game info for {title}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching RAWG game info for {title}: {e}")
    return None


async def fetch_rawg_image_only(title: str) -> Optional[str]:
    """Fetch only the image URL from RAWG API with timeout."""
    try:
        rawg_info = await asyncio.wait_for(fetch_rawg_game_info(title), timeout=2.0)
        if rawg_info:
            return rawg_info.get("background_image")
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching RAWG image for {title}")
    except Exception as e:
        logger.warning(f"Error fetching RAWG image for {title}: {e}")
    return None


# ============== TRANSFORM FUNCTIONS ==============

def calculate_discount(savings_str: str, normal_price: float, sale_price: float) -> float:
    """Calculate discount percentage from savings string or price difference."""
    try:
        return float(savings_str)
    except (ValueError, TypeError):
        return ((normal_price - sale_price) / normal_price * 100) if normal_price > 0 else 0


async def transform_deal_to_game_response(deal: dict, is_trending: bool = False, is_deal_of_day: bool = False, fetch_rawg: bool = False, fetch_rawg_image: bool = False, price_comparison: Optional[list[dict]] = None) -> GameResponse:
    """Transform CheapShark deal to GameResponse format."""
    game_id = f"cs_{deal.get('gameID', '')}"
    title = deal.get("title", "Unknown")
    thumb = deal.get("thumb", "")
    
    sale_price = float(deal.get("salePrice", 0))
    normal_price = float(deal.get("normalPrice", sale_price))
    savings_str = deal.get("savings", "0")
    discount = calculate_discount(savings_str, normal_price, sale_price)
    
    description = f"Experience {title} - Available now at great prices!"
    genres = ["Action"]
    image = thumb
    
    if fetch_rawg or fetch_rawg_image:
        rawg_info = await fetch_rawg_game_info(title)
        if rawg_info:
            rawg_image = rawg_info.get("background_image")
            if rawg_image and (fetch_rawg or fetch_rawg_image):
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

