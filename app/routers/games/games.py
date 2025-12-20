from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from app.logic.etl import run_etl_pipeline
from app.logic.users import get_current_user

router = APIRouter(prefix="/games", tags=["Games"])


@router.post("/etl", status_code=status.HTTP_200_OK)
async def trigger_etl(
    search: Optional[str] = Query(None, description="Search term to filter games"),
    rawg_api_key: Optional[str] = Query(None, description="Optional RAWG API key"),
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger ETL pipeline to fetch game data from external APIs.
    Requires authentication.
    """
    result = await run_etl_pipeline(search=search, rawg_api_key=rawg_api_key)
    return result


