from typing import Optional
from fastapi import APIRouter, status, Query
from app.logic.etl import run_etl_pipeline
from app.logic.games import select_all_games_from_dict
from app.db import games_db

router = APIRouter(prefix="/games", tags=["Games"])


@router.get("/", status_code=status.HTTP_200_OK)
async def get_all_games():
    """
    Get all games from the in-memory database.
    """
    games = select_all_games_from_dict(games_db)
    return games


@router.post("/etl", status_code=status.HTTP_200_OK)
async def trigger_etl(
    search: Optional[str] = Query(None, description="Search term to filter games"),
):
    """
    Trigger ETL pipeline to fetch game data from external APIs.
    DEV mode: Authentication temporarily disabled for testing.
    """
    result = await run_etl_pipeline(search=search)
    return result


