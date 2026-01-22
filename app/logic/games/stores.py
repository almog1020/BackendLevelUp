"""Store management logic for CheapShark API."""
import httpx
import logging

logger = logging.getLogger(__name__)

# Cache for store names (store_id -> store_name)
_store_cache: dict[str, str] = {}
_store_cache_fetched: bool = False


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
            
            if not isinstance(stores_data, list):
                logger.warning(f"Expected list but got {type(stores_data)}")
                stores_data = []
            
            # Build mapping: storeID -> storeName
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
            
            if _store_cache:
                _store_cache_fetched = True
                logger.info(f"Successfully fetched {len(_store_cache)} stores from CheapShark")
                return _store_cache
            else:
                logger.warning("No stores were parsed from CheapShark API response")
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching stores from CheapShark: {e}")
    except Exception as e:
        logger.error(f"Error fetching stores from CheapShark: {type(e).__name__}: {e}")
    
    # Fallback mapping if API fails or returns no data
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
    logger.info(f"Using fallback stores: {len(_store_cache)} stores available")
    return _store_cache


