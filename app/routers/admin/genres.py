from fastapi import APIRouter
from typing import Dict, Any

from app.logic.etl import get_admin_genre_stats

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/genres")
async def admin_genres() -> Dict[str, Any]:
    """
    Get genre statistics from IGDB games.
    
    Fetches exactly 500 IGDB games and returns genre counts for chart usage.
    Uses minimal API calls:
    - 1 call to fetch genres catalog
    - 1 call to fetch games (genres field only)
    - OAuth token call only if cached token expired
    
    Returns only count and genre_stats, no games list or images.
    No authentication required at this stage.
    """
    return await get_admin_genre_stats()

