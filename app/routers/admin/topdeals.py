from typing import Optional, Dict, Any
from fastapi import APIRouter, status, Query, HTTPException

from app.logic.etl import get_top_deals, UpstreamDataError

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/top-deals", status_code=status.HTTP_200_OK)
async def get_top_deals_endpoint(
    search: Optional[str] = Query(None, description="Search term to filter games by title"),
    min_discount: float = Query(60.0, ge=0.0, le=100.0, description="Minimum discount percentage (0-100)"),
    limit: int = Query(30, ge=1, le=200, description="Maximum number of deals to return (1-200)"),
    sort: str = Query("discount", description="Sort order: discount, savings, or price")
) -> Dict[str, Any]:
    """
    Get top deals from CheapShark filtered by minimum discount.
    
    Returns deals with discount percentage >= min_discount, sorted by the specified criteria.
    Each deal includes game info, price info, discount percentage, and price details.
    
    Args:
        search: Optional search term to filter games by title
        min_discount: Minimum discount percentage (0-100, default 60.0)
        limit: Maximum number of deals to return (1-200, default 30)
        sort: Sort order - "discount" (highest discount), "savings" (highest savings), or "price" (lowest price)
        
    Returns:
        Dictionary with:
        - deals: List[dict] - Each deal contains:
            - game: Game dict with id, title, image_url
            - price: GamePrice dict with game_id, store, price, currency, url
            - discount_percent: float
            - normal_price: float | None
            - sale_price: float | None
    """
    try:
        result = await get_top_deals(search=search, min_discount=min_discount, limit=limit, sort=sort)
        return result
    except UpstreamDataError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream CheapShark API error: {str(e)}"
        )

