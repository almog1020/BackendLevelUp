from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from app.logic.etl import run_etl_pipeline
from app.logic.users import get_current_user

router = APIRouter(prefix="/games", tags=["Games"])


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


