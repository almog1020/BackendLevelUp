"""
ETL Pipeline for extracting and transforming game data from external APIs.

Extract: Pull raw data from external game store APIs
Transform: Normalize and clean data into standard format
Note: No Load step - data is returned directly without storage
"""

import httpx
import os
import logging
from typing import Optional
from datetime import datetime, timedelta, timezone

from app.models.games import Game, GamePrice

# IGDB API configuration (Twitch OAuth)
IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID", "vv2p0vpmisdo9u5o34uhjchyd5ndjr")
IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET", "mkqxpoaja50arre65d0asfzl35dcu1")
IGDB_OAUTH_URL = "https://id.twitch.tv/oauth2/token"
IGDB_GAMES_URL = "https://api.igdb.com/v4/games"
IGDB_GENRES_URL = "https://api.igdb.com/v4/genres"
IGDB_TIMEOUT = 5.0

# IGDB endpoint constants
IGDB_LIMIT = 500


# CheapShark API configuration
CHEAPSHARK_BASE_URL = "https://www.cheapshark.com/api/1.0"
CHEAPSHARK_TIMEOUT = 10.0
RAWG_TIMEOUT = 5.0  # Shorter timeout for RAWG enrichment calls

# Logger for IGDB operations
logger = logging.getLogger(__name__)

# IGDB OAuth token cache (in-memory)
_igdb_token: Optional[str] = None
_igdb_token_expires_at: Optional[datetime] = None


# ============== EXCEPTIONS ==============

class UpstreamDataError(Exception):
    """Raised when upstream API (CheapShark) fails to provide data."""
    pass


# ============== EXTRACT ==============

async def extract_from_cheapshark(search: Optional[str] = None, page_size: int = 20) -> list[dict]:
    """
    Extract game deals from CheapShark API (free, no API key needed).
    https://apidocs.cheapshark.com/
    
    Raises:
        UpstreamDataError: If API request fails, times out, or returns non-200 status
    """
    try:
        async with httpx.AsyncClient(timeout=CHEAPSHARK_TIMEOUT) as client:
            url = f"{CHEAPSHARK_BASE_URL}/deals"
            params = {"pageSize": page_size}
            if search:
                params["title"] = search
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise UpstreamDataError("Upstream CheapShark API timeout")
    except httpx.HTTPStatusError as e:
        raise UpstreamDataError(f"Upstream CheapShark API error: {e.response.status_code}")
    except Exception as e:
        raise UpstreamDataError(f"Upstream CheapShark API error: {str(e)}")


async def get_igdb_access_token() -> str:
    """
    Get IGDB access token using Twitch OAuth client_credentials flow.
    Uses in-memory cache to avoid requesting new token on every call.
    
    Returns:
        Access token string, or empty string if authentication fails
    """
    global _igdb_token, _igdb_token_expires_at
    
    # Check if we have a valid cached token (with 60 second buffer)
    if _igdb_token and _igdb_token_expires_at:
        if datetime.utcnow() < (_igdb_token_expires_at - timedelta(seconds=60)):
            return _igdb_token
    
    # Validate credentials (only check if empty/None, not against default values)
    if not IGDB_CLIENT_ID:
        logger.warning("IGDB_CLIENT_ID not configured")
        return ""
    if not IGDB_CLIENT_SECRET:
        logger.warning("IGDB_CLIENT_SECRET not configured")
        return ""
    
    try:
        async with httpx.AsyncClient(timeout=IGDB_TIMEOUT) as client:
            response = await client.post(
                IGDB_OAUTH_URL,
                params={
                    "client_id": IGDB_CLIENT_ID,
                    "client_secret": IGDB_CLIENT_SECRET,
                    "grant_type": "client_credentials"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)  # Default 1 hour
            
            if not access_token:
                logger.warning("IGDB OAuth response missing access_token")
                return ""
            
            # Cache token
            _igdb_token = access_token
            _igdb_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return access_token
            
    except httpx.TimeoutException:
        logger.warning("IGDB OAuth: Request timeout")
        return ""
    except httpx.HTTPStatusError as e:
        logger.warning(f"IGDB OAuth: HTTP {e.response.status_code} - {e.response.reason_phrase}")
        return ""
    except Exception as e:
        logger.warning(f"IGDB OAuth error: {type(e).__name__}: {str(e)}")
        return ""


# ============== ADMIN GENRE STATS ENDPOINT FUNCTIONS ==============

async def igdb_fetch_genres_catalog() -> dict[int, str]:
    """
    Fetch IGDB genres catalog in a single API call (no pagination).
    
    Returns:
        Dictionary mapping genre ID (int) to genre name (str).
        Returns empty dict if API call fails or no token available.
    """
    # Get access token
    token = await get_igdb_access_token()
    if not token:
        logger.warning("IGDB: Failed to obtain access token for genres catalog")
        return {}
    
    try:
        # Build IGDB query (single request, limit 500)
        query = "fields id,name; limit 500;"
        
        async with httpx.AsyncClient(timeout=IGDB_TIMEOUT) as client:
            response = await client.post(
                IGDB_GENRES_URL,
                headers={
                    "Client-ID": IGDB_CLIENT_ID,
                    "Authorization": f"Bearer {token}"
                },
                content=query.encode("utf-8")
            )
            response.raise_for_status()
            data = response.json()
            
            # Build catalog from response
            catalog: dict[int, str] = {}
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "id" in item and "name" in item:
                        try:
                            genre_id = int(item["id"])
                            genre_name = str(item["name"])
                            if genre_name:
                                catalog[genre_id] = genre_name
                        except (ValueError, TypeError):
                            continue
            
            return catalog
            
    except (httpx.TimeoutException, httpx.HTTPStatusError, Exception) as e:
        logger.warning(f"IGDB genres catalog fetch error: {type(e).__name__}")
        return {}


async def igdb_fetch_games_genre_ids() -> list[list[int]]:
    """
    Fetch IGDB games with only genres field in a single API call.
    Always fetches exactly IGDB_LIMIT (500) games.
    
    Returns:
        List of genre ID lists, one per game.
        Example: [[4, 12], [], [31], ...]
        Returns empty list if API call fails or no token available.
    """
    # Get access token
    token = await get_igdb_access_token()
    if not token:
        logger.warning("IGDB: Failed to obtain access token for games genre IDs fetch")
        return []
    
    try:
        # Build IGDB query (single request, only genres field, always 500)
        query = f"fields genres; sort id asc; limit {IGDB_LIMIT};"
        
        async with httpx.AsyncClient(timeout=IGDB_TIMEOUT) as client:
            response = await client.post(
                IGDB_GAMES_URL,
                headers={
                    "Client-ID": IGDB_CLIENT_ID,
                    "Authorization": f"Bearer {token}"
                },
                content=query.encode("utf-8")
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract genre IDs for each game
            genre_id_lists: list[list[int]] = []
            if isinstance(data, list):
                for game in data:
                    genres = game.get("genres", [])
                    
                    # Ensure genres is a list and filter only integers
                    if not genres:
                        genre_id_lists.append([])
                    else:
                        genre_ids = []
                        for g in genres:
                            if isinstance(g, int):
                                genre_ids.append(g)
                            elif isinstance(g, (str, float)):
                                try:
                                    genre_ids.append(int(g))
                                except (ValueError, TypeError):
                                    continue
                        genre_id_lists.append(genre_ids)
            
            return genre_id_lists
            
    except (httpx.TimeoutException, httpx.HTTPStatusError, Exception) as e:
        logger.warning(f"IGDB games genre IDs fetch error: {type(e).__name__}")
        return []


def build_genre_stats(genre_id_lists: list[list[int]], catalog: dict[int, str]) -> dict[str, int]:
    """
    Build genre statistics by counting genre occurrences across games.
    
    Args:
        genre_id_lists: List of genre ID lists, one per game
        catalog: Dictionary mapping genre ID (int) to genre name (str)
        
    Returns:
        Dictionary mapping genre names to counts.
        Games with no genres or unknown genre IDs are counted as "Unknown".
    """
    genre_counts: dict[str, int] = {}
    
    for genre_ids in genre_id_lists:
        # If game has no genres, count as "Unknown"
        if not genre_ids:
            genre_counts["Unknown"] = genre_counts.get("Unknown", 0) + 1
        else:
            # Count each genre
            has_valid_genre = False
            for genre_id in genre_ids:
                genre_name = catalog.get(genre_id)
                if genre_name:
                    genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 1
                    has_valid_genre = True
            
            # If no valid genres found in catalog, count as "Unknown"
            if not has_valid_genre:
                genre_counts["Unknown"] = genre_counts.get("Unknown", 0) + 1
    
    return genre_counts


async def get_admin_genre_stats() -> dict:
    """
    Fetch IGDB games and build genre statistics.
    Uses only 2 IGDB API calls: one for genres catalog, one for games.
    Always processes exactly IGDB_LIMIT (500) games.
    
    Returns:
        Dictionary with:
        - count: int - Number of games processed
        - genre_stats: dict[str, int] - Genre name to count mapping
        
        Returns {"count": 0, "genre_stats": {}} if IGDB fails.
    """
    try:
        # Fetch genres catalog and games genre IDs (always 500 games)
        catalog = await igdb_fetch_genres_catalog()
        genre_id_lists = await igdb_fetch_games_genre_ids()
        
        # Build genre statistics
        genre_stats = build_genre_stats(genre_id_lists, catalog)
        
        return {
            "count": len(genre_id_lists),
            "genre_stats": genre_stats
        }
        
    except Exception as e:
        logger.warning(f"Admin genre stats error: {type(e).__name__}")
        return {
            "count": 0,
            "genre_stats": {}
        }


# ============== IGDB GAMES ENDPOINT FUNCTIONS ==============

def _ts_to_iso_date(ts: int | None) -> str | None:
    """
    Convert IGDB unix timestamp (seconds) to ISO date string (YYYY-MM-DD) in UTC.
    
    Args:
        ts: Unix timestamp in seconds, or None
        
    Returns:
        ISO date string in format "YYYY-MM-DD", or None if ts is None/invalid
    """
    if ts is None:
        return None
    
    try:
        # Convert unix timestamp to datetime (UTC)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        # Return ISO date string (YYYY-MM-DD)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError, OSError):
        return None


def _normalize_igdb_cover_url(cover_data: dict | None) -> str | None:
    """
    Normalize IGDB cover URL to full HTTPS URL.
    
    IGDB cover.url can be:
    - "//images.igdb.com/igdb/image/..." (protocol-relative)
    - "https://images.igdb.com/igdb/image/..." (full URL)
    - None or missing
    
    Args:
        cover_data: IGDB cover object (dict with "url" key) or None
        
    Returns:
        Full HTTPS URL string or None
    """
    if not cover_data or not isinstance(cover_data, dict):
        return None
    
    url = cover_data.get("url")
    if not url or not isinstance(url, str):
        return None
    
    # If URL starts with "//", prepend "https:"
    if url.startswith("//"):
        return "https:" + url
    
    # If already has protocol, return as-is
    if url.startswith("http://") or url.startswith("https://"):
        return url
    
    # Otherwise, assume HTTPS
    return "https://" + url


async def igdb_fetch_games_full(limit: int = IGDB_LIMIT) -> list[dict]:
    """
    Fetch IGDB games with full details: name, rating, release_date, genres (names), image_url.
    
    Args:
        limit: Maximum number of games to fetch (default IGDB_LIMIT, capped to 500)
        
    Returns:
        List of game dictionaries with keys:
        - name: str
        - rating: float | None
        - release_date: str | None (ISO format YYYY-MM-DD)
        - genres: list[str]
        - image_url: str | None (normalized cover URL)
        
        Returns empty list if API call fails or no token available.
    """
    # Clamp limit to valid range
    limit = max(1, min(limit, IGDB_LIMIT))
    
    # Get access token
    token = await get_igdb_access_token()
    if not token:
        logger.warning("IGDB: Failed to obtain access token for games full fetch")
        return []
    
    # Fetch genres catalog for mapping IDs to names
    catalog = await igdb_fetch_genres_catalog()
    
    try:
        # Build IGDB query - include cover.url for images
        query = f"fields name,rating,first_release_date,genres,cover.url; sort id asc; limit {limit};"
        
        async with httpx.AsyncClient(timeout=IGDB_TIMEOUT) as client:
            response = await client.post(
                IGDB_GAMES_URL,
                headers={
                    "Client-ID": IGDB_CLIENT_ID,
                    "Authorization": f"Bearer {token}"
                },
                content=query.encode("utf-8")
            )
            response.raise_for_status()
            data = response.json()
            
            # Transform games
            games: list[dict] = []
            if isinstance(data, list):
                for game in data:
                    # Extract and convert genres IDs to names
                    genre_ids = game.get("genres", []) or []
                    genre_names: list[str] = []
                    
                    for gid in genre_ids:
                        try:
                            genre_id = int(gid) if isinstance(gid, (int, str)) else None
                            if genre_id and genre_id in catalog:
                                genre_name = catalog[genre_id]
                                if genre_name:
                                    genre_names.append(genre_name)
                        except (ValueError, TypeError):
                            continue
                    
                    # If no genres found, use "Unknown"
                    if not genre_names:
                        genre_names = ["Unknown"]
                    
                    # Extract rating (can be None)
                    rating = game.get("rating")
                    if rating is not None:
                        try:
                            rating = float(rating)
                        except (ValueError, TypeError):
                            rating = None
                    
                    # Extract and convert release date
                    release_date = _ts_to_iso_date(game.get("first_release_date"))
                    
                    # Extract and normalize cover image URL
                    cover_data = game.get("cover")
                    image_url = _normalize_igdb_cover_url(cover_data)
                    
                    games.append({
                        "name": game.get("name") or "Unknown",
                        "rating": rating,
                        "release_date": release_date,
                        "genres": genre_names,
                        "image_url": image_url,
                    })
            
            return games
            
    except httpx.TimeoutException:
        logger.warning("IGDB games full fetch: Request timeout")
        return []
    except httpx.HTTPStatusError as e:
        logger.warning(f"IGDB games full fetch: HTTP {e.response.status_code} - {e.response.reason_phrase}")
        return []
    except Exception as e:
        logger.warning(f"IGDB games full fetch error: {type(e).__name__}: {str(e)}")
        return []


async def get_igdb_games_500(limit: int = IGDB_LIMIT) -> dict:
    """
    Get IGDB games with full details (name, rating, release_date, genres, image_url).
    
    Args:
        limit: Maximum number of games to fetch (default IGDB_LIMIT, capped to 500)
        
    Returns:
        Dictionary with:
        - count: int - Number of games returned
        - games: list[dict] - Game dictionaries with keys:
            - name: str
            - rating: float | None
            - release_date: str | None (ISO format YYYY-MM-DD)
            - genres: list[str]
            - image_url: str | None (normalized cover URL)
        
        Returns {"count": 0, "games": []} if IGDB fails.
    """
    try:
        games = await igdb_fetch_games_full(limit=limit)
        if not games:
            logger.warning("IGDB games 500: No games returned (check token/API status)")
        return {
            "count": len(games),
            "games": games
        }
    except Exception as e:
        logger.warning(f"IGDB games 500 error: {type(e).__name__}: {str(e)}")
        return {
            "count": 0,
            "games": []
        }


# ============== TRANSFORM ==============

def transform_cheapshark_deal(raw_deal: dict, genres: list[str] | None = None) -> tuple[Game, GamePrice]:
    """
    Transform CheapShark deal data into our schema.
    
    Args:
        raw_deal: Raw deal data from CheapShark
        genres: Optional list of genres. If None, genre fields are omitted (None).
                If empty list, sets to ["Unknown"]. If provided, uses as-is.
    
    Note:
        When genres is None, genre and genres fields remain None and will be
        excluded from JSON output via model_dump(exclude_none=True).
    """
 
    
    game = Game(
        id=f"cs_{raw_deal.get('gameID', '')}",
        title=raw_deal.get("title", "Unknown"),
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


def _calc_discount_percent(raw_deal: dict) -> float:
    """
    Calculate discount percentage from CheapShark deal data.
    
    Prefers "savings" field (string percent), falls back to computing from
    normalPrice and salePrice: (1 - sale/normal) * 100
    
    Args:
        raw_deal: Raw deal data from CheapShark
        
    Returns:
        Discount percentage as float, clamped to [0, 100]
    """
<<<<<<< HEAD
    # Try to get savings field (string like "60.00")
    savings = raw_deal.get("savings")
    if savings is not None:
        try:
            discount = float(savings)
            return max(0.0, min(100.0, discount))
        except (ValueError, TypeError):
            pass
=======
    games_db = {}
    prices_db = []
>>>>>>> main
    
    # Fallback: compute from normalPrice and salePrice
    try:
        normal_price = raw_deal.get("normalPrice")
        sale_price = raw_deal.get("salePrice")
        
        if normal_price is not None and sale_price is not None:
            normal = float(normal_price)
            sale = float(sale_price)
            
            if normal > 0:
                discount = (1 - sale / normal) * 100
                return max(0.0, min(100.0, discount))
    except (ValueError, TypeError):
        pass
    
    # If all else fails, return 0
    return 0.0





# ============== PUBLIC API FOR GAMES ENDPOINT ==============

async def get_games(search: Optional[str] = None, page_size: int = 30) -> dict:
    """
    Get games directly from CheapShark API with full transformation pipeline.
    Fetches data at request time - no database or caching.
    
    This function implements a pure Extract-Transform pipeline:
    - Extract: Fetch deals from CheapShark API
    - Transform: Normalize to Game/GamePrice schemas
    - No Load: Returns data directly without storage
    
    Args:
        search: Optional search term to filter games by title
        page_size: Number of deals to return (default 30, max 200 for API calls, but router limits to 200)
    
    Returns:
        Dictionary with:
        - games: List[dict] - Normalized game dictionaries with fields:
            - id: str (e.g., "cs_123")
            - title: str
            - image_url: Optional[str]
        - prices: List[dict] - Price dictionaries with fields:
            - game_id: str
            - store: str
            - price: float
            - currency: str
            - url: Optional[str]
        
    Raises:
        UpstreamDataError: If CheapShark API request fails, times out, or returns non-200 status
    """
    # Extract: Fetch raw deals from CheapShark (limit to requested page_size, max 200)
    max_games = min(page_size, 200)  # Limit CheapShark API calls to 200 max
    raw_deals = await extract_from_cheapshark(search=search, page_size=max_games)
    
    # Transform: Convert to Game and GamePrice objects, then to dicts
    # No genre enrichment in CheapShark flow
    games: list[dict] = []
    prices: list[dict] = []
    
    for deal in raw_deals:
        # Transform deal without genres (genres=None => genre/genres fields remain None)
        game, price = transform_cheapshark_deal(deal, genres=None)
        
        # model_dump(exclude_none=True) automatically omits genre/genres when they are None
        games.append(game.model_dump(exclude_none=True))
        prices.append(price.model_dump())
    
    return {
<<<<<<< HEAD
        "games": games,
        "prices": prices,
=======
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "games_processed": games_added,
        "prices_processed": prices_added,
>>>>>>> main
    }


# ============== TOP DEALS ENDPOINT FUNCTIONS ==============

async def get_top_deals(
    search: Optional[str] = None,
    min_discount: float = 60.0,
    limit: int = 30,
    sort: str = "discount"
) -> dict:
    """
    Get top deals from CheapShark API filtered by minimum discount.
    
    Args:
        search: Optional search term to filter games by title
        min_discount: Minimum discount percentage (0-100, default 60.0)
        limit: Maximum number of deals to return (1-200, default 30)
        sort: Sort order - "discount" | "savings" | "price" (default "discount")
        
    Returns:
        Dictionary with:
        - deals: List[dict] - Each deal contains:
            - game: Game dict (exclude_none=True)
            - price: GamePrice dict
            - discount_percent: float
            - normal_price: float | None
            - sale_price: float | None
        
    Raises:
        UpstreamDataError: If CheapShark API request fails, times out, or returns non-200 status
    """
    # Validate and clamp parameters
    min_discount = max(0.0, min(100.0, min_discount))
    limit = max(1, min(200, limit))
    
    # Validate sort parameter
    valid_sorts = {"discount", "savings", "price"}
    if sort not in valid_sorts:
        sort = "discount"
    
    # Extract: Fetch raw deals from CheapShark (fetch more to filter, max 200)
    max_games = min(limit * 2, 200)  # Fetch more to account for filtering
    raw_deals = await extract_from_cheapshark(search=search, page_size=max_games)
    
    # Transform and filter deals
    deals: list[dict] = []
    
    for raw_deal in raw_deals:
        # Calculate discount percentage
        discount_percent = _calc_discount_percent(raw_deal)
        
        # Filter by minimum discount
        if discount_percent < min_discount:
            continue
        
        # Transform deal
        game, price = transform_cheapshark_deal(raw_deal, genres=None)
        
        # Extract prices (handle missing/invalid gracefully)
        normal_price = None
        sale_price = None
        try:
            normal_price_val = raw_deal.get("normalPrice")
            sale_price_val = raw_deal.get("salePrice")
            if normal_price_val is not None:
                normal_price = float(normal_price_val)
            if sale_price_val is not None:
                sale_price = float(sale_price_val)
        except (ValueError, TypeError):
            pass
        
        deals.append({
            "game": game.model_dump(exclude_none=True),
            "price": price.model_dump(),
            "discount_percent": discount_percent,
            "normal_price": normal_price,
            "sale_price": sale_price,
        })
    
    # Sort deals
    if sort == "discount":
        deals.sort(key=lambda x: x["discount_percent"], reverse=True)
    elif sort == "savings":
        # Sort by absolute savings (normal_price - sale_price)
        deals.sort(key=lambda x: (x["normal_price"] or 0) - (x["sale_price"] or 0), reverse=True)
    elif sort == "price":
        # Sort by sale price (lowest first)
        deals.sort(key=lambda x: x["sale_price"] or float('inf'))
    
    # Limit results
    deals = deals[:limit]
    
    return {
        "deals": deals
    }


# ============== LEGACY ETL PIPELINE (for POST /etl endpoint) ==============

async def run_etl_pipeline(search: Optional[str] = None) -> dict:
    """
    Legacy ETL pipeline function (for POST /etl endpoint).
    Now returns data directly without storing in games_db/prices_db.
    
    Returns summary of processed data.
    """
    try:
        # Use get_games to fetch and transform data (limit to 30 games)
        result = await get_games(search=search, page_size=30)
        
        return {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "games_processed": len(result["games"]),
            "prices_processed": len(result["prices"]),
        }
    except UpstreamDataError as e:
        # Re-raise as-is (router will handle conversion to HTTPException)
        raise
    except Exception as e:
        # Wrap other errors
        raise UpstreamDataError(f"ETL pipeline error: {str(e)}")

