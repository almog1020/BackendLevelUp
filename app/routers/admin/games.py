from typing import Optional, Dict, Any
from fastapi import APIRouter, status, Query, HTTPException

from app.logic.etl import get_igdb_games_500, IGDB_LIMIT, run_etl_pipeline, UpstreamDataError

router = APIRouter(prefix="/games", tags=["Games"])

# Final endpoint URL: GET /games/?limit=500


@router.get("/", status_code=status.HTTP_200_OK)
async def get_all_games(
    limit: int = Query(default=500, ge=1, le=500, description="Maximum number of games to return (1-500)")
) -> Dict[str, Any]:
    """
    Get games from IGDB API with full details.
    
    IMPORTANT: This endpoint returns IGDB games ONLY, NOT CheapShark deals.
    For CheapShark deals, use POST /games/etl or other CheapShark endpoints.
    
    Fetches games from IGDB with fields: name, rating, release_date, genres (names), image_url.
    Uses existing OAuth token caching and genres catalog mapping.
    
    Args:
        limit: Maximum number of games to return (default 500, max 500)
        
    Returns:
        Dictionary with:
        - count: int - Number of games returned
        - games: list[dict] - Game dictionaries with:
            - name: str
            - rating: float | None
            - release_date: str | None (ISO format YYYY-MM-DD)
            - genres: list[str]
            - image_url: str | None (normalized cover URL from IGDB)
            
    On IGDB failure, returns {"count": 0, "games": []} and logs warning.
    """
    # Clamp limit to valid range using IGDB_LIMIT
    limit = max(1, min(limit, IGDB_LIMIT))
    
    # Call IGDB-only function (no CheapShark logic)
    return await get_igdb_games_500(limit=limit)


@router.post("/etl", status_code=status.HTTP_200_OK)
async def trigger_etl(
    search: Optional[str] = Query(None, description="Search term to filter games"),
):
    """
    Trigger ETL pipeline to fetch game data from external APIs.
    DEV mode: Authentication temporarily disabled for testing.
    """
    try:
        result = await run_etl_pipeline(search=search)
        return result
    except UpstreamDataError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream CheapShark API error: {str(e)}"
        )
