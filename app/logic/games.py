from typing import Optional


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
